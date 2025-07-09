import bpy

from bpy.types import (
    Operator,
)

from bpy.props import StringProperty

from . import json_helpers
from . import hansens_float_packer

import os
import json
from mathutils import Vector

def update_material(self, context):
    self.added_to_material = False

class SR_OT_AddEditCoordinatesNode(Operator):
    """
    Add the edit to the material
    """

    # at one point, this just added the Coordinates,
    # now it does everything but I can't be
    # faffed to rename it
    bl_idname = "shading_rig.add_edit_coordinates_node"
    bl_label = "Add Edit to Material"
    bl_description = "Adds the ShadingRigEdit node group and sets up Attributes"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if not (
            json_helpers.get_shading_rig_list_index() >= 0
            and len(scene.shading_rig_list) > 0
        ):
            return False

        active_item = scene.shading_rig_list[json_helpers.get_shading_rig_list_index()]

        if not (
            active_item.material
            and active_item.material.use_nodes
            and active_item.material.node_tree
        ):
            return False

        if active_item.added_to_material:
            return False

        if "ShadingRigEdit" not in bpy.data.node_groups:
            return False

        mat = active_item.material
        if mat and mat.node_tree:
            nodes = mat.node_tree.nodes
            if (
                "DiffuseToRGB_ShadingRig" not in nodes
                or "ColorRamp_ShadingRig" not in nodes
                # These names MUST NOT CHANGE
                # in the shader editor!
                # You can do whatever you want
                # with the nodes, just don't
                # touch these two.
            ):
                cls.poll_message_set(
                    "Material must contain 'DiffuseToRGB_ShadingRig' and 'ColorRamp_ShadingRig' nodes!"
                )
                return False

        return True

    def execute(self, context):
        scene = context.scene
        rig_index = json_helpers.get_shading_rig_list_index()
        active_item = scene.shading_rig_list[rig_index]

        material = active_item.material
        node_group_name = "ShadingRigEdit"
        node_tree = material.node_tree
        nodes = node_tree.nodes

        source_node = nodes.get("DiffuseToRGB_ShadingRig")
        dest_node = nodes.get("ColorRamp_ShadingRig")

        edit_coords_group = bpy.data.node_groups[node_group_name]

        new_node = material.node_tree.nodes.new("ShaderNodeGroup")
        new_node.node_tree = edit_coords_group

        empty_obj = active_item.empty_object
        if not empty_obj:
            self.report({"ERROR"}, "No Empty Object assigned to the rig.")
            material.node_tree.nodes.remove(new_node)
            return {"CANCELLED"}

        node_instance_name = f"{node_group_name}_{empty_obj.name}"
        new_node.name = node_instance_name
        new_node.label = node_instance_name
        new_node.location.x -= 200

        mix_node_lighten = material.node_tree.nodes.new("ShaderNodeMixRGB")
        mix_node_lighten_name = f"MixRGB_Lighten_{empty_obj.name}"
        mix_node_lighten.name = mix_node_lighten_name
        mix_node_lighten.label = mix_node_lighten_name

        mix_node_lighten.location = new_node.location + Vector((new_node.width + 40, 0))
        mix_node_lighten.blend_type = "LIGHTEN"

        previous_link = None
        if dest_node.inputs[0].is_linked:
            previous_link = dest_node.inputs[0].links[0]

        current_chain_tail_node = previous_link.from_node if previous_link else None

        y_offset_increment = 300
        new_y_pos = 0.0
        if current_chain_tail_node:
            new_y_pos = current_chain_tail_node.location.y + y_offset_increment
        else:
            new_y_pos = dest_node.location.y + y_offset_increment

        new_node.location.x = dest_node.location.x - 450
        new_node.location.y = new_y_pos

        mix_node_lighten.location.x = new_node.location.x + new_node.width + 100
        mix_node_lighten.location.y = new_y_pos

        node_tree.links.new(new_node.outputs[0], mix_node_lighten.inputs["Color2"])

        if previous_link:
            node_tree.links.new(
                previous_link.from_socket, mix_node_lighten.inputs["Color1"]
            )
        else:
            node_tree.links.new(
                source_node.outputs[0], mix_node_lighten.inputs["Color1"]
            )

        node_tree.links.new(mix_node_lighten.outputs["Color"], dest_node.inputs[0])

        attr_node = node_tree.nodes.new("ShaderNodeAttribute")

        attr_node.attribute_name = f"packed:{empty_obj.name}"
        attr_node.label = f"packed:{empty_obj.name}"
        attr_node.attribute_type = "OBJECT"

        attr_node.location.x = new_node.location.x - 200
        attr_node.location.y = new_y_pos - 200

        hansens_float_packer.unpack_nodes(
            attr_node, new_node, mix_node_lighten, node_tree
        )

        active_item.added_to_material = True
        self.report(
            {"INFO"},
            f"Node group and drivers added to material '{material.name}'.",
        )

        json_helpers.sync_scene_to_json(context.scene)

        return {"FINISHED"}


class SR_OT_SetupObject(Operator):
    """Sets up the active object with the base Shading Rig material."""

    bl_idname = "shading_rig.setup_object"
    bl_label = "Set Up Shading Rig on Object"
    bl_description = "Assigns and creates a unique copy of the ShadingRig_Base material for the active object"

    @classmethod
    def poll(cls, context):
        base_mat_name = "ShadingRig_Base"
        if base_mat_name not in bpy.data.materials:
            cls.poll_message_set(f"Base material '{base_mat_name}' not found.")
            return False

        obj = context.active_object
        if not obj or obj.type != "MESH":
            cls.poll_message_set("Select a mesh object.")
            return False

        for mat_slot in obj.material_slots:
            if mat_slot.material and mat_slot.material.name.startswith(base_mat_name):
                cls.poll_message_set("Object already has a Shading Rig material.")
                return False

        return True

    def execute(self, context):
        obj = context.active_object
        base_mat = bpy.data.materials.get("ShadingRig_Base")

        if not obj.material_slots:
            bpy.ops.object.material_slot_add()

        new_material = base_mat.copy()

        obj.material_slots[0].material = new_material

        context.scene.shading_rig_default_material = new_material

        self.report(
            {"INFO"}, f"'{obj.name}' set up with material '{new_material.name}'."
        )
        json_helpers.sync_scene_to_json(context.scene)

        return {"FINISHED"}


class SR_OT_AppendNodes(Operator):
    """Appends required node groups from the bundled .blend file."""

    bl_idname = "shading_rig.append_nodes"
    bl_label = "Append Required Nodes"
    bl_description = (
        "Appends node groups from the bundled 'shading_rig_nodes.blend' file"
    )

    @classmethod
    def poll(cls, context):
        if "ShadingRigEdit" in bpy.data.node_groups:
            cls.poll_message_set("Required nodes already exist in this file.")
            return False
        if "ShadingRig_Base" in bpy.data.materials:
            cls.poll_message_set("Required material 'ShadingRig_Base' already exists.")
            return False
        if len(context.scene.shading_rig_chararacter_name) <= 1:
            cls.poll_message_set("Set a character name first.")
            return False

        script_file = os.path.realpath(__file__)
        directory = os.path.dirname(script_file)
        blend_file_path = os.path.join(directory, "shading_rig_nodes.blend")
        if not os.path.exists(blend_file_path):
            cls.poll_message_set("Bundled 'shading_rig_nodes.blend' not found.")
            return False

        return True

    def execute(self, context):
        props_obj = bpy.data.objects.get(
            f"ShadingRigSceneProperties_{context.scene.shading_rig_chararacter_name}"
        )
        if not props_obj:
            # Create the empty if it doesn't exist
            props_obj = bpy.data.objects.new(
                f"ShadingRigSceneProperties_{context.scene.shading_rig_chararacter_name}",
                None,
            )
            bpy.context.collection.objects.link(props_obj)

            props_obj["shading_rig_list_index"] = 0
            props_obj["shading_rig_list"] = bpy.data.collections.new("ShadingRigList")

            try:
                props_obj.shading_rig_list_index = (
                    json_helpers.get_shading_rig_list_index()
                )
                props_obj.shading_rig_list = bpy.context.scene.shading_rig_list
            except Exception as e:
                self.report({"INFO"}, f"{e}")

            props_obj["character_name"] = context.scene.shading_rig_chararacter_name

        script_file = os.path.realpath(__file__)
        directory = os.path.dirname(script_file)
        blend_file_path = os.path.join(directory, "shading_rig_nodes.blend")

        with bpy.data.libraries.load(blend_file_path, link=False) as (
            data_from,
            data_to,
        ):
            data_to.node_groups = [name for name in data_from.node_groups]
            if "ShadingRig_Base" in data_from.materials:
                data_to.materials = ["ShadingRig_Base"]

        self.report(
            {"INFO"},
            f"Appended {len(data_to.node_groups)} node groups and {len(data_to.materials)} material(s).",
        )

        return {"FINISHED"}


# This is a weird little visual operator,
# doesn't really fit anywhere else
class SR_OT_SetEmptyDisplayType(Operator):
    bl_idname = "shading_rig.set_empty_display_type"
    bl_label = "Set Empty Display Type"
    bl_description = "Set the display type of the rig's empty object"

    display_type: StringProperty()

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if not (
            json_helpers.get_shading_rig_list_index() >= 0
            and len(scene.shading_rig_list) > 0
        ):
            cls.poll_message_set("No shading rigs in the list.")
            return False
        active_item = scene.shading_rig_list[json_helpers.get_shading_rig_list_index()]
        return active_item.empty_object is not None

    def execute(self, context):
        scene = context.scene
        active_item = scene.shading_rig_list[json_helpers.get_shading_rig_list_index()]
        empty_obj = active_item.empty_object

        if empty_obj:
            empty_obj.empty_display_type = self.display_type
            return {"FINISHED"}

        return {"CANCELLED"}


class SR_OT_SyncExternalData(Operator):
    """Sync external data from all ShadingRigSceneProperties objects into a combined object."""

    bl_idname = "shading_rig.sync_external_data"
    bl_label = "Sync External Data"
    bl_description = "Combine all external ShadingRigSceneProperties objects into a single combined object"

    @classmethod
    def poll(cls, context):
        # Check if there are any ShadingRigSceneProperties objects other than Combined
        properties_objects = []
        for obj in bpy.data.objects:
            if (
                obj.name.startswith("ShadingRigSceneProperties_")
                and obj.name != "ShadingRigSceneProperties_Combined"
            ):
                properties_objects.append(obj)

        if not properties_objects:
            cls.poll_message_set("No external ShadingRigSceneProperties objects found.")
            return False

        # Check if any of them have data
        has_data = False
        for props_obj in properties_objects:
            json_data = props_obj.get("shading_rig_list_json", "[]")
            if json_data and json_data != "[]":
                has_data = True
                break

        if not has_data:
            cls.poll_message_set("No external data found to sync.")
            return False

        return True

    def execute(self, context):
        try:
            # Create the combined properties object
            combined_obj = json_helpers.create_combined_properties_object()

            if not combined_obj:
                self.report({"ERROR"}, "Failed to create combined properties object.")
                return {"CANCELLED"}

            # Validate the combined JSON before syncing
            json_data = combined_obj.get("shading_rig_list_json", "[]")
            try:
                test_data = json.loads(json_data)
                if not isinstance(test_data, list):
                    self.report(
                        {"ERROR"},
                        f"Invalid JSON data format: expected list, got {type(test_data)}",
                    )
                    return {"CANCELLED"}
            except json.JSONDecodeError as e:
                self.report({"ERROR"}, f"Invalid JSON data: {e}")
                return {"CANCELLED"}

            # Sync the combined data to the scene
            json_helpers.sync_json_to_scene(context.scene)

            # Count how many objects were combined
            properties_objects = []
            for obj in bpy.data.objects:
                if (
                    obj.name.startswith("ShadingRigSceneProperties_")
                    and obj.name != "ShadingRigSceneProperties_Combined"
                ):
                    json_data = obj.get("shading_rig_list_json", "[]")
                    if json_data and json_data != "[]":
                        properties_objects.append(obj)

            # Count missing objects
            missing_objects = 0
            missing_materials = 0
            for rig in context.scene.shading_rig_list:
                if not rig.empty_object:
                    missing_objects += 1
                if not rig.material:
                    missing_materials += 1

            info_message = (
                f"Combined data from {len(properties_objects)} external objects."
            )
            if missing_objects > 0:
                info_message += f" Warning: {missing_objects} empty objects not found."
            if missing_materials > 0:
                info_message += f" Warning: {missing_materials} materials not found."

            self.report({"INFO"}, info_message)

            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Failed to sync external data: {e}")
            import traceback

            traceback.print_exc()
            return {"CANCELLED"}


class SR_OT_ClearCombinedData(Operator):
    """Clear the combined data and return to normal character-based behavior."""

    bl_idname = "shading_rig.clear_combined_data"
    bl_label = "Clear Combined Data"
    bl_description = "Remove the combined properties object and return to normal character-based behavior"

    @classmethod
    def poll(cls, context):
        combined_obj = bpy.data.objects.get("ShadingRigSceneProperties_Combined")
        if not combined_obj:
            cls.poll_message_set("No combined data to clear.")
            return False
        return True

    def execute(self, context):
        try:
            # Clear the combined properties object
            json_helpers.cleanup_combined_properties()

            # Clear the scene's shading rig list
            context.scene.shading_rig_list.clear()

            self.report(
                {"INFO"},
                "Combined data cleared. Returned to normal character-based behavior.",
            )

            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Failed to clear combined data: {e}")
            return {"CANCELLED"}


def update_character_name(self, context):
    new_name = self.shading_rig_chararacter_name
    if len(new_name) <= 0:
        self.shading_rig_chararacter_name = "Character"
        return

    props_obj = json_helpers.get_scene_properties_object()
    if props_obj:
        old_name = props_obj.get("character_name", "")
        if old_name != new_name:
            props_obj.name = f"ShadingRigSceneProperties_{new_name}"
            props_obj["character_name"] = new_name
            json_helpers.sync_scene_to_json(context.scene)
    else:
        # Create the empty if it doesn't exist
        props_obj = bpy.data.objects.new(
            f"ShadingRigSceneProperties_{new_name}",
            None,
        )
        bpy.context.collection.objects.link(props_obj)
