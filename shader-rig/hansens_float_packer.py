#   If you use this in your work, please refer to it as Hansen's float-packing algorithm.
#   Licensed as Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
#   https://creativecommons.org/licenses/by-sa/4.0/

import math


def clamp(minimum, x, maximum):
    return max(minimum, min(x, maximum))


def packing_algorithm(elongation, sharpness, bulge, bend, hardness, mode, clamp_val, rotation):
    """
    This packing algorithm combines 8 distinct attributes
    into a single RGB value, so that Blender can use this
    information in a single Attribute node (with 7 digits
    of precision to spare if more attributes are needed!)

    Blender can only handle 8 attribute nodes per material,
    which is not enough for a shading rig. This algorithm
    allows for 8 shading effects per shading rig per material,
    which should be enough.

    Elong (0 to .999) 3d
    Sharp (0 to .999) 3d
    roTation (0 to 99) 1d (first digit)
    benD (-.999 to .999) 4d
    bUlge (-.999 to 999) 4d
    Hardness (0 to .999) 3d
    Clamp (0 or 1) 1d
    Rotation (0 to 99) 2d
    Mode (0 (Lighten), 1 (Subtract), 2 (Multiply), 3 (Darken), 4 (Add)) 1d

    EEETSSS
    DDD-AAA
    UUU-MCR_
    """

    pairs = {
        "red": ["elongation", "rotation", "sharpness"],
        "green": ["bend", "hardness"],
        "blue": ["bulge", "clamp_val", "mode"],
    }
    vals = {}
    signs = {}

    for color, attributes in pairs.items():
        for attr in attributes:
            if attr in ["elongation", "bend", "bulge"]:
                # all of these are -0.999 to 0.999
                vals[attr] = math.floor(clamp(-0.999, locals()[attr], 0.999) * 1000)
                signs[attr] = 1 if vals[attr] >= 0 else 0
                vals[attr] = abs(vals[attr])
            elif attr in ["sharpness", "hardness"]:
                # these are 0.0 to 0.999
                vals[attr] = math.floor(clamp(0.0, locals()[attr], 0.999) * 1000)
            elif attr == "clamp_val":
                # this is 0 or 1, as a Boolean (t/f)
                vals[attr] = locals()[attr]
                if vals[attr] == True:
                    vals[attr] = 1
                else: 
                    vals[attr] = 0
            elif attr == "mode":
                # this is 0 to 4
                vals[attr] = int(clamp(0, locals()[attr], 4))
            elif attr == "rotation":
                # this is 0 to 99
                vals[attr] = int(clamp(0, locals()[attr], 99))

    # red: elongation (3) + rot_tens (1) + sharpness (3) + elongation_sign (1)
    rot_tens = math.floor(vals["rotation"] / 10)
    red = vals["elongation"] * 1000000 + rot_tens * 100000 + vals["sharpness"] * 10 + signs["elongation"]

    green = vals["bend"] * 10000 + signs["bend"] * 1000 + vals["hardness"]
    # blue: bulge (3) + bulge_sign (1) + mode (1) + clamp (1) + rot_ones (1)
    rot_ones = vals["rotation"] % 10
    blue = (
        vals["bulge"] * 10000
        + signs["bulge"] * 1000
        + vals["mode"] * 100
        + vals["clamp_val"] * 10
        + rot_ones
    )

    return (red, green, blue)


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
    # Extract elongation (first 3 digits)
    elongation_div = new_math("DIVIDE", 1000000.0)
    node_tree.links.new(red, elongation_div.inputs[0])
    elongation_raw = new_math("FLOOR")
    node_tree.links.new(elongation_div.outputs[0], elongation_raw.inputs[0])
    elongation_value = new_math("DIVIDE", 1000.0)
    node_tree.links.new(elongation_raw.outputs[0], elongation_value.inputs[0])

    # Extract rotation tens digit
    rot_tens_div = new_math("DIVIDE", 100000.0)
    node_tree.links.new(red, rot_tens_div.inputs[0])
    rot_tens_mod = new_math("MODULO", 10.0)
    node_tree.links.new(rot_tens_div.outputs[0], rot_tens_mod.inputs[0])
    rot_tens_raw = new_math("FLOOR")
    node_tree.links.new(rot_tens_mod.outputs[0], rot_tens_raw.inputs[0])

    # Extract sharpness
    sharpness_div = new_math("DIVIDE", 10.0)
    node_tree.links.new(red, sharpness_div.inputs[0])
    sharpness_mod = new_math("MODULO", 1000.0)
    node_tree.links.new(sharpness_div.outputs[0], sharpness_mod.inputs[0])
    sharpness_value = new_math("DIVIDE", 1000.0)
    node_tree.links.new(sharpness_mod.outputs[0], sharpness_value.inputs[0])
    node_tree.links.new(sharpness_value.outputs[0], effect_node.inputs[2])

    # Extract elongation sign
    elongation_sign_raw = new_math("MODULO", 10.0)
    node_tree.links.new(red, elongation_sign_raw.inputs[0])
    elongation_sign_raw = new_math("FLOOR")
    node_tree.links.new(elongation_sign_div.outputs[0], elongation_sign_raw.inputs[0])

    # Apply sign to elongation
    elongation_signed = apply_sign(elongation_value, elongation_sign_raw)
    node_tree.links.new(elongation_signed.outputs[0], effect_node.inputs[1])

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

    rot_tens_scaled = new_math("MULTIPLY", 10.0)
    node_tree.links.new(rot_tens_raw.outputs[0], rot_tens_scaled.inputs[0])

    full_rotation = new_math("ADD")
    node_tree.links.new(rot_tens_scaled.outputs[0], full_rotation.inputs[0])
    node_tree.links.new(rot_ones_raw.outputs[0], full_rotation.inputs[1])

    rotation_value = new_math("DIVIDE", 100.0) # Scale to 0.0-0.99
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
