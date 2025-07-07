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
        rig_data = {
            "name": rig.name,
            "elongation": rig.elongation,
            "sharpness": rig.sharpness,
            "amount": rig.amount,
            "bulge": rig.bulge,
            "bend": rig.bend,
            "rotation": rig.rotation,
            "added_to_material": rig.added_to_material,
            "correspondences_index": rig.correspondences_index,
            "empty_object_name": rig.empty_object.name if rig.empty_object else "",
            "light_object_name": rig.light_object.name if rig.light_object else "",
            "material_name": rig.material.name if rig.material else "",
            "correspondences": [
                {
                    "name": corr.name,
                    "light_rotation": list(corr.light_rotation),
                    "empty_position": list(corr.empty_position),
                    "empty_scale": list(corr.empty_scale),
                }
                for corr in rig.correspondences
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
        new_rig.name = rig_data["name"]
        new_rig.elongation = rig_data["elongation"]
        new_rig.sharpness = rig_data["sharpness"]
        new_rig.amount = rig_data["amount"]
        new_rig.bulge = rig_data["bulge"]
        new_rig.bend = rig_data["bend"]
        new_rig.rotation = rig_data["rotation"]
        new_rig.added_to_material = rig_data["added_to_material"]
        new_rig.correspondences_index = rig_data["correspondences_index"]

        # Re-link objects by name
        if rig_data["empty_object_name"]:
            new_rig.empty_object = bpy.data.objects.get(rig_data["empty_object_name"])
        if rig_data["light_object_name"]:
            new_rig.light_object = bpy.data.objects.get(rig_data["light_object_name"])
        if rig_data["material_name"]:
            new_rig.material = bpy.data.materials.get(rig_data["material_name"])

        # Rebuild correspondences
        for corr_data in rig_data["correspondences"]:
            new_corr = new_rig.correspondences.add()
            new_corr.name = corr_data["name"]
            new_corr.light_rotation = corr_data["light_rotation"]
            new_corr.empty_position = corr_data["empty_position"]
            new_corr.empty_scale = corr_data["empty_scale"]


def combine_multiple_json_shading_rig_lists(json_list):
    """Combine multiple JSON shading rig lists into one."""
    combined_rig_list = []
    for json_data in json_list:
        rig_data_list = deserialize_rig_list_from_json(json_data)
        combined_rig_list.extend(rig_data_list)
    return serialize_rig_list_to_json(combined_rig_list)


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
