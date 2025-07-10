import json

import bpy

# ---------------------------------------------------------------------------- #
#                                 JSON helpers                                 #
# ---------------------------------------------------------------------------- #

# CollectionProperties have to be stored as JSON to work as object properties
# This is incredibly stupid but ¯\_(ツ)_/¯


def serialize_rig_list_to_json(rig_list):
    """Convert rig list to JSON string."""
    data = []
    for rig in rig_list:
        empty_object_name = ""
        if rig.empty_object and hasattr(rig.empty_object, "name"):
            empty_object_name = rig.empty_object.name
        light_object_name = ""
        if rig.light_object and hasattr(rig.light_object, "name"):
            light_object_name = rig.light_object.name
        material_name = ""
        if rig.material and hasattr(rig.material, "name"):
            material_name = rig.material.name
        rig_data = {
            "name": rig.name,
            "elongation": rig.elongation,
            "sharpness": rig.sharpness,
            "hardness": rig.hardness,
            "bulge": rig.bulge,
            "bend": rig.bend,
            "mask": rig.mask,
            "mode": rig.mode,
            "added_to_material": rig.added_to_material,
            "correlations_index": rig.correlations_index,
            "empty_object_name": empty_object_name,
            "light_object_name": light_object_name,
            "material_name": material_name,
            "correlations": [
                {
                    "name": corr.name,
                    "light_rotation": list(corr.light_rotation),
                    "empty_position": list(corr.empty_position),
                    "empty_rotation": list(corr.empty_rotation),
                    "empty_scale": list(corr.empty_scale),
                }
                for corr in rig.correlations
            ],
        }
        data.append(rig_data)
    return json.dumps(data)


def deserialize_rig_list_from_json(json_string):
    """Convert JSON string back to rig list data."""
    if not json_string:
        return []
    return json.loads(json_string)


# It's not enough to serialize, we need to sync between
# the existing CollectionProperty and the JSON string
# because BLENDER CAN'T DO IT NATIVELY?!?!?!?!?!
# (╯°□°)╯︵ ┻━┻


def sync_scene_to_json(scene):
    """Save scene rig list to JSON on empty object."""
    json_data = serialize_rig_list_to_json(scene.shading_rig_list)
    set_shading_rig_list_json(json_data)


def sync_json_to_scene(scene):
    """Load rig list from JSON into scene collection."""
    json_data = get_shading_rig_list_json()
    rig_data_list = deserialize_rig_list_from_json(json_data)

    # Clear existing
    scene.shading_rig_list.clear()

    # Rebuild from JSON
    for rig_data in rig_data_list:
        new_rig = scene.shading_rig_list.add()

        # Set basic properties first
        new_rig.name = rig_data["name"]
        new_rig.elongation = rig_data["elongation"]
        new_rig.sharpness = rig_data["sharpness"]
        new_rig.hardness = rig_data["hardness"]
        new_rig.bulge = rig_data["bulge"]
        new_rig.bend = rig_data["bend"]
        new_rig.mask = rig_data["mask"]
        new_rig.mode = rig_data["mode"]
        new_rig.added_to_material = rig_data["added_to_material"]
        new_rig.correlations_index = rig_data["correlations_index"]

        # Handle object references carefully - only assign if objects exist
        if rig_data.get("empty_object_name"):
            empty_obj = bpy.data.objects.get(rig_data["empty_object_name"])
            if empty_obj and empty_obj.type == "EMPTY":
                new_rig.empty_object = empty_obj

        if rig_data.get("light_object_name"):
            light_obj = bpy.data.objects.get(rig_data["light_object_name"])
            if light_obj and light_obj.type == "LIGHT":
                new_rig.light_object = light_obj

        if rig_data.get("material_name"):
            material = bpy.data.materials.get(rig_data["material_name"])
            if material:
                new_rig.material = material

        # Rebuild correlations
        for corr_data in rig_data["correlations"]:
            new_corr = new_rig.correlations.add()
            new_corr.name = corr_data["name"]
            new_corr.light_rotation = corr_data["light_rotation"]
            new_corr.empty_position = corr_data["empty_position"]
            new_corr.empty_rotation = corr_data["empty_rotation"]
            new_corr.empty_scale = corr_data["empty_scale"]


def combine_multiple_json_shading_rig_lists(json_list):
    """Combine multiple JSON shading rig lists into one."""
    combined_rig_list = []
    for json_data in json_list:
        rig_data_list = deserialize_rig_list_from_json(json_data)
        combined_rig_list.extend(rig_data_list)
    return json.dumps(combined_rig_list)


def create_combined_properties_object():
    """Create a combined properties object from all existing ShadingRigSceneProperties objects."""
    # Find all ShadingRigSceneProperties objects
    properties_objects = []
    for obj in bpy.data.objects:
        if (
            obj.name.startswith("ShadingRigSceneProperties_")
            and obj.name != "ShadingRigSceneProperties_Combined"
        ):
            properties_objects.append(obj)

    if not properties_objects:
        return None

    # Collect all JSON data from these objects
    json_data_list = []
    for props_obj in properties_objects:
        json_data = props_obj.get("shading_rig_list_json", "[]")
        if json_data and json_data != "[]":
            json_data_list.append(json_data)

    if not json_data_list:
        return None

    # Create or get the combined properties object
    combined_obj_name = "ShadingRigSceneProperties_Combined"
    combined_obj = bpy.data.objects.get(combined_obj_name)

    if not combined_obj:
        combined_obj = bpy.data.objects.new(combined_obj_name, None)
        bpy.context.collection.objects.link(combined_obj)
        combined_obj["shading_rig_list_index"] = 0
        combined_obj["character_name"] = "Combined"

    # Combine all the JSON data
    combined_json = combine_multiple_json_shading_rig_lists(json_data_list)
    combined_obj["shading_rig_list_json"] = combined_json

    return combined_obj


def use_combined_properties():
    """Check if we should use the combined properties object."""
    combined_obj = bpy.data.objects.get("ShadingRigSceneProperties_Combined")
    return combined_obj is not None


# ---------------------------------------------------------------------------- #
#             Getters/setters for object level "scene" properties              #
# ---------------------------------------------------------------------------- #


def get_scene_properties_object():
    """Get the ShadingRigSceneProperties empty object."""

    if use_combined_properties():
        combined_obj = bpy.data.objects.get("ShadingRigSceneProperties_Combined")
        if combined_obj:
            return combined_obj

    props_obj = bpy.data.objects.get(
        f"ShadingRigSceneProperties_{bpy.context.scene.shading_rig_chararacter_name}"
    )
    return props_obj


def get_shading_rig_list_index():
    props_obj = get_scene_properties_object()
    return props_obj.get("shading_rig_list_index", 0)


def set_shading_rig_list_index(value):
    props_obj = get_scene_properties_object()
    props_obj["shading_rig_list_index"] = value


def get_shading_rig_list_json():
    props_obj = get_scene_properties_object()
    return props_obj.get("shading_rig_list_json", "[]")


def set_shading_rig_list_json(json_data):
    props_obj = get_scene_properties_object()
    props_obj["shading_rig_list_json"] = json_data


def cleanup_combined_properties():
    """Remove the combined properties object to return to normal behavior."""
    combined_obj = bpy.data.objects.get("ShadingRigSceneProperties_Combined")
    if combined_obj:
        bpy.data.objects.remove(combined_obj)
