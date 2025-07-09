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

    @classmethod
    def poll(cls, context):
        if json_helpers.get_scene_properties_object() is None:
            cls.poll_message_set(
                "Please set a character name and append required nodes"
            )
            return False

        if not context.scene.shading_rig_default_material:
            cls.poll_message_set("Please set up shading rig on an object")
            return False

        return True

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
        new_empty.empty_display_size = 0.25
        new_empty.show_name = True
        new_empty.show_in_front = True
        bpy.ops.transform.rotate(value=1.5708, orient_axis="X", orient_type="LOCAL")
        bpy.ops.transform.resize(value=(1.5, 1.5, 1.5))

        new_item.empty_object = new_empty

        new_item.name = (
            f"SR_Edit_{scene.shading_rig_chararacter_name}_{len(rig_list):03d}"
        )

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
                    "hardness",
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
                    f"shading_rig_list[{rig_index}].hardness",
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
                    f"bpy.packing_algorithm("
                    f"x_loc, y_loc, z_loc, x_scale, elongation, "
                    f"sharpness, hardness, bulge, bend, rotation)[{channel}]"
                )

        json_helpers.sync_scene_to_json(context.scene)

        return {"FINISHED"}


class SR_OT_Correlation_Add(Operator):
    """Add a new correlation to the active rig."""

    bl_idname = "shading_rig.correlation_add"
    bl_label = "Add Correlation"
    bl_description = "Add a new correlation to the active rig"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if not (
            json_helpers.get_shading_rig_list_index() >= 0
            and len(scene.shading_rig_list) > 0
        ):
            cls.poll_message_set("No edits in the list.")
            return False

        if not scene.shading_rig_list[
            json_helpers.get_shading_rig_list_index()
        ].light_object:
            cls.poll_message_set("Active edit has no Light Object assigned.")
            return False

        if not scene.shading_rig_list[
            json_helpers.get_shading_rig_list_index()
        ].empty_object:
            cls.poll_message_set("Active edit has no Empty Object assigned.")
            return False

        if not scene.shading_rig_chararacter_name:
            cls.poll_message_set("Please set a character name.")
            return False

        if not scene.shading_rig_list[
            json_helpers.get_shading_rig_list_index()
        ].added_to_material:
            cls.poll_message_set("Add the edit to a material first.")
            return False

        return True

    def execute(self, context):
        try:
            scene = context.scene
            active_rig_item = scene.shading_rig_list[
                json_helpers.get_shading_rig_list_index()
            ]

            light_obj = active_rig_item.light_object
            empty_obj = active_rig_item.empty_object

            if not light_obj or not empty_obj:
                self.report(
                    {"ERROR"}, "Active edit has no Light or Empty Object assigned."
                )
                return {"CANCELLED"}

            new_corr = active_rig_item.correlations.add()
            new_corr.name = f"Correlation_{scene.shading_rig_chararacter_name}_{len(active_rig_item.correlations):03d}"

            new_corr.light_rotation = light_obj.rotation_euler
            new_corr.empty_position = empty_obj.location
            new_corr.empty_scale = empty_obj.scale

            active_rig_item.correlations_index = len(active_rig_item.correlations) - 1

            self.report({"INFO"}, f"Stored pose in '{new_corr.name}'.")

        except Exception as e:
            self.report({"ERROR"}, "Failed to add correlation. " + str(e))
            return {"CANCELLED"}

        json_helpers.sync_scene_to_json(context.scene)
        return {"FINISHED"}


class SR_OT_Correlation_Remove(Operator):
    """Remove the selected correlation from the active edit."""

    bl_idname = "shading_rig.correlation_remove"
    bl_label = "Remove Correlation"
    bl_description = "Remove the selected correlation from the active edit"

    @classmethod
    def poll(cls, context):
        scene = context.scene

        if not (
            json_helpers.get_shading_rig_list_index() >= 0
            and len(scene.shading_rig_list) > 0
        ):
            cls.poll_message_set("No edits in the list.")
            return False
        active_rig_item = scene.shading_rig_list[
            json_helpers.get_shading_rig_list_index()
        ]
        return len(active_rig_item.correlations) > 0

    def execute(self, context):
        scene = context.scene
        active_rig_item = scene.shading_rig_list[
            json_helpers.get_shading_rig_list_index()
        ]
        index = active_rig_item.correlations_index

        if index >= len(active_rig_item.correlations):
            return {"CANCELLED"}

        removed_name = active_rig_item.correlations[index].name
        active_rig_item.correlations.remove(index)

        if index > 0:
            active_rig_item.correlations_index = index - 1
        else:
            active_rig_item.correlations_index = 0

        self.report({"INFO"}, f"Removed correlation '{removed_name}' from edit.")
        json_helpers.sync_scene_to_json(context.scene)
        return {"FINISHED"}


class SR_OT_RigList_Remove(Operator):
    """Remove the selected rig from the list."""

    bl_idname = "shading_rig.list_remove"
    bl_label = "Remove Edit"
    bl_description = (
        "Remove the selected edit and its associated objects from the scene"
    )

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
                "hardness",
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


def update_parent_object(self, context):
    """Create or update a child of constraint on the empty object, to parent_object"""
    active_rig_item = self

    if not active_rig_item.empty_object:
        return

    empty_obj = active_rig_item.empty_object
    parent_obj = active_rig_item.parent_object

    constraint_name = "ShadingRig Parent"
    child_of_constraint = empty_obj.constraints.get(constraint_name)

    if parent_obj:
        if not child_of_constraint:
            child_of_constraint = empty_obj.constraints.new(type="CHILD_OF")
            child_of_constraint.name = constraint_name
        child_of_constraint.target = parent_obj
    else:
        if child_of_constraint:
            empty_obj.constraints.remove(child_of_constraint)
