#   If you use this in your work, please refer to it as Hansen's float-packing algorithm.
#   Licensed as Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
#   https://creativecommons.org/licenses/by-sa/4.0/

import math


def clamp(minimum, x, maximum):
    return max(minimum, min(x, maximum))


def packing_algorithm(
    x_loc, y_loc, z_loc, x_scale, elongation, sharpness, hardness, bulge, bend, rotation
):
    """
    This packing algorithm combines 10 distinct attributes
    into a single RGBA value, so that Blender can use this
    information in a single Attribute node.

    Blender can only handle 8 attribute nodes per material,
    which is not enough for a shading rig. This algorithm
    allows for 8 shading edits per shading rig per material,
    which should be enough.

    Format specifications:
    - XYZ locations are magnitude n.nn, stored as 3 digits (nnn)
    - X scale is magnitude n.nn, stored as 3 digits (nnn)
    - Rotation is stored as nn.n (1 decimal)
    - Other values are stored with 2 decimal places as 2 digits

    Cheat sheet:
        R: XXXYYYS
        G: AAEEss#
        B: ZZZSSBB
        A: bbRRR##

    This is designed to be used in a shading rig. In this case,
    you shouldn't be moving the edits/the underlying rig around
    more than a few units, so 3 digits of location precision is
    more than enough. (Use non-world space, obviously.)

    There is a small hardness of data loss due to the packing process.
    In testing, data loss averages between 0.36% and 3.69%.

    Since x_scale controls the size of the shading edit, as does Hardness,
    the actual precision of size_adjustments is at worst 99.87%.
    """

    # Red Channel: X, Y location (3 digits each) + scale's third digit (1 digit)
    # Format: XXXYYYS
    x_loc_abs = min(abs(math.floor(abs(x_loc) * 100.0)), 999)
    y_loc_abs = min(abs(math.floor(abs(y_loc) * 100.0)), 999)
    scale = min(abs(math.floor(abs(x_scale) * 100.0)), 999)
    scale_third_digit_only = scale % 10

    red = x_loc_abs * 10000 + y_loc_abs * 10 + scale_third_digit_only

    # Green Channel: hardness (2 digits) + elongation (2 digits) + sharpness (2 digits) + signs (1 digit)
    # Format: AAEEss# where # encodes z_loc_sign and bend_sign
    hardness_val = min(abs(math.floor(hardness * 100.0)), 99)
    elongation_val = min(abs(math.floor(abs(elongation) * 100.0)), 99)
    sharpness_val = min(abs(math.floor(abs(sharpness) * 100.0)), 99)

    # Sign encoding for z_loc and bend
    z_loc_sign = 0 if z_loc < 0 else 1
    bend_sign = 0 if bend < 0 else 1
    sign_digit = 3 + z_loc_sign + bend_sign * 2

    green = (
        hardness_val * 100000 + elongation_val * 1000 + sharpness_val * 10 + sign_digit
    )

    # Blue Channel: Z location (3 digits) + X scale (first 2 digits) + bulge (2 digits)
    # Format: ZZZSSBB
    z_loc_abs = min(abs(math.floor(abs(z_loc) * 100.0)), 999)
    scale_first_and_second_digit = scale // 10
    bulge_val = min(abs(math.floor(abs(bulge) * 100.0)), 99)

    blue = z_loc_abs * 10000 + scale_first_and_second_digit * 100 + bulge_val

    # Alpha Channel: bend (2 digits) + rotation (3 digits) + location signs (2 digits)
    # Format: bbRRR##

    rotation = rotation * 180.0 / math.pi / 100.0
    # The rotation comes in from Blender as radians, so we convert it to degrees.
    # If you are using this in a different context, you may not need to convert;
    # however, the algorithm expects degrees so make sure this is the case.

    bend_val = min(abs(math.floor(abs(bend) * 100.0)), 99)
    rotation_val = min(abs(math.floor(abs(rotation) * 100.0)), 999)

    # Sign encoding for the last 2 digits
    x_loc_sign = 0 if x_loc < 0 else 1
    y_loc_sign = 0 if y_loc < 0 else 1
    elongation_sign = 0 if elongation < 0 else 1
    bulge_sign = 0 if bulge < 0 else 1

    # Combine signs into 2 digits
    signs_combined = x_loc_sign + y_loc_sign * 2 + elongation_sign * 4 + bulge_sign * 8
    signs_combined = min(signs_combined, 99)

    alpha = bend_val * 100000 + rotation_val * 100 + signs_combined

    return (red, green, blue, alpha)


def unpack_nodes(attribute_node, edit_node, hardness_dest, node_tree):
    def new_math(op, val=None):
        node = node_tree.nodes.new("ShaderNodeMath")
        node.operation = op
        if val is not None:
            node.inputs[1].default_value = val
        return node

    def apply_sign(value_node, sign_node):
        # Convert 0/1 to -1/+1: signed = value * (sign * 2 - 1)
        mul2 = new_math("MULTIPLY")
        mul2.inputs[1].default_value = 2.0
        node_tree.links.new(sign_node.outputs[0], mul2.inputs[0])

        sub1 = new_math("SUBTRACT")
        sub1.inputs[1].default_value = 1.0
        node_tree.links.new(mul2.outputs[0], sub1.inputs[0])

        signed_value = new_math("MULTIPLY")
        node_tree.links.new(value_node.outputs[0], signed_value.inputs[0])
        node_tree.links.new(sub1.outputs[0], signed_value.inputs[1])
        return signed_value

    separate = node_tree.nodes.new("ShaderNodeSeparateXYZ")
    node_tree.links.new(attribute_node.outputs[0], separate.inputs[0])
    red, green, blue = separate.outputs[0], separate.outputs[1], separate.outputs[2]
    alpha = attribute_node.outputs[3]

    # ------------------ RED CHANNEL: XXXYYYS ------------------
    scale_third = new_math("MODULO", 10.0)
    node_tree.links.new(red, scale_third.inputs[0])

    red_div10 = new_math("DIVIDE", 10.0)
    node_tree.links.new(red, red_div10.inputs[0])
    red_floor = new_math("FLOOR")
    node_tree.links.new(red_div10.outputs[0], red_floor.inputs[0])

    y_loc_abs = new_math("MODULO", 1000.0)
    node_tree.links.new(red_floor.outputs[0], y_loc_abs.inputs[0])

    x_loc_div = new_math("DIVIDE", 1000.0)
    node_tree.links.new(red_floor.outputs[0], x_loc_div.inputs[0])
    x_loc_abs = new_math("FLOOR")
    node_tree.links.new(x_loc_div.outputs[0], x_loc_abs.inputs[0])

    # ------------------ GREEN CHANNEL: AAEEss# ------------------
    sign_digit = new_math("MODULO", 10.0)
    node_tree.links.new(green, sign_digit.inputs[0])

    green_div10 = new_math("DIVIDE", 10.0)
    node_tree.links.new(green, green_div10.inputs[0])
    green_floor10 = new_math("FLOOR")
    node_tree.links.new(green_div10.outputs[0], green_floor10.inputs[0])

    sharpness_val = new_math("MODULO", 100.0)
    node_tree.links.new(green_floor10.outputs[0], sharpness_val.inputs[0])

    green_div100 = new_math("DIVIDE", 100.0)
    node_tree.links.new(green_floor10.outputs[0], green_div100.inputs[0])
    green_floor100 = new_math("FLOOR")
    node_tree.links.new(green_div100.outputs[0], green_floor100.inputs[0])

    elongation_val = new_math("MODULO", 100.0)
    node_tree.links.new(green_floor100.outputs[0], elongation_val.inputs[0])

    hardness_div = new_math("DIVIDE", 100.0)
    node_tree.links.new(green_floor100.outputs[0], hardness_div.inputs[0])
    hardness_floor = new_math("FLOOR")
    node_tree.links.new(hardness_div.outputs[0], hardness_floor.inputs[0])

    # Decode z_loc_sign and bend_sign from sign_digit
    sign_offset = new_math("SUBTRACT", 3.0)
    node_tree.links.new(sign_digit.outputs[0], sign_offset.inputs[0])

    z_loc_sign = new_math("MODULO", 2.0)
    node_tree.links.new(sign_offset.outputs[0], z_loc_sign.inputs[0])

    bend_sign_div = new_math("DIVIDE", 2.0)
    node_tree.links.new(sign_offset.outputs[0], bend_sign_div.inputs[0])
    bend_sign = new_math("FLOOR")
    node_tree.links.new(bend_sign_div.outputs[0], bend_sign.inputs[0])

    # ------------------ BLUE CHANNEL: ZZZSSBB ------------------
    bulge_val = new_math("MODULO", 100.0)
    node_tree.links.new(blue, bulge_val.inputs[0])

    blue_div = new_math("DIVIDE", 100.0)
    node_tree.links.new(blue, blue_div.inputs[0])
    blue_floor = new_math("FLOOR")
    node_tree.links.new(blue_div.outputs[0], blue_floor.inputs[0])

    scale_first_two = new_math("MODULO", 100.0)
    node_tree.links.new(blue_floor.outputs[0], scale_first_two.inputs[0])

    z_loc_div = new_math("DIVIDE", 100.0)
    node_tree.links.new(blue_floor.outputs[0], z_loc_div.inputs[0])
    z_loc_abs = new_math("FLOOR")
    node_tree.links.new(z_loc_div.outputs[0], z_loc_abs.inputs[0])

    scale_first_two_x10 = new_math("MULTIPLY", 10.0)
    node_tree.links.new(scale_first_two.outputs[0], scale_first_two_x10.inputs[0])

    scale_full = new_math("ADD")
    node_tree.links.new(scale_first_two_x10.outputs[0], scale_full.inputs[0])
    node_tree.links.new(scale_third.outputs[0], scale_full.inputs[1])

    x_scale = new_math("DIVIDE", 100.0)
    node_tree.links.new(scale_full.outputs[0], x_scale.inputs[0])

    # ------------------ CORRECTED ALPHA CHANNEL: bbRRR## ------------------
    # Extract signs (2 digits), rotation (3 digits), bend (2 digits)
    signs_combined = new_math("MODULO", 100.0)
    node_tree.links.new(alpha, signs_combined.inputs[0])

    alpha_div100 = new_math("DIVIDE", 100.0)
    node_tree.links.new(alpha, alpha_div100.inputs[0])
    alpha_floor100 = new_math("FLOOR")
    node_tree.links.new(alpha_div100.outputs[0], alpha_floor100.inputs[0])

    rotation_val = new_math("MODULO", 1000.0)
    node_tree.links.new(alpha_floor100.outputs[0], rotation_val.inputs[0])

    rotation_divide_by_ten = new_math("DIVIDE", 1000.0)
    node_tree.links.new(rotation_val.outputs[0], rotation_divide_by_ten.inputs[0])
    rotation_val = rotation_divide_by_ten

    rotation_to_degrees = new_math("MULTIPLY", (180.0 / math.pi))
    node_tree.links.new(rotation_val.outputs[0], rotation_to_degrees.inputs[0])
    rotation_val = rotation_to_degrees

    bend_div1000 = new_math("DIVIDE", 1000.0)
    node_tree.links.new(alpha_floor100.outputs[0], bend_div1000.inputs[0])
    bend_val = new_math("FLOOR")
    node_tree.links.new(bend_div1000.outputs[0], bend_val.inputs[0])

    # Decode combined signs
    x_loc_sign = new_math("MODULO", 2.0)
    node_tree.links.new(signs_combined.outputs[0], x_loc_sign.inputs[0])

    y_loc_sign_div = new_math("DIVIDE", 2.0)
    node_tree.links.new(signs_combined.outputs[0], y_loc_sign_div.inputs[0])
    y_loc_sign_floor = new_math("FLOOR")
    node_tree.links.new(y_loc_sign_div.outputs[0], y_loc_sign_floor.inputs[0])
    y_loc_sign = new_math("MODULO", 2.0)
    node_tree.links.new(y_loc_sign_floor.outputs[0], y_loc_sign.inputs[0])

    elong_sign_div = new_math("DIVIDE", 4.0)
    elong_sign_floor = new_math("FLOOR")
    node_tree.links.new(signs_combined.outputs[0], elong_sign_div.inputs[0])
    node_tree.links.new(elong_sign_div.outputs[0], elong_sign_floor.inputs[0])
    elong_sign = new_math("MODULO", 2.0)
    node_tree.links.new(elong_sign_floor.outputs[0], elong_sign.inputs[0])

    bulge_sign_div = new_math("DIVIDE", 8.0)
    bulge_sign_floor = new_math("FLOOR")
    node_tree.links.new(signs_combined.outputs[0], bulge_sign_div.inputs[0])
    node_tree.links.new(bulge_sign_div.outputs[0], bulge_sign_floor.inputs[0])
    bulge_sign = new_math("MODULO", 2.0)
    node_tree.links.new(bulge_sign_floor.outputs[0], bulge_sign.inputs[0])

    sharpness_is_positive = new_math("GREATER_THAN", 0.0)
    node_tree.links.new(sharpness_val.outputs[0], sharpness_is_positive.inputs[0])

    x_loc_div100 = new_math("DIVIDE", 100.0)
    node_tree.links.new(x_loc_abs.outputs[0], x_loc_div100.inputs[0])
    x_loc = apply_sign(x_loc_div100, x_loc_sign)

    y_loc_div100 = new_math("DIVIDE", 100.0)
    node_tree.links.new(y_loc_abs.outputs[0], y_loc_div100.inputs[0])
    y_loc = apply_sign(y_loc_div100, y_loc_sign)

    z_loc_div100 = new_math("DIVIDE", 100.0)
    node_tree.links.new(z_loc_abs.outputs[0], z_loc_div100.inputs[0])
    z_loc = apply_sign(z_loc_div100, z_loc_sign)

    elong_div = new_math("DIVIDE", 100.0)
    node_tree.links.new(elongation_val.outputs[0], elong_div.inputs[0])
    elongation = apply_sign(elong_div, elong_sign)

    bend_div = new_math("DIVIDE", 100.0)
    node_tree.links.new(bend_val.outputs[0], bend_div.inputs[0])
    bend = apply_sign(bend_div, bend_sign)

    bulge_div = new_math("DIVIDE", 100.0)
    node_tree.links.new(bulge_val.outputs[0], bulge_div.inputs[0])
    bulge = apply_sign(bulge_div, bulge_sign)

    sharpness_div = new_math("DIVIDE", 100.0)
    node_tree.links.new(sharpness_val.outputs[0], sharpness_div.inputs[0])

    # Convert boolean to sign: if positive, use 1, else use -1
    sharpness_sign_mul2 = new_math("MULTIPLY", 2.0)
    node_tree.links.new(sharpness_is_positive.outputs[0], sharpness_sign_mul2.inputs[0])

    sharpness_sign_sub1 = new_math("SUBTRACT", 1.0)
    node_tree.links.new(sharpness_sign_mul2.outputs[0], sharpness_sign_sub1.inputs[0])

    sharpness = new_math("MULTIPLY")
    node_tree.links.new(sharpness_div.outputs[0], sharpness.inputs[0])
    node_tree.links.new(sharpness_sign_sub1.outputs[0], sharpness.inputs[1])

    hardness = new_math("DIVIDE", 100.0)
    node_tree.links.new(hardness_floor.outputs[0], hardness.inputs[0])

    # Connect to edit_node inputs
    node_tree.links.new(x_loc.outputs[0], edit_node.inputs[0])
    node_tree.links.new(y_loc.outputs[0], edit_node.inputs[1])
    node_tree.links.new(z_loc.outputs[0], edit_node.inputs[2])
    node_tree.links.new(x_scale.outputs[0], edit_node.inputs[3])
    node_tree.links.new(elongation.outputs[0], edit_node.inputs[4])
    node_tree.links.new(sharpness.outputs[0], edit_node.inputs[5])
    node_tree.links.new(bend.outputs[0], edit_node.inputs[6])
    node_tree.links.new(bulge.outputs[0], edit_node.inputs[7])
    node_tree.links.new(rotation_val.outputs[0], edit_node.inputs[8])
    node_tree.links.new(hardness.outputs[0], hardness_dest.inputs[0])


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
