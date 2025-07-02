from . import json_helpers

def property_update_sync(self, context):
    """
    Generic update callback for rig item properties.
    Triggers a sync to the JSON data store.
    """
    json_helpers.sync_scene_to_json(context.scene)