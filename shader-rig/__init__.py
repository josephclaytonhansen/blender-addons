bl_info = {
    "name": "Shading Rig",
    "description": "Dynamic Art-directable Stylised Shading for 3D Characters",
    "author": "Joseph Hansen (code, implementation, and improvements), Lohit Petikam et al (original research), Nick Ewing (testing), thorn (sanity checking and helpful reminders)",
    "version": (1, 2, 106),
    "blender": (4, 1, 0),
    "location": "Shading Rig",
    "category": "NPR",
}

import bpy

from . import math_helpers
from . import json_helpers
from . import setup_helpers
from . import addremove_helpers
from . import update_helpers
from mathutils import Vector

from . import hansens_float_packer

bpy.app.driver_namespace["hansens_float_packer"] = hansens_float_packer
# this has to be globally assigned to work consistently
# actually, no, it just doesn't work consistently at all
# seems like this only works immediately after you install
# an addon. Definitely a bug

_previous_light_rotations = {}

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
    Panel,
)


# -------------------------------- Definitions ------------------------------- #
class SR_CorrelationItem(PropertyGroup):
    """A single correlation item."""

    name: StringProperty(name="Name", default="New Correlation")

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

    # Fergalicious definition?


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

    parent_object: PointerProperty(
        name="Parent Object",
        description="The object to which the Empty will be parented",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type in {"MESH", "CURVE", "EMPTY"},
        update=addremove_helpers.update_parent_object,
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

    elongation: FloatProperty(
        name="Elongation",
        default=0.0,
        min=-1,
        max=1,
        step=0.05,
        update=update_helpers.property_update_sync,
    )

    sharpness: FloatProperty(
        name="Sharpness",
        default=0.0,
        min=0,
        max=1.0,
        step=0.05,
        update=update_helpers.property_update_sync,
    )

    hardness: FloatProperty(
        name="Hardness",
        default=0.5,
        min=0,
        max=1.0,
        step=0.02,
        update=update_helpers.property_update_sync,
    )

    bulge: FloatProperty(
        name="Bulge",
        default=0.0,
        min=-1.0,
        max=1.0,
        step=0.05,
        update=update_helpers.property_update_sync,
    )

    bend: FloatProperty(
        name="Bend",
        default=0.0,
        min=-1.0,
        max=1.0,
        step=0.05,
        update=update_helpers.property_update_sync,
    )

    rotation: FloatProperty(
        name="Rotation",
        default=0.0,
        min=-3.14,
        max=3.14,
        step=0.1,
        unit="ROTATION",
        update=update_helpers.property_update_sync,
    )

    show_active_settings: BoolProperty(
        name="Show Active Rig Settings",
        description="Toggle visibility of active rig settings",
        default=True,
    )

    correlations: CollectionProperty(type=SR_CorrelationItem)

    correlations_index: IntProperty(name="Selected Correlation Index", default=0)

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


class SR_UL_CorrelationList(UIList):
    """UIList for displaying the list of correlations for a rig."""

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):

        if self.layout_type in {"DEFAULT", "COMPACT"}:

            layout.prop(item, "name", text="", emboss=False, icon="DOT")

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon="DOT")


# --------------------------------- UI Panel --------------------------------- #
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
            text="Settings",
            emboss=False,
        )

        if scene.shading_rig_show_defaults:
            col = box.column(align=True)
            row = col.row(align=True)
            split = row.split(factor=0.5)
            splitcol1 = split.column(align=True)
            splitcol2 = split.column(align=True)
            splitcol1.label(text="Character Name")
            splitcol2.prop(scene, "shading_rig_chararacter_name", text="")
            row = col.row(align=True)
            row.label(text="", icon="LIGHT")
            row.prop(scene, "shading_rig_default_light", text="")
            col.prop(scene, "shading_rig_corr_readonly")

        layout.separator()

        box = layout.box()
        col = box.column(align=True)

        col.operator(setup_helpers.SR_OT_AppendNodes.bl_idname, icon="APPEND_BLEND")

        if len(scene.shading_rig_list) <= 0:
            col.operator(
                setup_helpers.SR_OT_SyncExternalData.bl_idname, icon="FILE_REFRESH"
            )
            col.operator(setup_helpers.SR_OT_ClearCombinedData.bl_idname, icon="TRASH")

        col.operator(setup_helpers.SR_OT_SetupObject.bl_idname, icon="MATERIAL_DATA")

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
        col.operator(addremove_helpers.SR_OT_RigList_Add.bl_idname, icon="ADD", text="")
        col.operator(
            addremove_helpers.SR_OT_RigList_Remove.bl_idname, icon="REMOVE", text=""
        )

        if True:
            try:
                active_item = scene.shading_rig_list[
                    json_helpers.get_shading_rig_list_index()
                ]
            except Exception as e:
                print(f"Shading Rig Debug: {e} (this is fine)")
                return

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
                    setup_helpers.SR_OT_SetEmptyDisplayType.bl_idname,
                    icon="MESH_UVSPHERE",
                    text="",
                )
                op.display_type = "SPHERE"

                op = row.operator(
                    setup_helpers.SR_OT_SetEmptyDisplayType.bl_idname,
                    icon="MESH_CIRCLE",
                    text="",
                )
                op.display_type = "CIRCLE"

                op = row.operator(
                    setup_helpers.SR_OT_SetEmptyDisplayType.bl_idname,
                    icon="MESH_CONE",
                    text="",
                )
                op.display_type = "CONE"

                op = row.operator(
                    setup_helpers.SR_OT_SetEmptyDisplayType.bl_idname,
                    icon="EMPTY_AXIS",
                    text="",
                )
                op.display_type = "PLAIN_AXES"

                col.separator()

                col.prop(active_item, "parent_object", text="Parent Object")

                col.prop(active_item, "elongation")
                col.prop(active_item, "sharpness")
                col.prop(active_item, "hardness")
                col.prop(active_item, "bulge")
                col.prop(active_item, "bend")
                col.prop(active_item, "rotation")

                if not active_item.added_to_material:
                    col.operator(
                        setup_helpers.SR_OT_AddEditCoordinatesNode.bl_idname,
                        icon="NODETREE",
                    )

            box = layout.box()
            box.label(text="Correlations")
            row = box.row()
            row.template_list(
                "SR_UL_CorrelationList",
                "",
                active_item,
                "correlations",
                active_item,
                "correlations_index",
            )
            col = row.column(align=True)
            col.operator(
                addremove_helpers.SR_OT_Correlation_Add.bl_idname,
                icon="ADD",
                text="",
            )
            col.operator(
                addremove_helpers.SR_OT_Correlation_Remove.bl_idname,
                icon="REMOVE",
                text="",
            )

            if (
                active_item.correlations_index >= 0
                and len(active_item.correlations) > 0
            ):
                active_corr = active_item.correlations[active_item.correlations_index]

                corr_box = box.box()
                corr_box.prop(active_corr, "name", text="Name")

                col = corr_box.column(align=True)
                col.enabled = not scene.shading_rig_corr_readonly
                col.prop(active_corr, "light_rotation", text="Light Rotation")
                col.prop(active_corr, "empty_position", text="Empty Position")
                col.prop(active_corr, "empty_scale", text="Empty Scale")


@bpy.app.handlers.persistent
def load_handler(dummy):
    if bpy.data.objects.get("ShadingRigSceneProperties"):
        json_helpers.sync_json_to_scene(bpy.context.scene)
        # As long as the addon is installed,
        # this should allow appending between files


@bpy.app.handlers.persistent
def update_shading_rig_handler(scene, depsgraph):
    """
    Handles automatic updates for the Shading Rig system.
    1. Detects renames of Empty objects and syncs shader node names.
    2. Interpolates Empty transform based on Light rotation.
    """
    # realistically, though, something is almost certain
    # to break if you rename an edit...
    # I'll probably fix that at some point
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
        correlations = rig_item.correlations
        if not light_obj:
            print(
                f"Shading Rig Debug: Skipping rig '{rig_item.name}' - no Light object assigned."
            )
            continue
        if len(correlations) == 0:
            print(
                f"Shading Rig Debug: Skipping rig '{rig_item.name}' - no correlations found."
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

        weighted_pos, weighted_scale = math_helpers.calculateWeightedEmptyPosition(
            correlations, current_light_rotation
        )
        empty_obj.location = weighted_pos
        empty_obj.scale = weighted_scale

        _previous_light_rotations[light_obj_key] = current_light_rotation.copy()


# ---------------------- Register and unregister classes --------------------- #
CLASSES = [
    SR_CorrelationItem,
    SR_RigItem,
    SR_UL_RigList,
    SR_UL_CorrelationList,
    addremove_helpers.SR_OT_RigList_Add,
    setup_helpers.SR_OT_AddEditCoordinatesNode,
    setup_helpers.SR_OT_SetEmptyDisplayType,
    setup_helpers.SR_OT_SetupObject,
    setup_helpers.SR_OT_AppendNodes,
    setup_helpers.SR_OT_SyncExternalData,
    setup_helpers.SR_OT_ClearCombinedData,
    addremove_helpers.SR_OT_Correlation_Add,
    addremove_helpers.SR_OT_Correlation_Remove,
    addremove_helpers.SR_OT_RigList_Remove,
    SR_PT_ShadingRigPanel,
]


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.shading_rig_list = CollectionProperty(
        type=SR_RigItem,
        name="Shading Rig List",
    )
    bpy.types.Scene.shading_rig_list_index = IntProperty(
        name="Shading Rig List Index",
        default=0,
        min=0,
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

    bpy.types.Scene.shading_rig_chararacter_name = StringProperty(
        name="Character Name",
        description="Name of the character being shaded",
        default="",
        update=setup_helpers.update_character_name,
    )

    bpy.app.handlers.depsgraph_update_post.append(update_shading_rig_handler)

    bpy.app.handlers.load_post.append(load_handler)

    bpy.types.Scene.shading_rig_corr_readonly = BoolProperty(
        name="Read-Only Correlations",
        description="Make stored correlation values read-only",
        default=True,
    )

    bpy.packing_algorithm = hansens_float_packer.packing_algorithm


def unregister():
    del bpy.types.Scene.shading_rig_default_material
    del bpy.types.Scene.shading_rig_default_light

    del bpy.types.Scene.shading_rig_list
    del bpy.types.Scene.shading_rig_list_index
    del bpy.types.Scene.shading_rig_chararacter_name

    if update_shading_rig_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(update_shading_rig_handler)

    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)

    del bpy.types.Scene.shading_rig_show_defaults
    del bpy.types.Scene.shading_rig_corr_readonly

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
