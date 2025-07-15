import os

import bpy
from bpy.types import (
    Operator,
)
from mathutils import Matrix, Vector

from . import hansens_float_packer, json_helpers

def create_mode_mix_nodes(
    node_tree,
    mode_value_output,
    base_color_input,
    effect_mask_socket,
    hardness_output,
    location,
):

    def new_math(op, val=None, x_offset=0, y_offset=0):
        node = node_tree.nodes.new("ShaderNodeMath")
        node.operation = op
        if val is not None:
            node.inputs[1].default_value = val
        node.location = location + Vector((x_offset, y_offset))
        return node

    def new_mix(blend_type, fac=1.0, x_offset=0, y_offset=0):
        node = node_tree.nodes.new("ShaderNodeMixRGB")
        node.blend_type = blend_type
        if fac is not None:
            node.inputs[0].default_value = fac
        node.location = location + Vector((x_offset, y_offset))
        return node

    # --- 1. Calculate all 5 blend modes, blended by hardness ---
    blend_modes = ["LIGHTEN", "SUBTRACT", "MULTIPLY", "DARKEN", "ADD"]
    blend_nodes = []
    y_pos = 200
    for i, mode_name in enumerate(blend_modes):
        # Don't set a default fac, as it will be linked from hardness
        mix_node = new_mix(mode_name, fac=None, x_offset=0, y_offset=y_pos)
        node_tree.links.new(hardness_output, mix_node.inputs[0])
        node_tree.links.new(base_color_input, mix_node.inputs[1])
        node_tree.links.new(effect_mask_socket, mix_node.inputs[2])
        blend_nodes.append(mix_node)
        y_pos -= 120

    # --- 2. Create selection logic based on mode input ---
    # Round and clamp the mode value to be safe
    mode_rounded = new_math("ROUND", x_offset=200, y_offset=100)
    node_tree.links.new(mode_value_output, mode_rounded.inputs[0])

    # Clamp the mode value between 0 and 4 using MIN and MAX, since Math node has no CLAMP
    mode_max = new_math("MAXIMUM", 0.0, x_offset=350, y_offset=100)
    node_tree.links.new(mode_rounded.outputs[0], mode_max.inputs[0])

    mode_clamped = new_math("MINIMUM", 4.0, x_offset=500, y_offset=100)
    node_tree.links.new(mode_max.outputs[0], mode_clamped.inputs[0])

    compare_nodes = []
    y_pos = 200
    x_pos = 650
    for i in range(5):
        compare = new_math("COMPARE", float(i), x_pos, y_pos)
        compare.inputs[2].default_value = 0.01  # Epsilon for float comparison
        node_tree.links.new(mode_clamped.outputs[0], compare.inputs[0])
        compare_nodes.append(compare)
        y_pos -= 120

    # --- 3. Isolate the result of the selected blend mode ---
    selected_results = []
    y_pos = 200
    x_pos = 850
    for i, blend_node in enumerate(blend_nodes):
        select_mix = new_mix("MIX", x_offset=x_pos, y_offset=y_pos)
        select_mix.inputs[1].default_value = (0, 0, 0, 1)  # Color1 = Black
        node_tree.links.new(blend_node.outputs[0], select_mix.inputs[2])
        node_tree.links.new(compare_nodes[i].outputs[0], select_mix.inputs[0])
        selected_results.append(select_mix)
        y_pos -= 120

    # --- 4. Add the isolated results together ---
    # Since only one result is non-black, adding them is equivalent to choosing one.
    # We use Math nodes instead of MixRGB(Add) to avoid color-related clamping issues.
    add_node_x = 1050
    last_output = selected_results[0].outputs[0]
    
    # Chain Math(Add) nodes to sum the 5 results
    add_1 = new_math("ADD", x_offset=add_node_x, y_offset=140)
    node_tree.links.new(last_output, add_1.inputs[0])
    node_tree.links.new(selected_results[1].outputs[0], add_1.inputs[1])

    add_2 = new_math("ADD", x_offset=add_node_x + 200, y_offset=80)
    node_tree.links.new(add_1.outputs[0], add_2.inputs[0])
    node_tree.links.new(selected_results[2].outputs[0], add_2.inputs[1])

    add_3 = new_math("ADD", x_offset=add_node_x + 400, y_offset=20)
    node_tree.links.new(add_2.outputs[0], add_3.inputs[0])
    node_tree.links.new(selected_results[3].outputs[0], add_3.inputs[1])

    selected_blend_result = new_math("ADD", x_offset=add_node_x + 600, y_offset=-40)
    node_tree.links.new(add_3.outputs[0], selected_blend_result.inputs[0])
    node_tree.links.new(selected_results[4].outputs[0], selected_blend_result.inputs[1])

    # The selected result, which was already blended by hardness, is the final output.
    # The final mixing stage is no longer needed.
    return selected_blend_result.outputs[0]

def unpack_nodes(attribute_node, effect_node, node_tree, effect_empty):
    def new_math(op, val=None):
        node = node_tree.nodes.new("ShaderNodeMath")
        node.operation = op
        if val is not None:
            node.inputs[1].default_value = val
        return node

    def apply_sign(value_node, sign_node):
        # Convert 0/1 to -1/+1: signed = value * (sign * 2 - 1)
        mul2 = new_math("MULTIPLY", 2.0)
        node_tree.links.new(sign_node.outputs[0], mul2.inputs[0])

        sub1 = new_math("SUBTRACT", 1.0)
        node_tree.links.new(mul2.outputs[0], sub1.inputs[0])

        signed_value = new_math("MULTIPLY")
        node_tree.links.new(value_node.outputs[0], signed_value.inputs[0])
        node_tree.links.new(sub1.outputs[0], signed_value.inputs[1])
        return signed_value

    separate = node_tree.nodes.new("ShaderNodeSeparateXYZ")
    node_tree.links.new(attribute_node.outputs[0], separate.inputs[0])
    red, green, blue = separate.outputs[0], separate.outputs[1], separate.outputs[2]

    """
    Effect node inputs, in order:
    emptyVector
    Elongation
    Sharpness
    Rotation
    Bend
    Bulge
    Mask
    Clamp
    """
    # Empty vector: add a Texture Coordinate node, and use the Object output
    # Set the Object in the Texture Coordinate to effect_empty
    tex_coord = node_tree.nodes.new("ShaderNodeTexCoord")
    tex_coord.object = effect_empty
    node_tree.links.new(tex_coord.outputs[3], effect_node.inputs[0])

    # RED CHANNEL: EEETSSS
    # Extract elongation
    elongation_div = new_math("DIVIDE", 10000.0)
    node_tree.links.new(red, elongation_div.inputs[0])
    elongation_raw = new_math("FLOOR")
    node_tree.links.new(elongation_div.outputs[0], elongation_raw.inputs[0])
    elongation_value = new_math("DIVIDE", 1000.0)
    node_tree.links.new(elongation_raw.outputs[0], elongation_value.inputs[0])
    node_tree.links.new(elongation_value.outputs[0], effect_node.inputs[1])

    # Extract rotation tens digit
    rot_tens_div = new_math("DIVIDE", 1000.0)
    node_tree.links.new(red, rot_tens_div.inputs[0])
    rot_tens_mod = new_math("MODULO", 10.0)
    node_tree.links.new(rot_tens_div.outputs[0], rot_tens_mod.inputs[0])
    rot_tens_raw = new_math("FLOOR")
    node_tree.links.new(rot_tens_mod.outputs[0], rot_tens_raw.inputs[0])

    # Extract sharpness
    sharpness_mod = new_math("MODULO", 1000.0)
    node_tree.links.new(red, sharpness_mod.inputs[0])
    sharpness_value = new_math("DIVIDE", 940.0)
    node_tree.links.new(sharpness_mod.outputs[0], sharpness_value.inputs[0])
    node_tree.links.new(sharpness_value.outputs[0], effect_node.inputs[2])

    # GREEN CHANNEL: bend (3 value + 1 sign) + hardness (3 value)
    # Packing format: BBBSHHH

    # --- Extract Bend (first 4 digits) ---
    bend_div = new_math("DIVIDE", 10000.0)
    node_tree.links.new(green, bend_div.inputs[0])
    bend_raw = new_math("FLOOR")
    node_tree.links.new(bend_div.outputs[0], bend_raw.inputs[0])
    bend_value = new_math("DIVIDE", 1000.0)
    node_tree.links.new(bend_raw.outputs[0], bend_value.inputs[0])

    green_mod_10000 = new_math("MODULO", 10000.0)
    node_tree.links.new(green, green_mod_10000.inputs[0])
    bend_sign_div = new_math("DIVIDE", 1000.0)
    node_tree.links.new(green_mod_10000.outputs[0], bend_sign_div.inputs[0])
    bend_sign_raw = new_math("FLOOR")
    node_tree.links.new(bend_sign_div.outputs[0], bend_sign_raw.inputs[0])

    bend_signed = apply_sign(bend_value, bend_sign_raw)
    node_tree.links.new(bend_signed.outputs[0], effect_node.inputs[4])  # Connect to Bend input

    # --- Extract Hardness (last 3 digits) ---
    hardness_raw = new_math("MODULO", 1000.0)
    node_tree.links.new(green, hardness_raw.inputs[0])
    hardness_value = new_math("DIVIDE", 1000.0)
    node_tree.links.new(hardness_raw.outputs[0], hardness_value.inputs[0])

    # BLUE CHANNEL: bulge (3 val + 1 sign) + mode (1) + clamp (1) + rotation ones (1)
    # Packing format: UUU S M C R_
    # Extract bulge value (first 4 digits)
    bulge_div = new_math("DIVIDE", 10000.0)
    node_tree.links.new(blue, bulge_div.inputs[0])
    bulge_raw = new_math("FLOOR")
    node_tree.links.new(bulge_div.outputs[0], bulge_raw.inputs[0])
    bulge_value = new_math("DIVIDE", 1000.0)
    node_tree.links.new(bulge_raw.outputs[0], bulge_value.inputs[0])

    # Extract bulge sign (5th digit)
    blue_mod_10000 = new_math("MODULO", 10000.0)
    node_tree.links.new(blue, blue_mod_10000.inputs[0])
    bulge_sign_div = new_math("DIVIDE", 1000.0)
    node_tree.links.new(blue_mod_10000.outputs[0], bulge_sign_div.inputs[0])
    bulge_sign_raw = new_math("FLOOR")
    node_tree.links.new(bulge_sign_div.outputs[0], bulge_sign_raw.inputs[0])

    # Apply sign to bulge
    bulge_signed = apply_sign(bulge_value, bulge_sign_raw)
    node_tree.links.new(bulge_signed.outputs[0], effect_node.inputs[5])

    # Extract mode (from the 100s place)
    blue_mod_1000 = new_math("MODULO", 1000.0)
    node_tree.links.new(blue, blue_mod_1000.inputs[0])
    mode_div = new_math("DIVIDE", 100.0)
    node_tree.links.new(blue_mod_1000.outputs[0], mode_div.inputs[0])
    mode_raw = new_math("FLOOR")
    node_tree.links.new(mode_div.outputs[0], mode_raw.inputs[0])

    # Extract clamp (from the 10s place)
    blue_mod_100 = new_math("MODULO", 100.0)
    node_tree.links.new(blue, blue_mod_100.inputs[0])
    clamp_div = new_math("DIVIDE", 10.0)
    node_tree.links.new(blue_mod_100.outputs[0], clamp_div.inputs[0])
    clamp_raw = new_math("FLOOR")
    node_tree.links.new(clamp_div.outputs[0], clamp_raw.inputs[0])
    node_tree.links.new(clamp_raw.outputs[0], effect_node.inputs[7])

    # Extract rotation ones digit and combine with tens digit
    rot_ones_raw = new_math("MODULO", 10.0)
    node_tree.links.new(blue, rot_ones_raw.inputs[0])

    # Combine tens and ones digits for rotation
    # (rot_tens * 10) + rot_ones
    rot_tens_scaled = new_math("MULTIPLY", 10.0)
    node_tree.links.new(rot_tens_raw.outputs[0], rot_tens_scaled.inputs[0])

    full_rotation = new_math("ADD")
    node_tree.links.new(rot_tens_scaled.outputs[0], full_rotation.inputs[0])
    node_tree.links.new(rot_ones_raw.outputs[0], full_rotation.inputs[1])

    rotation_value = new_math("DIVIDE", 10.0)  # Scale to 0.0-9.9
    node_tree.links.new(full_rotation.outputs[0], rotation_value.inputs[0])
    node_tree.links.new(rotation_value.outputs[0], effect_node.inputs[3])

    return (mode_raw, hardness_value)

# Congratulations, you read through this whole thing! By the time
# you're reading this, hopefully it's obselete and they've
# fixed the arbitrary limit on the number of attribute nodes
# you can use in a material in Blender.
#
#
#
# haha
# ---------------------------------------------------------------------------- #
#             ,;:;;,
#            ;;;;;
#    .=',    ;:;;:,
#   /_', "=. ';:;:;
#   @=:__,  \,;:;:'
#     _(\.=  ;:;;'
#    `"_(  _/="`
#     `"'``
# One of my coworkers learned what a modulo operator
# was because of this project, so at least SOMETHING
# came from all this

