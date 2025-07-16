import bpy

PRESETS = {
    "BEAN": {
        "name": "Bean",
        "elongation": .95,
        "sharpness": 0,
        "hardness": 0.40,
        "bulge": -1.0,
        "bend": -1.0,
        "mode": "ADD",
        "clamp": True,
        "rotation": 0,
    },
    "BOWL": {
        "name": "BOWL",
        "elongation": 0.91,
        "sharpness": 0.77,
        "hardness": 0.27,
        "bulge": 0,
        "bend": 0,
        "mode": "ADD",
        "clamp": True,
        "rotation": 0,
    },
    "LEAF": {
        "name": "Leaf",
        "elongation": 0.28,
        "sharpness": 1.0,
        "hardness": 0.28,
        "bulge": 0,
        "bend": 0,
        "mode": "ADD",
        "clamp": True,
        "rotation": 0,
    },
    "WORM": {
        "name": "Worm",
        "elongation": 1.0,
        "sharpness": 0,
        "hardness": 0.76,
        "bulge": 1.0,
        "bend": 1.0,
        "mode": "ADD",
        "clamp": True,
        "rotation": 30,
    },
    "CAPSULE": {
        "name": "Capsule",
        "elongation": .88,
        "sharpness": 0.06,
        "hardness": 0.46,
        "bulge": -1.0,
        "bend": 1.0,
        "mode": "LIGHTEN",
        "clamp": True,
        "rotation": 0,
    },
    "CRESCENT": {
        "name": "Crescent",
        "elongation": .92,
        "sharpness": 1.00,
        "hardness": 1.00,
        "bulge": -1.0,
        "bend": -1.0,
        "mode": "LIGHTEN",
        "clamp": True,
        "rotation": 0,
    },
    "TRIANGLE": {
        "name": "Triangle",
        "elongation": .60,
        "sharpness": .98,
        "hardness": .25,
        "bulge": -0.92,
        "bend": -0.8,
        "mode": "LIGHTEN",
        "clamp": True,
        "rotation": 9,
    },
    "PARABOLA": {
        "name": "Parabola",
        "elongation": .78,
        "sharpness": .58,
        "hardness": .25,
        "bulge": -0.92,
        "bend": -0.8,
        "mode": "LIGHTEN",
        "clamp": True,
        "rotation": 9,
    },
    "BUTTE": {
        "name": "Butte",
        "elongation": .78,
        "sharpness": .58,
        "hardness": .25,
        "bulge": -0.92,
        "bend": -0.8,
        "mode": "ADD",
        "clamp": True,
        "rotation": 9,
    },
    
}


def get_preset_items(self, context):
    """Generates the items for the preset EnumProperty."""
    items = []
    for identifier, settings in PRESETS.items():
        name = settings.get("name", identifier.replace("_", " ").title())
        items.append((identifier, name, f"Apply the {name} preset"))
    return items


def apply_preset(rig_item, preset_identifier):
    """Applies a preset's values to a given rig item."""
    if preset_identifier not in PRESETS:
        print(f"Shading Rig Error: Preset '{preset_identifier}' not found.")
        return

    preset_values = PRESETS[preset_identifier]

    for prop, value in preset_values.items():
        if hasattr(rig_item, prop):
            setattr(rig_item, prop, value)

