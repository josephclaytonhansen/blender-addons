import bpy
from . import presets_helpers

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
            presets_helpers.apply_preset(active_item, active_item.preset)
            self.report({"INFO"}, f"Applied preset: {active_item.preset}")

        return {"FINISHED"}
