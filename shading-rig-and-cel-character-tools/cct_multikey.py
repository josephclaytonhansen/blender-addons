import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)
from bpy.types import Operator, Panel, PropertyGroup

# ------------------------------------------------------------------------
#    Configuration
# ------------------------------------------------------------------------
MAX_SHAPE_KEYS = 52
DEFAULT_ROWS = 6
# ------------------------------------------------------------------------
#    Helper Functions
# ------------------------------------------------------------------------
def get_collections_callback(scene, context):
    """Callback for collection enumeration"""
    items = []

    try:
        if len(bpy.data.collections) == 0:
            items.append(("NONE", "No Collections Found", "Create a collection first"))
        else:
            for i, collection in enumerate(bpy.data.collections):
                items.append(
                    (str(i), collection.name, f"Collection: {collection.name}")
                )
    except Exception:
        # Fallback if there's any error
        items.append(
            ("0", "Error Loading Collections", "There was an error loading collections")
        )

    return items


def get_collection_name_from_enum(collection_enum_value):
    """Convert enum value back to collection name"""
    if not collection_enum_value:
        return None

    try:
        if collection_enum_value == "NONE":
            return None

        # If it's a numeric string, get the collection by index
        if collection_enum_value.isdigit():
            index = int(collection_enum_value)
            if index < len(bpy.data.collections):
                return list(bpy.data.collections)[index].name

        return None
    except:
        return None


def update_shape_key_live(self, context):
    """Update callback for live preview of shape keys"""
    props = context.scene.multikey_props
    if not props.collection or props.collection == "NONE":
        return

    # Find which shape key this belongs to
    for i, shape_key in enumerate(props.shape_keys):
        if shape_key == self:
            if shape_key.enabled and shape_key.name:
                collection_name = get_collection_name_from_enum(props.collection)
                if collection_name:
                    apply_shape_key_to_collection(
                        shape_key.name,
                        shape_key.value,
                        collection_name,
                        frame=None,
                        enabled=True,
                    )
            break


def apply_shape_key_to_collection(
    key_name, value, collection_name, frame=None, enabled=True
):
    """Apply shape key value to all objects in collection, optionally keyframe"""
    if not enabled or not key_name or not collection_name:
        return

    if collection_name not in bpy.data.collections:
        return

    collection = bpy.data.collections[collection_name]
    original_selection = list(bpy.context.selected_objects)

    try:
        # Clear selection
        for obj in bpy.context.selected_objects:
            obj.select_set(False)

        # Process objects in collection
        for obj in collection.all_objects:
            if not hasattr(obj.data, "shape_keys") or not obj.data.shape_keys:
                continue

            if not hasattr(obj.data.shape_keys, "key_blocks"):
                continue

            # Find and update the shape key
            for shape_key in obj.data.shape_keys.key_blocks:
                if shape_key.name == key_name:
                    shape_key.value = value

                    # Add keyframe if frame is specified
                    if frame is not None:
                        shape_key.keyframe_insert("value", frame=frame)
                    break

    finally:
        # Restore original selection
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in original_selection:
            obj.select_set(True)


# ------------------------------------------------------------------------
#    Property Classes
# ------------------------------------------------------------------------
class ShapeKeyItem(PropertyGroup):
    """Individual shape key properties"""

    name: StringProperty(
        name="Key Name",
        description="Name of the shape key (all objects must use identical shape key names)",
        default="",
        maxlen=64,
        update=update_shape_key_live,
    )

    value: FloatProperty(
        name="Value",
        description="Value (0.0 to 1.0) of the shape key",
        default=0.0,
        min=0.0,
        max=1.0,
        update=update_shape_key_live,
    )

    enabled: BoolProperty(
        name="Enabled",
        description="Enable/disable this key",
        default=True,
        update=update_shape_key_live,
    )


class MultiKeyProperties(PropertyGroup):
    """Main properties for the addon"""

    shape_keys: CollectionProperty(type=ShapeKeyItem)

    collection: EnumProperty(
        name="Collection",
        description="Collection containing objects to shape key",
        items=get_collections_callback,
    )

    frame: IntProperty(name="Frame", description="Frame to add keyframes", default=1)

    num_rows: IntProperty(
        name="Number of keys",
        description="Number of keys to show",
        default=DEFAULT_ROWS,
        min=1,
        max=MAX_SHAPE_KEYS,
    )

    all_value: FloatProperty(
        name="All Value",
        description="Value to set all keys to",
        default=0.6,
        min=0.0,
        max=1.0,
    )

# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------
class MULTIKEY_OT_SetAllValues(Operator):
    """Set all shape key values to a specific value"""

    bl_idname = "multikey.set_all_values"
    bl_label = "Set All Values"
    bl_description = "Set all enabled keys to the specified value"

    value: FloatProperty(default=0.0)

    def execute(self, context):
        props = context.scene.multikey_props

        for i in range(min(props.num_rows, len(props.shape_keys))):
            if props.shape_keys[i].enabled:
                props.shape_keys[i].value = self.value

        return {"FINISHED"}


class MULTIKEY_OT_SetAllTo(Operator):
    """Set all values to the 'all_value' property"""

    bl_idname = "multikey.set_all_to"
    bl_label = "Set All To"
    bl_description = "Set all enabled keys to the 'All Value' setting"

    def execute(self, context):
        props = context.scene.multikey_props

        for i in range(min(props.num_rows, len(props.shape_keys))):
            if props.shape_keys[i].enabled:
                props.shape_keys[i].value = props.all_value

        return {"FINISHED"}


class MULTIKEY_OT_GetCurrentFrame(Operator):
    """Get the current frame"""

    bl_idname = "multikey.get_current_frame"
    bl_label = "Get Current Frame"
    bl_description = "Set frame field to current frame"

    def execute(self, context):
        props = context.scene.multikey_props
        props.frame = context.scene.frame_current
        return {"FINISHED"}


class MULTIKEY_OT_AddKeyframes(Operator):
    """Add keyframes for all enabled shape keys"""

    bl_idname = "multikey.add_keyframes"
    bl_label = "Add Keyframes"
    bl_description = "Add keyframes at specified frame for all enabled shape keys"

    def execute(self, context):
        props = context.scene.multikey_props
        collection_name = get_collection_name_from_enum(props.collection)

        if not collection_name:
            self.report({"WARNING"}, "No collection selected")
            return {"CANCELLED"}

        # Apply all enabled shape keys
        for i in range(min(props.num_rows, len(props.shape_keys))):
            shape_key = props.shape_keys[i]
            if shape_key.enabled and shape_key.name:
                apply_shape_key_to_collection(
                    shape_key.name, shape_key.value, collection_name, props.frame, True
                )

        self.report({"INFO"}, f"Added keyframes at frame {props.frame}")
        return {"FINISHED"}


class MULTIKEY_OT_ClearNames(Operator):
    """Clear names of disabled shape keys"""

    bl_idname = "multikey.clear_names"
    bl_label = "Clear Unchecked Names"
    bl_description = "Clear names of disabled shape keys"

    def execute(self, context):
        props = context.scene.multikey_props

        for i in range(min(props.num_rows, len(props.shape_keys))):
            if not props.shape_keys[i].enabled:
                props.shape_keys[i].name = ""

        return {"FINISHED"}


class MULTIKEY_OT_ClearAllNames(Operator):
    """Clear all shape key names"""

    bl_idname = "multikey.clear_all_names"
    bl_label = "Clear All Names"
    bl_description = "Clear all shape key names"

    def execute(self, context):
        props = context.scene.multikey_props

        for i in range(min(props.num_rows, len(props.shape_keys))):
            props.shape_keys[i].name = ""

        return {"FINISHED"}


class MULTIKEY_OT_PreviewShapeKeys(Operator):
    """Preview shape key values without keyframing"""

    bl_idname = "multikey.preview_shape_keys"
    bl_label = "Preview"
    bl_description = "Apply current shape key values to objects for preview"

    def execute(self, context):
        props = context.scene.multikey_props
        collection_name = get_collection_name_from_enum(props.collection)

        if not collection_name:
            self.report({"WARNING"}, "No collection selected")
            return {"CANCELLED"}

        # Apply all enabled shape keys without keyframing
        for i in range(min(props.num_rows, len(props.shape_keys))):
            shape_key = props.shape_keys[i]
            if shape_key.enabled and shape_key.name:
                apply_shape_key_to_collection(
                    shape_key.name,
                    shape_key.value,
                    collection_name,
                    frame=None,
                    enabled=True,
                )

        return {"FINISHED"}


class MULTIKEY_OT_UpdateRows(Operator):
    """Update the number of visible rows"""

    bl_idname = "multikey.update_rows"
    bl_label = "Update Rows"
    bl_description = "Update the number of visible shape key rows"

    def execute(self, context):
        props = context.scene.multikey_props

        # Ensure we have enough shape key items
        while len(props.shape_keys) < props.num_rows:
            props.shape_keys.add()

        # Remove excess items if user reduced the number
        while len(props.shape_keys) > MAX_SHAPE_KEYS:
            props.shape_keys.remove(len(props.shape_keys) - 1)

        return {"FINISHED"}


# ------------------------------------------------------------------------
#    Panel
# ------------------------------------------------------------------------
class MULTIKEY_PT_Panel(Panel):
    """Main panel for MultiKey addon"""

    bl_label = "MultiKey"
    bl_idname = "MULTIKEY_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "SR + CCT"
    bl_context = "objectmode"

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        props = context.scene.multikey_props
        addon_prefs = context.preferences.addons["shading-rig-and-cel-character-tools"].preferences

        # Icon configuration
        icons = {
            "trash": "TRASH" if addon_prefs.show_icons else "NONE",
            "shape_key": "SHAPEKEY_DATA" if addon_prefs.show_icons else "NONE",
            "collection": "OUTLINER_OB_GROUP_INSTANCE" if addon_prefs.show_icons else "NONE",
            "keyframe": "KEY_HLT" if addon_prefs.show_icons else "NONE",
            "settings": "FILE_REFRESH",
        }

        # Clear buttons
        layout.operator("multikey.clear_names", icon=icons["trash"])
        layout.operator("multikey.clear_all_names", icon=icons["trash"])
        layout.separator()

        # Number of rows
        row = layout.row(align=True)
        row.prop(props, "num_rows")
        if len(props.shape_keys) < props.num_rows:
            row.operator("multikey.update_rows", icon=icons["settings"], text="")
        

        # Shape key rows - only show existing items
        for i in range(min(props.num_rows, len(props.shape_keys))):
            shape_key = props.shape_keys[i]

            row = layout.row(align=True)
            row.prop(
                shape_key, "name", icon=icons["shape_key"], text=""
            )
            row.prop(shape_key, "value", text="")
            row.prop(shape_key, "enabled", text="")

        layout.separator()

        # Collection selection
        layout.prop(props, "collection", icon=icons["collection"])

        layout.separator()

        # Custom set all
        row = layout.row(align=True)
        row.prop(props, "all_value", text="")
        row.operator("multikey.set_all_to", text="Set All To")

        layout.separator()

        # Keyframe controls
        row = layout.row(align=True)
        row.prop(props, "frame")
        row.operator("multikey.get_current_frame", text="", icon="TIME")

        layout.operator("multikey.add_keyframes", icon=icons["keyframe"])

        layout.separator()

# ------------------------------------------------------------------------
#    Handler Functions
# ------------------------------------------------------------------------
def update_frame_handler(dummy):
    """Update frame property when frame changes"""
    if bpy.context.scene and hasattr(bpy.context.scene, "multikey_props"):
        bpy.context.scene.multikey_props.frame = bpy.context.scene.frame_current
