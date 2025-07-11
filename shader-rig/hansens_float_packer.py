#   If you use this in your work, please refer to it as Hansen's float-packing algorithm.
#   Licensed as Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
#   https://creativecommons.org/licenses/by-sa/4.0/

import math


def clamp(minimum, x, maximum):
    return max(minimum, min(x, maximum))


def packing_algorithm(elongation, sharpness, bulge, bend, hardness, mask, mode):
    """
    This packing algorithm combines 7 distinct attributes
    into a single RGB value, so that Blender can use this
    information in a single Attribute node (with 7 digits
    of precision to spare if more attributes are needed!)

    Blender can only handle 8 attribute nodes per material,
    which is not enough for a shading rig. This algorithm
    allows for 8 shading edits per shading rig per material,
    which should be enough.

    Elong (-.999 to .999) 4d
    Sharp (0 to .999) 3d
    benD (-.999 to .999) 4d
    bUlge (-.999 to 999) 4d
    Hardness (0 to .999) 3d
    masK (0 to .99) 2d
    Mode (0 (Lighten), 1 (Subtract), 2 (Multiply), 3 (Darken), 4 (Add)) 1d

    EEE-SSS
    DDD-AAA
    UUU-MKK
    """

    pairs = {
        "red": ["elongation", "sharpness"],
        "green": ["bend", "hardness"],
        "blue": ["bulge", "mask", "mode"],
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
            elif attr == "mask":
                # this is 0.0 to 0.99
                vals[attr] = math.floor(clamp(0.0, locals()[attr], 0.99) * 100)
            elif attr == "mode":
                # this is 0 to 4
                vals[attr] = clamp(0, locals()[attr], 4)

    red = vals["elongation"] * 10000 + signs["elongation"] * 1000 + vals["sharpness"]

    green = vals["bend"] * 10000 + signs["bend"] * 1000 + vals["hardness"]
    blue = (
        vals["bulge"] * 10000
        + signs["bulge"] * 1000
        + vals["mode"] * 100
        + vals["mask"]
    )

    return (red, green, blue)


def unpack_nodes(attribute_node, edit_node, node_tree, effect_empty):
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
    Edit node inputs, in order:
    emptyVector
    Elongation
    Sharpness
    Rotation
    Bend
    Bulge
    Mask
    """
    # Empty vector: add a Texture Coordinate node, and use the Object output
    # Set the Object in the Texture Coordinate to effect_empty
    tex_coord = node_tree.nodes.new("ShaderNodeTexCoord")
    tex_coord.object = effect_empty
    node_tree.links.new(tex_coord.outputs[3], edit_node.inputs[0])

    # RED CHANNEL: elongation (4 digits) + sign (1 digit) + sharpness (3 digits)
    # Extract elongation value (first 4 digits)
    elongation_div = new_math("DIVIDE", 10000.0)
    node_tree.links.new(red, elongation_div.inputs[0])
    elongation_raw = new_math("FLOOR")
    node_tree.links.new(elongation_div.outputs[0], elongation_raw.inputs[0])
    elongation_value = new_math("DIVIDE", 1000.0)
    node_tree.links.new(elongation_raw.outputs[0], elongation_value.inputs[0])

    # Extract elongation sign (5th digit)
    red_mod_10000 = new_math("MODULO", 10000.0)
    node_tree.links.new(red, red_mod_10000.inputs[0])
    elongation_sign_div = new_math("DIVIDE", 1000.0)
    node_tree.links.new(red_mod_10000.outputs[0], elongation_sign_div.inputs[0])
    elongation_sign_raw = new_math("FLOOR")
    node_tree.links.new(elongation_sign_div.outputs[0], elongation_sign_raw.inputs[0])

    # Apply sign to elongation
    elongation_signed = apply_sign(elongation_value, elongation_sign_raw)
    node_tree.links.new(elongation_signed.outputs[0], edit_node.inputs[1])

    # Extract sharpness (last 3 digits)
    sharpness_raw = new_math("MODULO", 1000.0)
    node_tree.links.new(red, sharpness_raw.inputs[0])
    sharpness_value = new_math("DIVIDE", 1000.0)
    node_tree.links.new(sharpness_raw.outputs[0], sharpness_value.inputs[0])
    node_tree.links.new(sharpness_value.outputs[0], edit_node.inputs[2])

    # GREEN CHANNEL: bend (4 digits) + sign (1 digit) + hardness (3 digits)
    # Extract bend value (first 4 digits)
    bend_div = new_math("DIVIDE", 10000.0)
    node_tree.links.new(green, bend_div.inputs[0])
    bend_raw = new_math("FLOOR")
    node_tree.links.new(bend_div.outputs[0], bend_raw.inputs[0])
    bend_value = new_math("DIVIDE", 1000.0)
    node_tree.links.new(bend_raw.outputs[0], bend_value.inputs[0])

    # Extract bend sign (5th digit)
    green_mod_10000 = new_math("MODULO", 10000.0)
    node_tree.links.new(green, green_mod_10000.inputs[0])
    bend_sign_div = new_math("DIVIDE", 1000.0)
    node_tree.links.new(green_mod_10000.outputs[0], bend_sign_div.inputs[0])
    bend_sign_raw = new_math("FLOOR")
    node_tree.links.new(bend_sign_div.outputs[0], bend_sign_raw.inputs[0])

    # Apply sign to bend
    bend_signed = apply_sign(bend_value, bend_sign_raw)
    node_tree.links.new(bend_signed.outputs[0], edit_node.inputs[4])

    # Extract hardness (last 3 digits)
    hardness_raw = new_math("MODULO", 1000.0)
    node_tree.links.new(green, hardness_raw.inputs[0])
    hardness_value = new_math("DIVIDE", 1000.0)
    node_tree.links.new(hardness_raw.outputs[0], hardness_value.inputs[0])
    node_tree.links.new(hardness_value.outputs[0], edit_node.inputs[3])

    # BLUE CHANNEL: bulge (4 digits) + sign (1 digit) + mode (2 digits) + mask (2 digits)
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
    node_tree.links.new(bulge_signed.outputs[0], edit_node.inputs[5])

    # Extract mode (next 2 digits)
    blue_mod_1000 = new_math("MODULO", 1000.0)
    node_tree.links.new(blue, blue_mod_1000.inputs[0])
    mode_div = new_math("DIVIDE", 100.0)
    node_tree.links.new(blue_mod_1000.outputs[0], mode_div.inputs[0])
    mode_raw = new_math("FLOOR")
    node_tree.links.new(mode_div.outputs[0], mode_raw.inputs[0])

    # Extract mask (last 2 digits)
    mask_raw = new_math("MODULO", 100.0)
    node_tree.links.new(blue, mask_raw.inputs[0])
    mask_value = new_math("DIVIDE", 100.0)
    node_tree.links.new(mask_raw.outputs[0], mask_value.inputs[0])
    # Make mask negative
    mask_sign = new_math("MULTIPLY", -1.0)
    node_tree.links.new(mask_value.outputs[0], mask_sign.inputs[0])
    node_tree.links.new(mask_sign.outputs[0], edit_node.inputs[6])

    return (mode_raw, mask_value, hardness_value)


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
