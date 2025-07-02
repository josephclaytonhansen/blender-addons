import bpy

from bpy.types import (
    Operator,
)

from . import json_helpers

class SR_OT_RigList_Add(Operator):
    """Add a new edit to the list."""

    bl_idname = "shading_rig.list_add"
    bl_label = "Add Edit"
    bl_description = "Create a new Empty as a new edit"

    def execute(self, context):
        scene = context.scene
        cursor_location = scene.cursor.location
        rig_list = scene.shading_rig_list

        new_item = rig_list.add()

        if scene.shading_rig_default_material:
            new_item.material = scene.shading_rig_default_material

        if scene.shading_rig_default_light:
            new_item.light_object = scene.shading_rig_default_light

        bpy.ops.object.empty_add(type="SPHERE", align="VIEW", location=cursor_location)
        new_empty = context.active_object
        new_empty.empty_display_size = 0.5
        new_empty.show_name = True
        new_empty.show_in_front = True
        bpy.ops.transform.rotate(value=1.5708, orient_axis="X", orient_type="LOCAL")

        new_item.empty_object = new_empty

        new_item.name = f"SR_Edit.{len(rig_list):03d}"

        new_item.last_empty_name = new_item.name

        json_helpers.set_shading_rig_list_index(len(rig_list) - 1)

        # create custom properties on objects with the material
        objects_with_material = []
        for obj in bpy.data.objects:
            if any(s.material == new_item.material for s in obj.material_slots):
                objects_with_material.append(obj)

        print(
            f"Objects with material '{new_item.material.name}': {len(objects_with_material)} found."
        )

        rig_index = len(rig_list) - 1

        for obj in objects_with_material:
            packed_prop_name = f"packed:{new_item.name}"
            obj[packed_prop_name] = [0, 0, 0, 0]

            # Create drivers for each channel (0=red, 1=green, 2=blue, 3=alpha)
            for channel in range(4):
                # Create the driver
                fcurve = obj.driver_add(f'["{packed_prop_name}"]', channel)
                driver = fcurve.driver
                driver.type = "SCRIPTED"

                # Create input variables as Context Properties
                var_names = [
                    "x_loc",
                    "y_loc",
                    "z_loc",
                    "x_scale",
                    "elongation",
                    "sharpness",
                    "amount",
                    "bulge",
                    "bend",
                    "rotation",
                ]

                var_paths_transform_channel = [
                    f"{new_item.name}.location[0]",
                    f"{new_item.name}.location[1]",
                    f"{new_item.name}.location[2]",
                    f"{new_item.name}.scale[0]",
                ]
                var_paths_context_prop = [
                    f"shading_rig_list[{rig_index}].elongation",
                    f"shading_rig_list[{rig_index}].sharpness",
                    f"shading_rig_list[{rig_index}].amount",
                    f"shading_rig_list[{rig_index}].bulge",
                    f"shading_rig_list[{rig_index}].bend",
                    f"shading_rig_list[{rig_index}].rotation",
                ]

                var_paths = var_paths_transform_channel + var_paths_context_prop

                # Create driver variables
                for var_name, var_path in zip(var_names, var_paths):
                    var = driver.variables.new()
                    var.name = var_name
                    if "location" in var_path or "scale" in var_path:
                        # Use Transform Channel for location and scale
                        var.type = "TRANSFORMS"
                        # var.targets[0].id_type = 'OBJECT'
                        var.targets[0].id = new_item.empty_object
                        if "location" in var_path:
                            var.targets[0].transform_type = (
                                "LOC_X"
                                if "x_loc" in var_name
                                else "LOC_Y" if "y_loc" in var_name else "LOC_Z"
                            )
                        elif "scale" in var_path:
                            var.targets[0].transform_type = "SCALE_X"
                    else:
                        # Use Context Property for other variables
                        var.type = "CONTEXT_PROP"
                        var.targets[0].context_property = "ACTIVE_SCENE"
                        var.targets[0].data_path = var_path

                # Set the expression to use the input variables
                driver.expression = (
                    f"packing_algorithm("
                    f"x_loc, y_loc, z_loc, x_scale, elongation, "
                    f"sharpness, amount, bulge, bend, rotation)[{channel}]"
                )

        json_helpers.sync_scene_to_json(context.scene)

        return {"FINISHED"}


class SR_OT_Correspondence_Add(Operator):
    """Add a new correspondence to the active rig."""

    bl_idname = "shading_rig.correspondence_add"
    bl_label = "Add Correspondence"
    bl_description = "Add a new correspondence to the active rig"

    @classmethod
    def poll(cls, context):
        scene = context.scene

        return (
            json_helpers.get_shading_rig_list_index() >= 0
            and len(scene.shading_rig_list) > 0
        )

    def execute(self, context):
        scene = context.scene
        active_rig_item = scene.shading_rig_list[
            json_helpers.get_shading_rig_list_index()
        ]

        if not active_rig_item.light_object:
            self.report({"ERROR"}, "Active edit has no Light Object assigned.")
            return {"CANCELLED"}
        if not active_rig_item.empty_object:
            self.report({"ERROR"}, "Active edit has no Empty Object assigned.")
            return {"CANCELLED"}

        light_obj = active_rig_item.light_object
        empty_obj = active_rig_item.empty_object

        if not light_obj or not empty_obj:
            self.report({"ERROR"}, "Active edit has no Light or Empty Object assigned.")
            return {"CANCELLED"}

        try:
            new_corr = active_rig_item.correspondences.add()
            new_corr.name = f"Correspondence.{len(active_rig_item.correspondences):03d}"

            new_corr.light_rotation = light_obj.rotation_euler
            new_corr.empty_position = empty_obj.location
            new_corr.empty_scale = empty_obj.scale

            active_rig_item.correspondences_index = (
                len(active_rig_item.correspondences) - 1
            )

            self.report({"INFO"}, f"Stored pose in '{new_corr.name}'.")
        except Exception as e:
            self.report({"ERROR"}, "Failed to add correspondence. " + str(e))
            return {"CANCELLED"}
        json_helpers.sync_scene_to_json(context.scene)
        return {"FINISHED"}


class SR_OT_Correspondence_Remove(Operator):
    """Remove the selected correspondence from the active edit."""

    bl_idname = "shading_rig.correspondence_remove"
    bl_label = "Remove Correspondence"
    bl_description = "Remove the selected correspondence from the active edit"

    @classmethod
    def poll(cls, context):
        scene = context.scene

        if not (
            json_helpers.get_shading_rig_list_index() >= 0
            and len(scene.shading_rig_list) > 0
        ):
            return False
        active_rig_item = scene.shading_rig_list[
            json_helpers.get_shading_rig_list_index()
        ]
        return len(active_rig_item.correspondences) > 0

    def execute(self, context):
        scene = context.scene
        active_rig_item = scene.shading_rig_list[
            json_helpers.get_shading_rig_list_index()
        ]
        index = active_rig_item.correspondences_index

        if index >= len(active_rig_item.correspondences):
            return {"CANCELLED"}

        removed_name = active_rig_item.correspondences[index].name
        active_rig_item.correspondences.remove(index)

        if index > 0:
            active_rig_item.correspondences_index = index - 1
        else:
            active_rig_item.correspondences_index = 0

        self.report({"INFO"}, f"Removed correspondence '{removed_name}' from edit.")
        json_helpers.sync_scene_to_json(context.scene)
        return {"FINISHED"}


class SR_OT_RigList_Remove(Operator):
    """Remove the selected rig from the list."""

    bl_idname = "shading_rig.list_remove"
    bl_label = "Remove Edit"
    bl_description = "Remove the selected edit and its associated objects from the scene"

    @classmethod
    def poll(cls, context):
        return len(context.scene.shading_rig_list) > 0

    def execute(self, context):
        scene = context.scene
        rig_list = scene.shading_rig_list
        index = json_helpers.get_shading_rig_list_index()

        if index >= len(rig_list):
            return {"CANCELLED"}

        item_to_remove = rig_list[index]

        # Remove the custom properties
        if item_to_remove.material:
            base_prop_names = [
                "elongation",
                "sharpness",
                "amount",
                "bulge",
                "bend",
                "rotation",
                "edit_location_x",
                "edit_location_y",
                "edit_location_z",
                "edit_scale_x",
                "edit_scale_y",
                "edit_scale_z",
            ]

            for obj in bpy.data.objects:
                if any(
                    s.material == item_to_remove.material for s in obj.material_slots
                ):
                    for base_prop in base_prop_names:
                        prop_name = f"{base_prop}:{item_to_remove.name}"
                        if prop_name in obj:
                            del obj[prop_name]

        if item_to_remove.material and item_to_remove.empty_object:
            material = item_to_remove.material
            empty_name = item_to_remove.empty_object.name
            node_to_remove_name = f"ShadingRigEdit_{empty_name}"

            if material.node_tree:
                node_tree = material.node_tree
                mix_node_to_remove_name = f"MixRGB_{empty_name}"
                mix_node = node_tree.nodes.get(mix_node_to_remove_name)
                if mix_node:
                    input_socket = mix_node.inputs["Color1"]
                    output_socket = mix_node.outputs["Color"]

                    if input_socket.is_linked and output_socket.is_linked:
                        upstream_socket = input_socket.links[0].from_socket
                        downstream_sockets = [
                            link.to_socket for link in output_socket.links
                        ]

                        for downstream_socket in downstream_sockets:
                            node_tree.links.new(upstream_socket, downstream_socket)

                node_to_remove = material.node_tree.nodes.get(node_to_remove_name)
                if node_to_remove:
                    material.node_tree.nodes.remove(node_to_remove)

                if mix_node:
                    material.node_tree.nodes.remove(mix_node)

        objects_to_delete = []
        if item_to_remove.empty_object:
            objects_to_delete.append(item_to_remove.empty_object)

        rig_list.remove(index)

        if index > 0:
            json_helpers.set_shading_rig_list_index(index - 1)
        else:
            json_helpers.set_shading_rig_list_index(0)

        if objects_to_delete:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in objects_to_delete:
                if obj.name in bpy.data.objects:
                    bpy.data.objects[obj.name].select_set(True)
            bpy.ops.object.delete()

        json_helpers.sync_scene_to_json(context.scene)

        return {"FINISHED"}


#   If you use this in your work, please refer to it as Hansen's float-packing algorithm.
#   Licensed as Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
#   https://creativecommons.org/licenses/by-sa/4.0/

import math

def clamp(minimum, x, maximum):
    return max(minimum, min(x, maximum))

# Yes, this is duplicated, but calling in a function into a scripted driver 
# from a separate file apparently only works once, immediately after you install
# the addon (⇀︿⇀) Why? I have no idea.
def packing_algorithm(
    x_loc, y_loc, z_loc, x_scale, elongation, sharpness, amount, bulge, bend, rotation
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
    - Rotation is stored as integer (no decimals)
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

    There is a small amount of data loss due to the packing process.
    In testing, data loss averages between 0.36% and 3.69%.

    Since x_scale controls the size of the shading edit, as does Amount,
    the actual precision of size_adjustments is at worst 99.87%.
    """
    
    rotation = rotation * 180.0 / math.pi
    # The rotation comes in from Blender as radians, so we convert it to degrees.
    # If you are using this in a different context, you may not need to convert;
    # however, the algorithm expects degrees so make sure this is the case.

    # Red Channel: X, Y location (3 digits each) + scale's third digit (1 digit)
    # Format: XXXYYYS
    x_loc_abs = min(abs(math.floor(abs(x_loc) * 100.0)), 999)
    y_loc_abs = min(abs(math.floor(abs(y_loc) * 100.0)), 999)
    scale = min(abs(math.floor(abs(x_scale) * 100.0)), 999)
    scale_third_digit_only = scale % 10

    red = x_loc_abs * 10000 + y_loc_abs * 10 + scale_third_digit_only

    # Green Channel: amount (2 digits) + elongation (2 digits) + sharpness (2 digits) + signs (1 digit)
    # Format: AAEEss# where # encodes z_loc_sign and bend_sign
    amount_val = min(abs(math.floor(amount * 100.0)), 99)
    elongation_val = min(abs(math.floor(abs(elongation) * 100.0)), 99)
    sharpness_val = min(abs(math.floor(abs(sharpness) * 100.0)), 99)

    # Sign encoding for z_loc and bend
    z_loc_sign = 0 if z_loc < 0 else 1
    bend_sign = 0 if bend < 0 else 1
    sign_digit = 3 + z_loc_sign + bend_sign * 2

    green = (
        amount_val * 100000 + elongation_val * 1000 + sharpness_val * 10 + sign_digit
    )

    # Blue Channel: Z location (3 digits) + X scale (first 2 digits) + bulge (2 digits)
    # Format: ZZZSSBB
    z_loc_abs = min(abs(math.floor(abs(z_loc) * 100.0)), 999)
    scale_first_and_second_digit = scale // 10
    bulge_val = min(abs(math.floor(abs(bulge) * 100.0)), 99)

    blue = z_loc_abs * 10000 + scale_first_and_second_digit * 100 + bulge_val

    # Alpha Channel: bend (2 digits) + rotation (3 digits) + location signs (2 digits)
    # Format: bbRRR##
    bend_val = min(abs(math.floor(abs(bend) * 100.0)), 99)
    rotation_val = min(abs(math.floor(abs(rotation))), 999)

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

