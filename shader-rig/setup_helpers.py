import os

import bpy
from bpy.types import (
    Operator,
)
from mathutils import Matrix

from . import hansens_float_packer, json_helpers


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

        al = context.active_object.location
        bl = active_item.empty_object.location
        distance = (al - bl).length
        if distance > 1.5:
            cls.poll_message_set("Move the empty object closer to the active object")
            return False
        elif distance < 0.1:
            cls.poll_message_set("Move the empty object outside of the active object")
            return False

        mat = active_item.material
        if mat and mat.node_tree:
            nodes = mat.node_tree.nodes
            if (
                "ShadingRig_Entry" not in nodes
                or "ShadingRig_Ramp" not in nodes
                # These names MUST NOT CHANGE
                # in the shader editor!
                # You can do whatever you want
                # with the nodes, just don't
                # touch these two.
            ):
                cls.poll_message_set(
                    "Material must contain 'ShadingRig_Entry' and 'ShadingRig_Ramp' nodes!"
                )
                return False
        else:
            cls.poll_message_set("Material must have a valid node tree!")
            return False

        return True

    def execute(self, context):
        scene = context.scene

        a = context.active_object
        mat = a.matrix_local
        location, rotation, scale = mat.decompose()
        mat_scale = Matrix.LocRotScale(None, None, scale)
        a.data.transform(mat_scale)
        a.scale = 1, 1, 1

        rig_index = json_helpers.get_shading_rig_list_index()
        active_item = scene.shading_rig_list[rig_index]
        material = active_item.material
        node_group_name = "ShadingRigEffect"
        node_tree = material.node_tree
        nodes = node_tree.nodes
        source_node = nodes.get("ShadingRig_Entry")
        dest_node = nodes.get("ShadingRig_Ramp")
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

        attr_node = node_tree.nodes.new("ShaderNodeAttribute")
        attr_node.attribute_name = f"packed:{empty_obj.name}"
        attr_node.label = f"packed:{empty_obj.name}"
        attr_node.attribute_type = "OBJECT"

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

        attr_node.location.x = new_node.location.x - 200
        attr_node.location.y = new_y_pos - 200

        mode_raw, mask_value, hardness_value = hansens_float_packer.unpack_nodes(
            attribute_node=attr_node,
            edit_node=new_node,
            node_tree=node_tree,
            effect_empty=empty_obj,
        )

        if previous_link:
            base_color_socket = previous_link.from_socket
        else:
            base_color_socket = source_node.outputs[0]

        mix_node_lighten = node_tree.nodes.new("ShaderNodeMixRGB")
        mix_node_lighten.location.x = new_node.location.x - 200
        mix_node_lighten.location.y = new_y_pos - 200
        mix_node_lighten.blend_type = "LIGHTEN"

        node_tree.links.new(base_color_socket, mix_node_lighten.inputs[1])
        node_tree.links.new(new_node.outputs[0], mix_node_lighten.inputs[2])
        node_tree.links.new(hardness_value.outputs[0], mix_node_lighten.inputs[0])

        node_tree.links.new(mix_node_lighten.outputs[0], dest_node.inputs[0])

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
