from . import json_helpers
import bpy

def property_update_sync(self, context):
    """
    Generic update callback for rig item properties.
    Triggers a sync to the JSON data store.
    """
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