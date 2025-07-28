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
    UUU-MCR
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
            if attr in ["bend", "bulge"]:
                # all of these are -0.999 to 0.999
                vals[attr] = math.floor(clamp(-0.999, locals()[attr], 0.999) * 1000)
                signs[attr] = 1 if vals[attr] >= 0 else 0
                vals[attr] = abs(vals[attr])
            elif attr in ["sharpness", "hardness"]:
                # these are 0.0 to 0.999
                vals[attr] = math.floor(clamp(0.0, locals()[attr], 0.999) * 1000)
            elif attr == "elongation":
                # this is 0.0 to 0.999
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

    # red: elongation (3) + rot_tens (1) + sharpness (3)
    rot_tens = math.floor(vals["rotation"] / 10)
    red = vals["elongation"] * 10000 + rot_tens * 1000 + vals["sharpness"]

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