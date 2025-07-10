import json

import bpy
from bpy.types import (
    Operator,
)

from . import json_helpers


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
