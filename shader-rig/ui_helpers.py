import bpy
from . import presets_helpers

def get_preset_items(self, context):
    """Generates the items for the preset EnumProperty."""
    items = []
    for identifier, settings in presets_helpers.PRESETS.items():
        name = settings.get("name", identifier.replace("_", " ").title())
        items.append((identifier, name, f"Apply the {name} preset"))
    return items

class SR_PresetProperties(bpy.types.PropertyGroup):
    """Properties for the preset system."""
    preset: bpy.props.EnumProperty(
        name="Preset",
        description="Load a predefined set of values for the effect",
        items=get_preset_items,
    )

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

        preset_identifier = active_item.preset_ui.preset
        if preset_identifier:
            presets_helpers.apply_preset(active_item, preset_identifier)
            self.report({"INFO"}, f"Applied preset: {preset_identifier}")

        return {"FINISHED"}
