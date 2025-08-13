bl_info = {
    "name": "Shading Rig + Cel Character Tools",
    "description": "Dynamic Art-Directable Stylised Shading for 3D Characters, Stepped Cloth/Sim Interpolation",
    "author": "Joseph Hansen (code, implementation, docs, and improvements), Lohit Petikam et al (original research), thorn (sanity checking, testing)",
    "version": (1, 3, 199),
    "blender": (4, 1, 0),
    "location": "Shading Rig",
    "category": "NPR",
}

import bpy
from mathutils import Vector

from . import (
    addremove_helpers,
    externaldata_helpers,
    hansens_float_packer,
    json_helpers,
    math_helpers,
    node_helpers,
    setup_helpers,
    update_helpers,
    visual_helpers,
    cct_multikey,
    cct_stepped_cloth_interpolation,
)

PRESETS = {
    "BEAN": {
        "name": "Bean",
        "elongation": 0.95,
        "sharpness": 0,
        "hardness": 0.40,
        "bulge": -1.0,
        "bend": -1.0,
        "mode": "ADD",
        "clamp": True,
        "rotation": 0,
    },
    "BOWL": {
        "name": "Bowl",
        "elongation": 0.91,
        "sharpness": 0.77,
        "hardness": 0.27,
        "bulge": 0,
        "bend": 0,
        "mode": "ADD",
        "clamp": True,
        "rotation": 0,
    },
    "LEAF": {
        "name": "Leaf",
        "elongation": 0.28,
        "sharpness": 1.0,
        "hardness": 0.28,
        "bulge": 0,
        "bend": 0,
        "mode": "ADD",
        "clamp": True,
        "rotation": 0,
    },
    "WORM": {
        "name": "Worm",
        "elongation": 1.0,
        "sharpness": 0,
        "hardness": 0.76,
        "bulge": 1.0,
        "bend": 1.0,
        "mode": "ADD",
        "clamp": True,
        "rotation": 30,
    },
    "CAPSULE": {
        "name": "Capsule",
        "elongation": 0.88,
        "sharpness": 0.06,
        "hardness": 0.46,
        "bulge": -1.0,
        "bend": 1.0,
        "mode": "LIGHTEN",
        "clamp": True,
        "rotation": 0,
    },
    "CRESCENT": {
        "name": "Crescent",
        "elongation": 0.92,
        "sharpness": 1.00,
        "hardness": 1.00,
        "bulge": -1.0,
        "bend": -1.0,
        "mode": "LIGHTEN",
        "clamp": True,
        "rotation": 0,
    },
    "TRIANGLE": {
        "name": "Triangle",
        "elongation": 0.60,
        "sharpness": 0.98,
        "hardness": 0.25,
        "bulge": -0.92,
        "bend": -0.8,
        "mode": "LIGHTEN",
        "clamp": True,
        "rotation": 9,
    },
    "PARABOLA": {
        "name": "Parabola",
        "elongation": 0.78,
        "sharpness": 0.58,
        "hardness": 0.25,
        "bulge": -0.92,
        "bend": -0.8,
        "mode": "LIGHTEN",
        "clamp": True,
        "rotation": 9,
    },
    "BUTTE": {
        "name": "Butte",
        "elongation": 0.78,
        "sharpness": 0.58,
        "hardness": 0.25,
        "bulge": -0.92,
        "bend": -0.8,
        "mode": "ADD",
        "clamp": True,
        "rotation": 9,
    },
}


def get_preset_items(self, context):
    """Generates the items for the preset EnumProperty."""
    items = []
    for identifier, settings in PRESETS.items():
        name = settings.get("name", identifier.replace("_", " ").title())
        items.append((identifier, name, f"Apply the {name} preset"))
    return items


def apply_preset(rig_item, preset_identifier):
    """Applies a preset's values to a given rig item."""
    if preset_identifier not in PRESETS:
        print(f"Shading Rig Error: Preset '{preset_identifier}' not found.")
        return

    preset_values = PRESETS[preset_identifier]

    for prop, value in preset_values.items():
        if hasattr(rig_item, prop):
            setattr(rig_item, prop, value)

previous_settings = {}
is_silhouette_view = False

# --------------------------------- Operators -------------------------------- #
def toggle_silhouette_view(self, context):
    global previous_settings, is_silhouette_view
    
    if not is_silhouette_view:
        previous_settings['shading_type'] = bpy.context.space_data.shading.type
        previous_settings['shading_light'] = bpy.context.space_data.shading.light
        previous_settings['background_type'] = bpy.context.space_data.shading.background_type
        previous_settings['background_color'] = bpy.context.space_data.shading.background_color[:]
        previous_settings['color_type'] = bpy.context.space_data.shading.color_type
        previous_settings['single_color'] = bpy.context.space_data.shading.single_color[:]
        previous_settings['show_cavity'] = bpy.context.space_data.shading.show_cavity
        previous_settings['show_xray'] = bpy.context.space_data.shading.show_xray
        previous_settings['show_shadows'] = bpy.context.space_data.shading.show_shadows
        previous_settings['show_overlays'] = bpy.context.space_data.overlay.show_overlays
        previous_settings['show_object_outline'] = bpy.context.space_data.shading.show_object_outline
        
        bpy.context.space_data.shading.type = 'SOLID'
        bpy.context.space_data.shading.light = 'FLAT'
        bpy.context.space_data.shading.background_type = "VIEWPORT"
        bpy.context.space_data.shading.background_color = (0, 0, 0)
        bpy.context.space_data.shading.color_type = 'SINGLE'
        bpy.context.space_data.shading.single_color = (1, 1, 1)
        bpy.context.space_data.shading.show_cavity = False
        bpy.context.space_data.shading.show_xray = False
        bpy.context.space_data.shading.show_shadows = False
        bpy.context.space_data.overlay.show_overlays = False
        bpy.context.space_data.shading.show_object_outline = False
        
        is_silhouette_view = True
    else:
        bpy.context.space_data.shading.type = previous_settings['shading_type']
        bpy.context.space_data.shading.light = previous_settings['shading_light']
        bpy.context.space_data.shading.background_type = previous_settings['background_type']
        bpy.context.space_data.shading.background_color = previous_settings['background_color']
        bpy.context.space_data.shading.color_type = previous_settings['color_type']
        bpy.context.space_data.shading.single_color = previous_settings['single_color']
        bpy.context.space_data.shading.show_cavity = previous_settings['show_cavity']
        bpy.context.space_data.shading.show_xray = previous_settings['show_xray']
        bpy.context.space_data.shading.show_shadows = previous_settings['show_shadows']
        bpy.context.space_data.overlay.show_overlays = previous_settings['show_overlays']
        bpy.context.space_data.shading.show_object_outline = previous_settings['show_object_outline']
        
        is_silhouette_view = False

class ToggleSilhouetteViewOperator(bpy.types.Operator):
    bl_idname = "wm.toggle_silhouette_view"
    bl_label = "Toggle Silhouette View"
    
    def execute(self, context):
        toggle_silhouette_view(self, context)
        return {'FINISHED'}

def draw_toggle_button(self, context):
    addon_prefs = context.preferences.addons["shading-rig-and-cel-character-tools"].preferences
    layout = self.layout
    if addon_prefs.show_matte_button:
        layout.operator(ToggleSilhouetteViewOperator.bl_idname, text="Toggle Matte", icon='MOD_MASK')

class SR_OT_ApplyPreset(bpy.types.Operator):
    """Applies the selected preset to the active rig item."""

    bl_idname = "shading_rig.apply_preset"
    bl_label = "Apply Preset"
    bl_description = "Apply the selected preset's values to the active effect"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if not scene.shading_rig_list:
            return False
        if scene.shading_rig_list_index >= len(scene.shading_rig_list):
            return False
        return True

    def execute(self, context):
        scene = context.scene
        active_item = scene.shading_rig_list[scene.shading_rig_list_index]

        if active_item.preset:
            apply_preset(active_item, active_item.preset)
            self.report({"INFO"}, f"Applied preset: {active_item.preset}")

        return {"FINISHED"}


bpy.app.driver_namespace["hansens_float_packer"] = hansens_float_packer
# this has to be globally assigned to work consistently
# actually, no, it just doesn't work consistently at all
# seems like this only works immediately after you install
# an addon. Definitely a bug

_previous_light_transforms = {}

from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import (
    Panel,
    PropertyGroup,
    UIList,
    AddonPreferences
)

class SRCCT_Preferences(AddonPreferences):
    bl_idname = 'shading-rig-and-cel-character-tools'
    
    show_icons: BoolProperty(
        name="Show Icons",
        description="Display icons in UI panels",
        default=True,
    )
    shading_rig_corr_readonly: BoolProperty(
        name="Read-Only Correlations",
        description="Make shading rig correlations read-only",
        default=True,
    )
    show_matte_button: BoolProperty(
        name="Show Matte Button",
        description="Display a header button to toggle silhouette view in the UI",
        default=True,
    )
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "show_icons", text="Show Icons in UI")
        layout.prop(self, "shading_rig_corr_readonly", text="Read-Only Correlations")
        layout.prop(self, "show_matte_button", text="Show Matte Button in Header")

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
    
    light_position: FloatVectorProperty(
        name="Light Position",
        subtype="TRANSLATION",
        unit="LENGTH",
        size=3,
        description="Stored position of the light object",
    )

    empty_position: FloatVectorProperty(
        name="Empty Position",
        subtype="TRANSLATION",
        unit="LENGTH",
        size=3,
        description="Stored position of the empty object",
    )

    empty_rotation: FloatVectorProperty(
        name="Empty Rotation",
        subtype="EULER",
        unit="ROTATION",
        size=3,
        description="Stored rotation of the empty object",
    )

    empty_scale: FloatVectorProperty(
        name="Empty Scale",
        subtype="NONE",
        size=3,
        default=(1.0, 1.0, 1.0),
        description="Stored scale of the empty object",
    )

    # Fergalicious definition?


def get_blend_mode_items(self, _context):
    """Dynamically generate blend mode items for the EnumProperty."""
    # This list of identifiers MUST match the order in setup_helpers.create_mode_mix_nodes
    blend_mode_identifiers = ["LIGHTEN", "SUBTRACT", "MULTIPLY", "DARKEN", "ADD"]

    icon_map = {
        "LIGHTEN": "OUTLINER_OB_LIGHT",
        "SUBTRACT": "REMOVE",
        "MULTIPLY": "PANEL_CLOSE",
        "DARKEN": "LIGHT",
        "ADD": "ADD",
    }

    items = []
    for i, identifier in enumerate(blend_mode_identifiers):
        # Format for UI display (e.g., "LIGHTEN" -> "Lighten")
        name = identifier.title()
        description = f"Set blend mode to {name}"
        icon = icon_map.get(identifier, "NONE")

        # The full tuple: (identifier, name, description, icon, number)
        items.append((identifier, name, description, icon, i))

    return items


def sr_rig_item_name_update(self, context):
    """When the rig item is renamed, rename the associated empty object."""
    if self.empty_object and self.name != self.empty_object.name:
        if self.name:
            self.empty_object.name = self.name


class SR_RigItem(PropertyGroup):
    """A single rig item containing an Empty and a Light object."""

    name: StringProperty(
        name="Effect Name",
        description="Name of the shading rig effect",
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
        update=update_helpers.update_parent_object,
    )

    material: PointerProperty(
        name="Affected Material",
        description="The material that will be affected by this rig",
        type=bpy.types.Material,
        update=setup_helpers.update_material,
    )

    added_to_material: BoolProperty(
        name="Node Group Added",
        description="Tracks if the EffectCoordinates node has been added to the material",
        default=False,
    )

    elongation: FloatProperty(
        name="Elongation",
        default=0.0,
        min=0,
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

    mask: FloatProperty(
        name="Mask",
        default=0.5,
        min=0,
        max=1,
        step=0.05,
        update=update_helpers.property_update_sync,
    )

    mode: EnumProperty(
        name="Mode",
        description="Mode of the shading rig effect",
        items=get_blend_mode_items,
        default=0,
        update=update_helpers.property_update_sync,
    )

    preset: EnumProperty(
        name="Preset",
        description="Load a predefined set of values for the effect",
        items=get_preset_items,
        update=update_helpers.property_update_sync,
    )

    clamp: BoolProperty(
        name="Clamp",
        description="Clamp the effect to a normalized 0-1 range",
        default=True,
        update=update_helpers.property_update_sync,
    )

    rotation: IntProperty(
        name="Spin",
        description="Rotate the Effect around its center",
        default=0,
        min=0,
        max=99,
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

    bl_label = "Shading Rig Effects"
    bl_idname = "SR_PT_shading_rig_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "SR + CCT"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        addon_prefs = context.preferences.addons["shading-rig-and-cel-character-tools"].preferences

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
            row = col.row(align=True)
            row.label(text="", icon="MATERIAL")
            row.prop(scene, "shading_rig_default_material", text="")

        layout.separator()

        box = layout.box()
        col = box.column(align=True)

        col.operator(setup_helpers.SR_OT_AppendNodes.bl_idname, icon="APPEND_BLEND" if addon_prefs.show_icons else "NONE")

        if len(scene.shading_rig_list) <= 0:
            col.operator(
                externaldata_helpers.SR_OT_SyncExternalData.bl_idname,
                icon="FILE_REFRESH" if addon_prefs.show_icons else "NONE",
            )
            col.operator(
                externaldata_helpers.SR_OT_ClearCombinedData.bl_idname, icon="TRASH" if addon_prefs.show_icons else "NONE"
            )

        col.operator(setup_helpers.SR_OT_SetupObject.bl_idname, icon="MATERIAL_DATA" if addon_prefs.show_icons else "NONE")

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

        if scene.shading_rig_list and 0 <= scene.shading_rig_list_index < len(
            scene.shading_rig_list
        ):
            active_item = scene.shading_rig_list[scene.shading_rig_list_index]

            box = layout.box()

            row = box.row(align=True)
            row.prop(
                active_item,
                "show_active_settings",
                icon="TRIA_DOWN" if active_item.show_active_settings else "TRIA_RIGHT",
                text="Active Effect Settings",
                emboss=False,
            )

            if active_item.show_active_settings:

                col = box.column(align=True)

                row = col.row(align=True)
                row.label(text="", icon="EMPTY_DATA")
                row.prop(active_item, "empty_object", text="")
                row = col.row(align=True)
                row.label(text="", icon="LIGHT" if addon_prefs.show_icons else "NONE")
                row.prop(active_item, "light_object", text="")
                row = col.row(align=True)
                row.label(text="", icon="MATERIAL" if addon_prefs.show_icons else "NONE")
                row.prop(active_item, "material", text="")

                row = col.row(align=True)
                row.label(text="Display Type")
                op = row.operator(
                    visual_helpers.SR_OT_SetEmptyDisplayType.bl_idname,
                    icon="MESH_UVSPHERE",
                    text="",
                )
                op.display_type = "SPHERE"

                op = row.operator(
                    visual_helpers.SR_OT_SetEmptyDisplayType.bl_idname,
                    icon="MESH_CIRCLE",
                    text="",
                )
                op.display_type = "CIRCLE"

                op = row.operator(
                    visual_helpers.SR_OT_SetEmptyDisplayType.bl_idname,
                    icon="MESH_CONE",
                    text="",
                )
                op.display_type = "CONE"

                op = row.operator(
                    visual_helpers.SR_OT_SetEmptyDisplayType.bl_idname,
                    icon="EMPTY_AXIS",
                    text="",
                )
                op.display_type = "PLAIN_AXES"

                row = col.row(align=True)
                split = row.split(factor=0.5)
                splitcol1 = split.column(align=True)
                splitcol2 = split.column(align=True)
                splitcol1.label(text="Parent Object")
                splitcol2.prop(active_item, "parent_object", text="")

                col.separator()

                col.prop(active_item, "elongation")
                col.prop(active_item, "sharpness")
                col.prop(active_item, "hardness")
                col.prop(active_item, "bulge")
                col.prop(active_item, "bend")
                # col.prop(active_item, "mask")
                col.prop(active_item, "rotation")
                col.prop(active_item, "mode")
                col.prop(active_item, "clamp")

                preset_row = col.row(align=True)
                preset_row.prop(active_item, "preset", text="")
                preset_row.operator(SR_OT_ApplyPreset.bl_idname, text="Apply Preset")

                col.separator()

                if not active_item.added_to_material:
                    active_object = context.active_object
                    if (
                        active_object
                        and active_object.type == "MESH"
                        and active_item.material
                        and active_item.material.node_tree
                    ):
                        if (
                            active_object.dimensions.x > 2.0
                            or active_object.dimensions.y > 2.0
                            or active_object.dimensions.z > 2.0
                        ):
                            col.label(
                                text="Active object is too large for shading rig effects to work properly.",
                            )
                            col.label(
                                text="You must scale down your object, add the effect, and then rescale."
                            )
                            col.label(
                                text="Shading Rig works best on human-sized characters."
                            )
                        else:
                            col.operator(
                                setup_helpers.SR_OT_AddEffectCoordinatesNode.bl_idname,
                                icon="NODETREE",
                            )
                    else:
                        col.label(
                            text="Select a set-up mesh object",
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
                col.enabled = not addon_prefs.shading_rig_corr_readonly
                col.prop(active_corr, "light_position", text="Light Position")
                col.prop(active_corr, "light_rotation", text="Light Rotation")
                col.prop(active_corr, "empty_position", text="Empty Position")
                col.prop(active_corr, "empty_scale", text="Empty Scale")
                col.prop(active_corr, "empty_rotation", text="Empty Rotation")


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
    # to break if you rename an effect...
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

                old_shading_node_name = f"ShadingRigEffect_{old_empty_name}"
                new_shading_node_name = f"ShadingRigEffect_{current_empty_name}"
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
        current_light_position = eval_light_obj.location
        light_obj_key = light_obj.name_full

        prev_transform = _previous_light_transforms.get(light_obj_key)
        if prev_transform:
            # make a 6 digit list combining XYZ rotation and XYZ position
            rot_pos = list(prev_transform[0]) + list(prev_transform[1])
            # check the distance between the two 6 digit lists
            curr_rot_pos = list(current_light_rotation) + list(current_light_position)
            if all(
                abs(a - b) < 1e-5 for a, b in zip(rot_pos, curr_rot_pos)
            ):
                print("No significant change in light transform; skipping update.")
                continue

        weighted_pos, weighted_scale, weighted_rotation = (
            math_helpers.calculateWeightedEmptyPosition(
                correlations, current_light_rotation, current_light_position
            )
        )
        empty_obj.location = weighted_pos
        empty_obj.scale = weighted_scale
        empty_obj.rotation_euler = weighted_rotation

        if light_obj_key not in _previous_light_transforms:
            _previous_light_transforms[light_obj_key] = [None, None]
        _previous_light_transforms[light_obj_key][0] = current_light_rotation.copy()
        _previous_light_transforms[light_obj_key][1] = current_light_position.copy()


# ---------------------- Register and unregister classes --------------------- #
CLASSES = [
    SRCCT_Preferences,
    SR_CorrelationItem,
    SR_RigItem,
    SR_UL_RigList,
    SR_UL_CorrelationList,
    addremove_helpers.SR_OT_RigList_Add,
    setup_helpers.SR_OT_AddEffectCoordinatesNode,
    visual_helpers.SR_OT_SetEmptyDisplayType,
    SR_OT_ApplyPreset,
    setup_helpers.SR_OT_SetupObject,
    setup_helpers.SR_OT_AppendNodes,
    externaldata_helpers.SR_OT_SyncExternalData,
    externaldata_helpers.SR_OT_ClearCombinedData,
    addremove_helpers.SR_OT_Correlation_Add,
    addremove_helpers.SR_OT_Correlation_Remove,
    addremove_helpers.SR_OT_RigList_Remove,
    SR_PT_ShadingRigPanel,
    cct_stepped_cloth_interpolation.OBJECT_OT_interpolate_bake,
    # MultiKey classes
    cct_multikey.ShapeKeyItem,
    cct_multikey.MultiKeyProperties,
    cct_multikey.MULTIKEY_OT_SetAllValues,
    cct_multikey.MULTIKEY_OT_SetAllTo,
    cct_multikey.MULTIKEY_OT_GetCurrentFrame,
    cct_multikey.MULTIKEY_OT_AddKeyframes,
    cct_multikey.MULTIKEY_OT_ClearNames,
    cct_multikey.MULTIKEY_OT_ClearAllNames,
    cct_multikey.MULTIKEY_OT_UpdateRows,
    cct_multikey.MULTIKEY_PT_Panel,
    
    ToggleSilhouetteViewOperator
]


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.PHYSICS_PT_cloth_cache.append(
        cct_stepped_cloth_interpolation.draw_cloth_func
    )

    # Shading Rig properties
    bpy.types.Scene.shading_rig_list = CollectionProperty(
        type=SR_RigItem,
        name="Shading Rig List",
    )
    bpy.types.Scene.shading_rig_list_index = IntProperty(
        name="Shading Rig List Index",
        default=0,
        min=0,
    )

    # MultiKey properties
    bpy.types.Scene.multikey_props = PointerProperty(
        type=cct_multikey.MultiKeyProperties
    )

    # Add MultiKey handlers

    if cct_multikey.update_frame_handler not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(cct_multikey.update_frame_handler)

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
        update=externaldata_helpers.update_character_name,
    )

    bpy.app.handlers.depsgraph_update_post.append(update_shading_rig_handler)

    bpy.app.handlers.load_post.append(load_handler)

    bpy.packing_algorithm = hansens_float_packer.packing_algorithm
    
    # Silhouette view
    bpy.types.Scene.is_silhouette_view = bpy.props.BoolProperty(
        name="Silhouette View",
        description="Toggle Silhouette View",
        default=False,
        update=toggle_silhouette_view
    )
    bpy.types.VIEW3D_HT_header.append(draw_toggle_button)
    


def unregister():    
    # Remove MultiKey handlers

    if cct_multikey.update_frame_handler in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(cct_multikey.update_frame_handler)

    # Remove Shading Rig properties
    del bpy.types.Scene.shading_rig_default_material
    del bpy.types.Scene.shading_rig_default_light
    del bpy.types.Scene.shading_rig_list
    del bpy.types.Scene.shading_rig_list_index
    del bpy.types.Scene.shading_rig_chararacter_name
    del bpy.types.Scene.shading_rig_show_defaults

    # Remove MultiKey properties
    del bpy.types.Scene.multikey_props

    # Remove handlers
    if update_shading_rig_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(update_shading_rig_handler)

    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)

    # Remove cache functions
    bpy.types.PHYSICS_PT_cloth_cache.remove(
        cct_stepped_cloth_interpolation.draw_cloth_func
    )

    # Unregister all classes
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
        
    # Remove silhouette view
    del bpy.types.Scene.is_silhouette_view
    bpy.types.VIEW3D_HT_header.remove(draw_toggle_button)
