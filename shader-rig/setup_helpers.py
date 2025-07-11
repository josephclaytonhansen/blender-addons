import os

import bpy
from bpy.types import (
    Operator,
)
from mathutils import Matrix, Vector

from . import hansens_float_packer, json_helpers


def update_material(self, context):
    self.added_to_material = False


def create_mode_mix_nodes(
    node_tree,
    mode_value_output,
    base_color_input,
    effect_color_output,
    hardness_output,
    location,
):

    def new_math(op, val=None):
        node = node_tree.nodes.new("ShaderNodeMath")
        node.operation = op
        if val is not None:
            node.inputs[1].default_value = val
        return node

    def new_mix(blend_type, x_offset=0, y_offset=0):
        node = node_tree.nodes.new("ShaderNodeMixRGB")
        node.blend_type = blend_type
        node.location = location + Vector((x_offset, y_offset))
        return node

    # Create all blend mode mix nodes
    mix_lighten = new_mix("LIGHTEN", 0, 200)  # mode 0
    mix_subtract = new_mix("SUBTRACT", 0, 100)  # mode 1
    mix_multiply = new_mix("MULTIPLY", 0, 0)  # mode 2
    mix_darken = new_mix("DARKEN", 0, -100)  # mode 3
    mix_add = new_mix("ADD", 0, -200)  # mode 4

    # Connect inputs to all blend modes
    for mix_node in [mix_lighten, mix_subtract, mix_multiply, mix_darken, mix_add]:
        node_tree.links.new(base_color_input, mix_node.inputs[1])  # Color1
        node_tree.links.new(effect_color_output, mix_node.inputs[2])  # Color2
        node_tree.links.new(hardness_output, mix_node.inputs[0])  # Fac

    # Round the mode value to nearest integer
    mode_rounded = new_math("ROUND")
    mode_rounded.location = location + Vector((200, 300))
    node_tree.links.new(mode_value_output, mode_rounded.inputs[0])

    # Clamp mode between 0 and 4
    mode_clamped = new_math("MAXIMUM", 0.0)
    mode_clamped.location = location + Vector((300, 300))
    node_tree.links.new(mode_rounded.outputs[0], mode_clamped.inputs[0])

    mode_clamped2 = new_math("MINIMUM", 4.0)
    mode_clamped2.location = location + Vector((400, 300))
    node_tree.links.new(mode_clamped.outputs[0], mode_clamped2.inputs[0])

    mode_0_check = new_math("COMPARE", 0.0)
    mode_0_check.location = location + Vector((500, 200))
    node_tree.links.new(mode_clamped2.outputs[0], mode_0_check.inputs[0])

    mode_1_check = new_math("COMPARE", 1.0)
    mode_1_check.location = location + Vector((500, 100))
    node_tree.links.new(mode_clamped2.outputs[0], mode_1_check.inputs[0])

    mode_2_check = new_math("COMPARE", 2.0)
    mode_2_check.location = location + Vector((500, 0))
    node_tree.links.new(mode_clamped2.outputs[0], mode_2_check.inputs[0])

    mode_3_check = new_math("COMPARE", 3.0)
    mode_3_check.location = location + Vector((500, -100))
    node_tree.links.new(mode_clamped2.outputs[0], mode_3_check.inputs[0])

    mode_4_check = new_math("COMPARE", 4.0)
    mode_4_check.location = location + Vector((500, -200))
    node_tree.links.new(mode_clamped2.outputs[0], mode_4_check.inputs[0])

    # Create selection factors by multiplying mode check with hardness
    # This ensures hardness is properly applied to the selected mode

    # Multiply mode selection by hardness to get the actual blend factor
    factor_0 = new_math("MULTIPLY")
    factor_0.location = location + Vector((700, 200))
    node_tree.links.new(mode_0_check.outputs[0], factor_0.inputs[0])
    node_tree.links.new(hardness_output, factor_0.inputs[1])

    factor_1 = new_math("MULTIPLY")
    factor_1.location = location + Vector((700, 100))
    node_tree.links.new(mode_1_check.outputs[0], factor_1.inputs[0])
    node_tree.links.new(hardness_output, factor_1.inputs[1])

    factor_2 = new_math("MULTIPLY")
    factor_2.location = location + Vector((700, 0))
    node_tree.links.new(mode_2_check.outputs[0], factor_2.inputs[0])
    node_tree.links.new(hardness_output, factor_2.inputs[1])

    factor_3 = new_math("MULTIPLY")
    factor_3.location = location + Vector((700, -100))
    node_tree.links.new(mode_3_check.outputs[0], factor_3.inputs[0])
    node_tree.links.new(hardness_output, factor_3.inputs[1])

    factor_4 = new_math("MULTIPLY")
    factor_4.location = location + Vector((700, -200))
    node_tree.links.new(mode_4_check.outputs[0], factor_4.inputs[0])
    node_tree.links.new(hardness_output, factor_4.inputs[1])

    # Mix each blend result with the base color using the hardness-adjusted factor
    # This properly applies hardness to each mode
    final_0 = new_mix("MIX", 900, 200)
    node_tree.links.new(
        factor_0.outputs[0], final_0.inputs[0]
    )  # Hardness * mode_selection
    node_tree.links.new(base_color_input, final_0.inputs[1])  # Base color
    node_tree.links.new(mix_lighten.outputs[0], final_0.inputs[2])  # Blend result

    final_1 = new_mix("MIX", 900, 100)
    node_tree.links.new(factor_1.outputs[0], final_1.inputs[0])
    node_tree.links.new(base_color_input, final_1.inputs[1])
    node_tree.links.new(mix_subtract.outputs[0], final_1.inputs[2])

    final_2 = new_mix("MIX", 900, 0)
    node_tree.links.new(factor_2.outputs[0], final_2.inputs[0])
    node_tree.links.new(base_color_input, final_2.inputs[1])
    node_tree.links.new(mix_multiply.outputs[0], final_2.inputs[2])

    final_3 = new_mix("MIX", 900, -100)
    node_tree.links.new(factor_3.outputs[0], final_3.inputs[0])
    node_tree.links.new(base_color_input, final_3.inputs[1])
    node_tree.links.new(mix_darken.outputs[0], final_3.inputs[2])

    final_4 = new_mix("MIX", 900, -200)
    node_tree.links.new(factor_4.outputs[0], final_4.inputs[0])
    node_tree.links.new(base_color_input, final_4.inputs[1])
    node_tree.links.new(mix_add.outputs[0], final_4.inputs[2])

    sum_01 = new_mix("ADD", 1100, 150)
    node_tree.links.new(final_0.outputs[0], sum_01.inputs[1])
    node_tree.links.new(final_1.outputs[0], sum_01.inputs[2])
    sum_01.inputs[0].default_value = 1.0

    sum_23 = new_mix("ADD", 1100, -50)
    node_tree.links.new(final_2.outputs[0], sum_23.inputs[1])
    node_tree.links.new(final_3.outputs[0], sum_23.inputs[2])
    sum_23.inputs[0].default_value = 1.0

    sum_0123 = new_mix("ADD", 1300, 50)
    node_tree.links.new(sum_01.outputs[0], sum_0123.inputs[1])
    node_tree.links.new(sum_23.outputs[0], sum_0123.inputs[2])
    sum_0123.inputs[0].default_value = 1.0

    final_sum = new_mix("ADD", 1500, 0)
    node_tree.links.new(sum_0123.outputs[0], final_sum.inputs[1])
    node_tree.links.new(final_4.outputs[0], final_sum.inputs[2])
    final_sum.inputs[0].default_value = 1.0

    return final_sum.outputs[0]


class SR_OT_AddEffectCoordinatesNode(Operator):
    """
    Add the effect to the material
    """

    # at one point, this just added the Coordinates,
    # now it does everything but I can't be
    # faffed to rename it
    bl_idname = "shading_rig.add_effect_coordinates_node"
    bl_label = "Add Effect to Material"
    bl_description = "Adds the ShadingRigEffect node group and sets up Attributes"

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

        if "ShadingRigEffect" not in bpy.data.node_groups:
            return False

        al = context.active_object.location
        bl = active_item.empty_object.location
        distance = (al - bl).length
        if distance > 2:
            cls.poll_message_set("Move the empty object closer to the active object")
            return False
        elif distance < 0.25:
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
        effect_coords_group = bpy.data.node_groups[node_group_name]
        new_node = material.node_tree.nodes.new("ShaderNodeGroup")
        new_node.node_tree = effect_coords_group
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
            effect_node=new_node,
            node_tree=node_tree,
            effect_empty=empty_obj,
        )

        # if previous_link:
        #     base_color_socket = previous_link.from_socket
        # else:
        #     base_color_socket = source_node.outputs[0]

        # mix_node_lighten = node_tree.nodes.new("ShaderNodeMixRGB")
        # mix_node_lighten.location.x = new_node.location.x - 200
        # mix_node_lighten.location.y = new_y_pos - 200
        # mix_node_lighten.blend_type = "LIGHTEN"

        # node_tree.links.new(base_color_socket, mix_node_lighten.inputs[1])
        # node_tree.links.new(new_node.outputs[0], mix_node_lighten.inputs[2])
        # node_tree.links.new(hardness_value.outputs[0], mix_node_lighten.inputs[0])

        # node_tree.links.new(mix_node_lighten.outputs[0], dest_node.inputs[0])

        if previous_link:
            base_color_socket = previous_link.from_socket
        else:
            base_color_socket = source_node.outputs[0]

        final_output = create_mode_mix_nodes(
            node_tree=node_tree,
            mode_value_output=mode_raw.outputs[0],
            base_color_input=base_color_socket,
            effect_color_output=new_node.outputs[0],
            hardness_output=hardness_value.outputs[0],
            location=Vector((new_node.location.x + 400, new_node.location.y)),
        )

        node_tree.links.new(final_output, dest_node.inputs[0])

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
            cls.poll_message_set(
                f"Base material '{base_mat_name}' not found! Please append the required nodes first."
            )
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
            self.report({"INFO"}, "Material slot added to the object.")

        new_material = base_mat.copy()

        obj.material_slots[len(obj.material_slots) - 1].material = new_material

        context.scene.shading_rig_default_material = new_material

        self.report(
            {"INFO"},
            f"'{obj.name}' set up with material '{new_material.name}' on slot {len(obj.material_slots)-1}.",
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
        if "ShadingRigEffect" in bpy.data.node_groups:
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
            cls.poll_message_set(
                "Bundled 'shading_rig_nodes.blend' not found. Reinstall the addon."
            )
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
