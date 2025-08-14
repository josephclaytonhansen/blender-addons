import bpy
from bpy.types import (
    Operator,
)

from . import json_helpers

class SR_OT_ToggleEditMode(Operator):
    """Toggle Edit Mode for the active object"""
    bl_idname = "sr.toggle_edit_mode"
    bl_label = "Toggle Edit Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.types.Scene.is_evaluating_shading_rig:
            bpy.types.Scene.is_evaluating_shading_rig = False
            json_helpers.sync_scene_to_json(context.scene)
            return {"FINISHED"}
        else:
            bpy.types.Scene.is_evaluating_shading_rig = True
            json_helpers.sync_scene_to_json(context.scene)
            return {"FINISHED"}
        return {"CANCELLED"}
        