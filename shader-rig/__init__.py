bl_info = {
    "name": "Shading Rig",
    "description": "Dynamic Art-directable Stylised Shading for 3D Characters",
    "author": "Joseph Hansen (implementation and code owner), Lohit Petikam et al (original research), Nick Ewing (testing)",
    "version": (1, 0, 0),
    "blender": (4, 1, 0),
    "location": "Shading Rig",
    "category": "NPR",
}

from mathutils import Vector, Quaternion, Euler


# Weight calculation functions
def getDistances(correspondences, currentLightRotation):
    """
    Prerequisite for calculating weights;
    Finds the angular distance between the current light rotation
    and each of the stored light rotations using quaternions for accuracy.
    """
    distances = []
    current_quat = currentLightRotation.to_quaternion()

    for corr in correspondences:
        corr_euler = Euler(corr.light_rotation, "XYZ")
        corr_quat = corr_euler.to_quaternion()
        dist = current_quat.rotation_difference(corr_quat).angle
        distances.append(dist)
    return distances


def getWeights(distances):
    """
    Calculates normalized inverse distance weights.
    A smaller distance results in a larger weight.
    All weights are positive and sum to 1.0.
    """
    if not distances:
        return []

    weights = []
    total_weight = 0.0
    epsilon = 1e-6

    for d in distances:
        weight = 1.0 / (d + epsilon)
        weights.append(weight)
        total_weight += weight

    if total_weight > 0:
        for i in range(len(weights)):
            weights[i] /= total_weight

    return weights


def calculateWeightedEmptyPosition(correspondences, currentLightRotation):
    """
    Given a list of light rotations -> empty positions and a current light
    rotation, interpolates the empty position.
    """
    if not correspondences:
        return [0.0, 0.0, 0.0], [1.0, 1.0, 1.0]
    if len(correspondences) == 1:
        return list(correspondences[0].empty_position), list(
            correspondences[0].empty_scale
        )

    distances = getDistances(correspondences, currentLightRotation)
    weights = getWeights(distances)

    weighted_position = Vector((0.0, 0.0, 0.0))
    weighted_scale = Vector((0.0, 0.0, 0.0))

    for i, corr in enumerate(correspondences):
        weight = weights[i]
        weighted_position += Vector(corr.empty_position) * weight
        weighted_scale += Vector(corr.empty_scale) * weight

    return list(weighted_position), list(weighted_scale)


_previous_light_rotations = {}

# Blender stuff
import bpy
import os

from bpy.props import (
    StringProperty,
    BoolProperty,
    PointerProperty,
    CollectionProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
)
from bpy.types import (
    PropertyGroup,
    UIList,
    Operator,
    Panel,
)


class SR_OT_SetEmptyDisplayType(Operator):
    bl_idname = "shading_rig.set_empty_display_type"
    bl_label = "Set Empty Display Type"
    bl_description = "Set the display type of the rig's empty object"

    display_type: StringProperty()

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if not (scene.shading_rig_list_index >= 0 and len(scene.shading_rig_list) > 0):
            return False
        active_item = scene.shading_rig_list[scene.shading_rig_list_index]
        return active_item.empty_object is not None

    def execute(self, context):
        scene = context.scene
        active_item = scene.shading_rig_list[scene.shading_rig_list_index]
        empty_obj = active_item.empty_object

        if empty_obj:
            empty_obj.empty_display_type = self.display_type
            return {"FINISHED"}

        return {"CANCELLED"}


# Definitions
class SR_CorrespondenceItem(PropertyGroup):
    """A single correspondence item."""

    name: StringProperty(name="Name", default="New Correspondence")

    light_rotation: FloatVectorProperty(
        name="Light Rotation",
        subtype="EULER",
        unit="ROTATION",
        size=3,
        description="Stored rotation of the light object",
    )

    empty_position: FloatVectorProperty(
        name="Empty Position",
        subtype="TRANSLATION",
        unit="LENGTH",
        size=3,
        description="Stored position of the empty object",
    )

    empty_scale: FloatVectorProperty(
        name="Empty Scale",
        subtype="NONE",
        size=3,
        default=(1.0, 1.0, 1.0),
        description="Stored scale of the empty object",
    )


def sr_rig_item_name_update(self, context):
    """When the rig item is renamed, rename the associated empty object."""
    if self.empty_object and self.name != self.empty_object.name:
        if self.name:
            self.empty_object.name = self.name


class SR_RigItem(PropertyGroup):
    """A single rig item containing an Empty and a Light object."""

    name: StringProperty(
        name="Edit Name",
        description="Name of the shading rig edit",
        update=sr_rig_item_name_update,
    )

    empty_object: PointerProperty(
        name="Empty Object",
        description="The Empty object that acts as a controller or origin point",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "EMPTY",
    )

    light_object: PointerProperty(
        name="Light Object",
        description="The Light object that acts as a light source or projection point",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "LIGHT",
    )

    material: PointerProperty(
        name="Affected Material",
        description="The material that will be affected by this rig",
        type=bpy.types.Material,
    )

    added_to_material: BoolProperty(
        name="Node Group Added",
        description="Tracks if the EditCoordinates node has been added to the material",
        default=False,
    )

    elongation: FloatProperty(name="Elongation", default=0.0, min=-1, max=1, step=0.05)

    sharpness: FloatProperty(name="Sharpness", default=0.0, min=-1, max=1.0, step=0.05)

    amount: FloatProperty(name="Amount", default=0.92, min=0, max=1.0, step=0.02)

    direction: IntProperty(name="Direction", default=1, min=0, max=1)

    bulge: FloatProperty(name="Bulge", default=0.0, min=-1.0, max=1.0, step=0.05)

    bend: FloatProperty(name="Bend", default=0.0, min=-1.0, max=1.0, step=0.05)

    rotation: FloatProperty(
        name="Rotation",
        default=0.0,
        min=-3.14,
        max=3.14,
        unit="ROTATION",
    )

    show_active_settings: BoolProperty(
        name="Show Active Rig Settings",
        description="Toggle visibility of active rig settings",
        default=True,
    )

    correspondences: CollectionProperty(type=SR_CorrespondenceItem)

    correspondences_index: IntProperty(name="Selected Correspondence Index", default=0)

    last_empty_name: StringProperty(
        name="Last Empty Name",
        description="Internal: Stores the last known name of the empty object for rename detection.",
        default="",
    )


class SR_UL_RigList(UIList):
    """UIList for displaying the list of shading rigs."""

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.prop(item, "name", text="", emboss=False, icon="EMPTY_DATA")

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon="OBJECT_DATA")


class SR_UL_CorrespondenceList(UIList):
    """UIList for displaying the list of correspondences for a rig."""

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):

        if self.layout_type in {"DEFAULT", "COMPACT"}:

            layout.prop(item, "name", text="", emboss=False, icon="DOT")

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon="DOT")


# Operators
class SR_OT_RigList_Add(Operator):
    """Add a new rig to the list."""

    bl_idname = "shading_rig.list_add"
    bl_label = "Add Rig"
    bl_description = "Create a new Empty and Light, and add them as a new rig"

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

        scene.shading_rig_list_index = len(rig_list) - 1

        return {"FINISHED"}


class SR_OT_AddEditCoordinatesNode(Operator):
    bl_idname = "shading_rig.add_edit_coordinates_node"
    bl_label = "Set Up Drivers For Edit"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if not (scene.shading_rig_list_index >= 0 and len(scene.shading_rig_list) > 0):
            return False

        active_item = scene.shading_rig_list[scene.shading_rig_list_index]

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
            ):
                cls.poll_message_set(
                    "Material must contain 'DiffuseToRGB_ShadingRig' and 'ColorRamp_ShadingRig' nodes."
                )
                return False

        return True

    def execute(self, context):
        scene = context.scene
        rig_index = scene.shading_rig_list_index
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

        def setup_driver(target_socket, source_id, source_data_path, id_type="OBJECT"):
            """Helper function to create a simple driver for a node socket's default_value."""
            fcurve = target_socket.driver_add("default_value")
            driver = fcurve.driver
            driver.type = "SCRIPTED"

            for var in driver.variables:
                driver.variables.remove(var)

            var = driver.variables.new()
            var.name = "var"
            var.targets[0].id_type = id_type
            var.targets[0].id = source_id
            var.targets[0].data_path = source_data_path
            driver.expression = "var"

        if len(new_node.inputs) < 9:
            self.report(
                {"ERROR"}, f"'{node_group_name}' node group has fewer than 9 inputs."
            )
            material.node_tree.nodes.remove(new_node)
            return {"CANCELLED"}

        setup_driver(new_node.inputs[0], empty_obj, "location[0]")
        setup_driver(new_node.inputs[1], empty_obj, "location[1]")
        setup_driver(new_node.inputs[2], empty_obj, "location[2]")
        setup_driver(new_node.inputs[3], empty_obj, "scale[0]")

        base_path = f"shading_rig_list[{rig_index}]"
        setup_driver(new_node.inputs[4], scene, f"{base_path}.elongation", "SCENE")
        setup_driver(new_node.inputs[5], scene, f"{base_path}.sharpness", "SCENE")
        setup_driver(new_node.inputs[6], scene, f"{base_path}.bend", "SCENE")
        setup_driver(new_node.inputs[7], scene, f"{base_path}.bulge", "SCENE")
        setup_driver(new_node.inputs[8], scene, f"{base_path}.rotation", "SCENE")

        mix_node = material.node_tree.nodes.new("ShaderNodeMixRGB")
        mix_node_name = f"MixRGB_{empty_obj.name}"
        mix_node.name = mix_node_name
        mix_node.label = mix_node_name

        new_node.location.x -= 200
        mix_node.location = new_node.location + Vector((new_node.width + 40, 0))

        if active_item.direction == 1:
            mix_node.blend_type = "LIGHTEN"
        else:
            mix_node.blend_type = "DARKEN"

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

        mix_node.location.x = new_node.location.x + new_node.width + 40
        mix_node.location.y = new_y_pos

        node_tree.links.new(new_node.outputs[0], mix_node.inputs["Color2"])

        if previous_link:
            node_tree.links.new(previous_link.from_socket, mix_node.inputs["Color1"])
        else:
            node_tree.links.new(source_node.outputs[0], mix_node.inputs["Color1"])

        node_tree.links.new(mix_node.outputs["Color"], dest_node.inputs[0])

        fcurve = mix_node.driver_add("blend_type")
        driver = fcurve.driver
        driver.type = "SCRIPTED"
        var = driver.variables.new()
        var.name = "direction"
        var.targets[0].id_type = "SCENE"
        var.targets[0].id = scene
        var.targets[0].data_path = f"{base_path}.direction"
        driver.expression = "8 if direction == 1 else 7"

        setup_driver(mix_node.inputs["Fac"], scene, f"{base_path}.amount", "SCENE")

        active_item.added_to_material = True
        self.report(
            {"INFO"},
            f"Node group and drivers added to material '{material.name}'.",
        )

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

        script_file = os.path.realpath(__file__)
        directory = os.path.dirname(script_file)
        blend_file_path = os.path.join(directory, "shading_rig_nodes.blend")
        if not os.path.exists(blend_file_path):
            cls.poll_message_set("Bundled 'shading_rig_nodes.blend' not found.")
            return False

        return True

    def execute(self, context):
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


class SR_OT_Correspondence_Add(Operator):
    """Add a new correspondence to the active rig."""

    bl_idname = "shading_rig.correspondence_add"
    bl_label = "Add Correspondence"
    bl_description = "Add a new correspondence to the active rig"

    @classmethod
    def poll(cls, context):
        scene = context.scene

        return scene.shading_rig_list_index >= 0 and len(scene.shading_rig_list) > 0

    def execute(self, context):
        scene = context.scene
        active_rig_item = scene.shading_rig_list[scene.shading_rig_list_index]

        if not active_rig_item.light_object:
            self.report({"ERROR"}, "Active rig has no Light Object assigned.")
            return {"CANCELLED"}
        if not active_rig_item.empty_object:
            self.report({"ERROR"}, "Active rig has no Empty Object assigned.")
            return {"CANCELLED"}

        light_obj = active_rig_item.light_object
        empty_obj = active_rig_item.empty_object

        new_corr = active_rig_item.correspondences.add()
        new_corr.name = f"Correspondence.{len(active_rig_item.correspondences):03d}"

        new_corr.light_rotation = light_obj.rotation_euler
        new_corr.empty_position = empty_obj.location
        new_corr.empty_scale = empty_obj.scale

        active_rig_item.correspondences_index = len(active_rig_item.correspondences) - 1

        self.report({"INFO"}, f"Stored pose in '{new_corr.name}'.")
        return {"FINISHED"}


class SR_OT_Correspondence_Remove(Operator):
    """Remove the selected correspondence from the active rig."""

    bl_idname = "shading_rig.correspondence_remove"
    bl_label = "Remove Correspondence"
    bl_description = "Remove the selected correspondence from the active rig"

    @classmethod
    def poll(cls, context):
        scene = context.scene

        if not (scene.shading_rig_list_index >= 0 and len(scene.shading_rig_list) > 0):
            return False
        active_rig_item = scene.shading_rig_list[scene.shading_rig_list_index]
        return len(active_rig_item.correspondences) > 0

    def execute(self, context):
        scene = context.scene
        active_rig_item = scene.shading_rig_list[scene.shading_rig_list_index]
        index = active_rig_item.correspondences_index

        if index >= len(active_rig_item.correspondences):
            return {"CANCELLED"}

        removed_name = active_rig_item.correspondences[index].name
        active_rig_item.correspondences.remove(index)

        if index > 0:
            active_rig_item.correspondences_index = index - 1
        else:
            active_rig_item.correspondences_index = 0

        self.report({"INFO"}, f"Removed correspondence '{removed_name}' from rig.")
        return {"FINISHED"}


class SR_OT_RigList_Remove(Operator):
    """Remove the selected rig from the list."""

    bl_idname = "shading_rig.list_remove"
    bl_label = "Remove Rig"
    bl_description = "Remove the selected rig and its associated objects from the scene"

    @classmethod
    def poll(cls, context):
        return len(context.scene.shading_rig_list) > 0

    def execute(self, context):
        scene = context.scene
        rig_list = scene.shading_rig_list
        index = scene.shading_rig_list_index

        if index >= len(rig_list):
            return {"CANCELLED"}

        item_to_remove = rig_list[index]

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
            scene.shading_rig_list_index = index - 1
        else:
            scene.shading_rig_list_index = 0

        if objects_to_delete:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in objects_to_delete:
                if obj.name in bpy.data.objects:
                    bpy.data.objects[obj.name].select_set(True)
            bpy.ops.object.delete()

        return {"FINISHED"}


# UI Panel
class SR_PT_ShadingRigPanel(Panel):
    """Creates a Panel in the 3D Viewport's sidebar."""

    bl_label = "Shading Rig Edits"
    bl_idname = "SR_PT_shading_rig_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Shading Rig"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        row = box.row()
        row.prop(
            scene,
            "shading_rig_show_defaults",
            icon="TRIA_DOWN" if scene.shading_rig_show_defaults else "TRIA_RIGHT",
            text="Defaults",
            emboss=False,
        )

        if scene.shading_rig_show_defaults:
            col = box.column(align=True)
            row = col.row(align=True)
            row.label(text="", icon="MATERIAL")
            row.prop(scene, "shading_rig_default_material", text="")
            row = col.row(align=True)
            row.label(text="", icon="LIGHT")
            row.prop(scene, "shading_rig_default_light", text="")
            col.prop(scene, "shading_rig_corr_readonly")
            col.operator(SR_OT_SetupObject.bl_idname, icon="MATERIAL_DATA")
            col.operator(SR_OT_AppendNodes.bl_idname, icon="APPEND_BLEND")

        layout.separator()

        row = layout.row()
        row.template_list(
            "SR_UL_RigList",
            "",
            scene,
            "shading_rig_list",
            scene,
            "shading_rig_list_index",
        )

        col = row.column(align=True)
        col.operator(SR_OT_RigList_Add.bl_idname, icon="ADD", text="")
        col.operator(SR_OT_RigList_Remove.bl_idname, icon="REMOVE", text="")

        if scene.shading_rig_list_index >= 0 and len(scene.shading_rig_list) > 0:
            active_item = scene.shading_rig_list[scene.shading_rig_list_index]

            box = layout.box()

            row = box.row(align=True)
            row.prop(
                active_item,
                "show_active_settings",
                icon="TRIA_DOWN" if active_item.show_active_settings else "TRIA_RIGHT",
                text="Active Edit Settings",
                emboss=False,
            )

            if active_item.show_active_settings:

                col = box.column(align=True)

                row = col.row(align=True)
                row.label(text="", icon="EMPTY_DATA")
                row.prop(active_item, "empty_object", text="")
                row = col.row(align=True)
                row.label(text="", icon="LIGHT")
                row.prop(active_item, "light_object", text="")
                row = col.row(align=True)
                row.label(text="", icon="MATERIAL")
                row.prop(active_item, "material", text="")

                row = col.row(align=True)
                row.label(text="Display Type")
                op = row.operator(
                    SR_OT_SetEmptyDisplayType.bl_idname, icon="MESH_UVSPHERE", text=""
                )
                op.display_type = "SPHERE"

                op = row.operator(
                    SR_OT_SetEmptyDisplayType.bl_idname, icon="MESH_CIRCLE", text=""
                )
                op.display_type = "CIRCLE"

                op = row.operator(
                    SR_OT_SetEmptyDisplayType.bl_idname, icon="MESH_CONE", text=""
                )
                op.display_type = "CONE"

                op = row.operator(
                    SR_OT_SetEmptyDisplayType.bl_idname, icon="EMPTY_AXIS", text=""
                )
                op.display_type = "PLAIN_AXES"

                col.separator()

                col.prop(active_item, "elongation")
                col.prop(active_item, "sharpness")
                col.prop(active_item, "amount")
                col.prop(active_item, "direction")
                col.prop(active_item, "bulge")
                col.prop(active_item, "bend")
                col.prop(active_item, "rotation")

                if not active_item.added_to_material:
                    col.operator(
                        SR_OT_AddEditCoordinatesNode.bl_idname, icon="NODETREE"
                    )

            box = layout.box()
            box.label(text="Correspondences")
            row = box.row()
            row.template_list(
                "SR_UL_CorrespondenceList",
                "",
                active_item,
                "correspondences",
                active_item,
                "correspondences_index",
            )
            col = row.column(align=True)
            col.operator(SR_OT_Correspondence_Add.bl_idname, icon="ADD", text="")
            col.operator(SR_OT_Correspondence_Remove.bl_idname, icon="REMOVE", text="")

            if (
                active_item.correspondences_index >= 0
                and len(active_item.correspondences) > 0
            ):
                active_corr = active_item.correspondences[
                    active_item.correspondences_index
                ]

                corr_box = box.box()
                corr_box.prop(active_corr, "name", text="Name")

                col = corr_box.column(align=True)
                col.enabled = not scene.shading_rig_corr_readonly
                col.prop(active_corr, "light_rotation", text="Light Rotation")
                col.prop(active_corr, "empty_position", text="Empty Position")
                col.prop(active_corr, "empty_scale", text="Empty Scale")


@bpy.app.handlers.persistent
def update_shading_rig_handler(scene, depsgraph):
    """
    Handles automatic updates for the Shading Rig system.
    1. Detects renames of Empty objects and syncs shader node names.
    2. Interpolates Empty transform based on Light rotation.
    """
    for rig_item in scene.shading_rig_list:
        empty_obj = rig_item.empty_object
        if not empty_obj:
            print(
                f"Shading Rig Debug: Skipping rig '{rig_item.name}' - no Empty object assigned."
            )
            continue

        current_empty_name = empty_obj.name
        if rig_item.last_empty_name and rig_item.last_empty_name != current_empty_name:
            old_empty_name = rig_item.last_empty_name

            if rig_item.material and rig_item.material.node_tree:
                node_tree = rig_item.material.node_tree

                old_shading_node_name = f"ShadingRigEdit_{old_empty_name}"
                new_shading_node_name = f"ShadingRigEdit_{current_empty_name}"
                shading_node = node_tree.nodes.get(old_shading_node_name)
                if shading_node:
                    shading_node.name = new_shading_node_name
                    shading_node.label = new_shading_node_name

                old_mix_node_name = f"MixRGB_{old_empty_name}"
                new_mix_node_name = f"MixRGB_{current_empty_name}"
                mix_node = node_tree.nodes.get(old_mix_node_name)
                if mix_node:
                    mix_node.name = new_mix_node_name
                    mix_node.label = new_mix_node_name

        if rig_item.last_empty_name != current_empty_name:
            rig_item.last_empty_name = current_empty_name

        light_obj = rig_item.light_object
        correspondences = rig_item.correspondences
        if not light_obj:
            print(
                f"Shading Rig Debug: Skipping rig '{rig_item.name}' - no Light object assigned."
            )
            continue
        if len(correspondences) == 0:
            print(
                f"Shading Rig Debug: Skipping rig '{rig_item.name}' - no correspondences found."
            )
            continue

        eval_light_obj = light_obj.evaluated_get(depsgraph)
        if not eval_light_obj:
            print(
                f"Shading Rig Debug: Skipping rig '{rig_item.name}' - could not get evaluated light object from depsgraph."
            )
            continue

        current_light_rotation = eval_light_obj.rotation_euler
        light_obj_key = light_obj.name_full

        prev_rot = _previous_light_rotations.get(light_obj_key)
        if prev_rot:
            v_prev = Vector(prev_rot)
            v_curr = Vector(current_light_rotation)
            if (v_prev - v_curr).length < 1e-5:
                continue

        weighted_pos, weighted_scale = calculateWeightedEmptyPosition(
            correspondences, current_light_rotation
        )
        empty_obj.location = weighted_pos
        empty_obj.scale = weighted_scale

        _previous_light_rotations[light_obj_key] = current_light_rotation.copy()


# Register and unregister classes
CLASSES = [
    SR_CorrespondenceItem,
    SR_RigItem,
    SR_UL_RigList,
    SR_UL_CorrespondenceList,
    SR_OT_RigList_Add,
    SR_OT_AddEditCoordinatesNode,
    SR_OT_SetEmptyDisplayType,
    SR_OT_SetupObject,
    SR_OT_AppendNodes,
    SR_OT_Correspondence_Add,
    SR_OT_Correspondence_Remove,
    SR_OT_RigList_Remove,
    SR_PT_ShadingRigPanel,
]


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.shading_rig_list = CollectionProperty(type=SR_RigItem)
    bpy.types.Scene.shading_rig_list_index = IntProperty(
        name="Selected Rig Index", default=0
    )
    bpy.types.Scene.shading_rig_default_material = PointerProperty(
        name="Default Material",
        description="The default material assigned to new rigs",
        type=bpy.types.Material,
    )
    bpy.types.Scene.shading_rig_default_light = PointerProperty(
        name="Default Light",
        description="The default light assigned to new rigs",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "LIGHT",
    )
    bpy.types.Scene.shading_rig_show_defaults = BoolProperty(
        name="Show Defaults",
        description="Toggle visibility of default settings",
        default=True,
    )

    bpy.app.handlers.depsgraph_update_post.append(update_shading_rig_handler)

    bpy.types.Scene.shading_rig_corr_readonly = BoolProperty(
        name="Read-Only Correspondences",
        description="Make stored correspondence values read-only",
        default=True,
    )


def unregister():
    del bpy.types.Scene.shading_rig_list
    del bpy.types.Scene.shading_rig_list_index
    del bpy.types.Scene.shading_rig_default_material
    del bpy.types.Scene.shading_rig_default_light

    if update_shading_rig_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(update_shading_rig_handler)

    del bpy.types.Scene.shading_rig_show_defaults
    del bpy.types.Scene.shading_rig_corr_readonly

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    try:
        unregister()
    except (RuntimeError, AttributeError):
        pass
    register()
