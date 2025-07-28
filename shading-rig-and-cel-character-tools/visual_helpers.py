from bpy.props import StringProperty
from bpy.types import (
    Operator,
)

from . import json_helpers


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
