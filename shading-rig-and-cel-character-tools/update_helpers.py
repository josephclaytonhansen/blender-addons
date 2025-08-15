from . import json_helpers, sr_presets
import bpy

def property_update_sync(self, context):
    """
    Generic update callback for rig item properties.
    Triggers a sync to the JSON data store.
    """
    json_helpers.sync_scene_to_json(context.scene)

def apply_preset(rig_item, preset_identifier):
    """Applies a preset's values to a given rig item."""
    if preset_identifier not in sr_presets.PRESETS:
        print(f"Shading Rig Error: Preset '{preset_identifier}' not found.")
        return

    preset_values = sr_presets.PRESETS[preset_identifier]

    for prop, value in preset_values.items():
        if hasattr(rig_item, prop):
            setattr(rig_item, prop, value)

def update_preset(self, context):
    addon_prefs = bpy.context.preferences.addons["shading-rig-and-cel-character-tools"].preferences
    if addon_prefs.auto_apply_sr_presets:
        scene = context.scene
        active_item = scene.shading_rig_list[scene.shading_rig_list_index]

        if active_item.preset:
            apply_preset(active_item, active_item.preset)
    
    json_helpers.sync_scene_to_json(context.scene)
    
def update_parent_object(self, context):
    """Create or update a child of constraint on the empty object, to parent_object"""
    active_rig_item = self

    if not active_rig_item.empty_object:
        return

    empty_obj = active_rig_item.empty_object
    parent_obj = active_rig_item.parent_object

    constraint_name = "ShadingRig Parent"
    child_of_constraint = empty_obj.constraints.get(constraint_name)

    if parent_obj:
        if not child_of_constraint:
            child_of_constraint = empty_obj.constraints.new(type="CHILD_OF")
            child_of_constraint.name = constraint_name
        child_of_constraint.target = parent_obj
    else:
        if child_of_constraint:
            empty_obj.constraints.remove(child_of_constraint)