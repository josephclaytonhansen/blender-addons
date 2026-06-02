import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
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


def get_jawbone_pose_bone(props):
    """Return the selected jaw pose bone, if the armature and bone are valid."""
    armature = getattr(props, "jawbone_armature", None)
    bone_name = getattr(props, "jawbone_bone_name", "").strip()

    if not armature or armature.type != "ARMATURE" or not bone_name:
        return None

    pose = getattr(armature, "pose", None)
    if not pose:
        return None

    return pose.bones.get(bone_name)


def capture_jawbone_rest_pose(props):
    """Store the current jawbone pose as the rest pose reference."""
    pose_bone = get_jawbone_pose_bone(props)
    if not pose_bone:
        return False

    props.jawbone_rest_location = pose_bone.location.copy()
    props.jawbone_rest_rotation = pose_bone.rotation_euler.copy()
    return True


def apply_jawbone_pose_from_shape_keys(props):
    """Blend the selected jawbone toward the stored correspondences."""
    if not getattr(props, "update_jawbone", False):
        return

    pose_bone = get_jawbone_pose_bone(props)
    if not pose_bone:
        return

    rest_location = props.jawbone_rest_location
    rest_rotation = props.jawbone_rest_rotation

    location_offset = [0.0, 0.0, 0.0]
    rotation_offset = [0.0, 0.0, 0.0]

    for shape_key in props.shape_keys:
        if not shape_key.enabled or not shape_key.name:
            continue

        influence = shape_key.value
        for axis in range(3):
            location_offset[axis] += (
                shape_key.jawbone_location[axis] - rest_location[axis]
            ) * influence
            rotation_offset[axis] += (
                shape_key.jawbone_rotation[axis] - rest_rotation[axis]
            ) * influence

    pose_bone.location = [
        rest_location[0] + location_offset[0],
        rest_location[1] + location_offset[1],
        rest_location[2] + location_offset[2],
    ]
    pose_bone.rotation_euler = [
        rest_rotation[0] + rotation_offset[0],
        rest_rotation[1] + rotation_offset[1],
        rest_rotation[2] + rotation_offset[2],
    ]


def update_shape_key_live(self, context):
    """Update callback for live preview of shape keys"""
    props = context.scene.multikey_props
    collection_name = get_collection_name_from_enum(props.collection)

    # Find which shape key this belongs to
    for i, shape_key in enumerate(props.shape_keys):
        if shape_key == self:
            if collection_name and shape_key.enabled and shape_key.name:
                apply_shape_key_to_collection(
                    shape_key.name,
                    shape_key.value,
                    collection_name,
                    frame=None,
                    enabled=True,
                )
            break

    apply_jawbone_pose_from_shape_keys(props)


def update_jawbone_settings(self, context):
    """Refresh the stored jawbone rest pose and reapply the mapping."""
    props = context.scene.multikey_props

    if not props.update_jawbone:
        return

    if capture_jawbone_rest_pose(props):
        apply_jawbone_pose_from_shape_keys(props)


def ensure_shape_key_rows(props, target_count=None):
    """Make sure the backing collection has enough rows for the UI."""
    desired_count = (
        props.num_rows if target_count is None else min(target_count, MAX_SHAPE_KEYS)
    )

    while len(props.shape_keys) < desired_count:
        props.shape_keys.add()

    while len(props.shape_keys) > MAX_SHAPE_KEYS:
        props.shape_keys.remove(len(props.shape_keys) - 1)


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

    jawbone_location: FloatVectorProperty(
        name="Jawbone Location",
        description="Jawbone location saved for this shape key",
        subtype="TRANSLATION",
        size=3,
        default=(0.0, 0.0, 0.0),
    )

    jawbone_rotation: FloatVectorProperty(
        name="Jawbone Rotation",
        description="Jawbone rotation saved for this shape key",
        subtype="EULER",
        size=3,
        default=(0.0, 0.0, 0.0),
    )


class MultiKeyProperties(PropertyGroup):
    """Main properties for the addon"""

    shape_keys: CollectionProperty(type=ShapeKeyItem)

    jawbone_armature: PointerProperty(
        name="Jawbone Armature",
        description="Armature containing the jaw bone",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "ARMATURE",
        update=update_jawbone_settings,
    )

    jawbone_bone_name: StringProperty(
        name="Jawbone Bone",
        description="Pose bone controlled by the stored shape key correspondences",
        default="",
        update=update_jawbone_settings,
    )

    update_jawbone: BoolProperty(
        name="Update Jawbone",
        description="Lerp the jawbone as shape key values change",
        default=False,
        update=update_jawbone_settings,
    )

    jawbone_rest_location: FloatVectorProperty(
        name="Jawbone Rest Location",
        size=3,
        default=(0.0, 0.0, 0.0),
    )

    jawbone_rest_rotation: FloatVectorProperty(
        name="Jawbone Rest Rotation",
        subtype="EULER",
        size=3,
        default=(0.0, 0.0, 0.0),
    )

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

        if props.update_jawbone:
            apply_jawbone_pose_from_shape_keys(props)
            pose_bone = get_jawbone_pose_bone(props)
            if pose_bone:
                pose_bone.keyframe_insert("location", frame=props.frame)
                pose_bone.keyframe_insert("rotation_euler", frame=props.frame)

        self.report({"INFO"}, f"Added keyframes at frame {props.frame}")
        return {"FINISHED"}


class MULTIKEY_OT_SetJawboneForShapeKey(Operator):
    """Save the current jawbone pose for a shape key row"""

    bl_idname = "multikey.set_jawbone_for_shape_key"
    bl_label = "Set Jawbone For Selected Shapekey"
    bl_description = "Save the current jawbone pose for the selected shape key"

    shape_key_index: IntProperty(default=0)

    def execute(self, context):
        props = context.scene.multikey_props

        if self.shape_key_index < 0 or self.shape_key_index >= len(props.shape_keys):
            self.report({"WARNING"}, "Invalid shape key row")
            return {"CANCELLED"}

        pose_bone = get_jawbone_pose_bone(props)
        if not pose_bone:
            self.report({"WARNING"}, "Select a jawbone armature and bone first")
            return {"CANCELLED"}

        shape_key = props.shape_keys[self.shape_key_index]
        shape_key.jawbone_location = pose_bone.location.copy()
        shape_key.jawbone_rotation = pose_bone.rotation_euler.copy()

        return {"FINISHED"}


class MULTIKEY_OT_AddCorrespondence(Operator):
    """Add a new jawbone correspondence row"""

    bl_idname = "multikey.add_correspondence"
    bl_label = "Add Correspondence"
    bl_description = "Add a new shape key to jawbone correspondence row"

    def execute(self, context):
        props = context.scene.multikey_props

        if len(props.shape_keys) >= MAX_SHAPE_KEYS:
            self.report({"WARNING"}, "Maximum number of correspondences reached")
            return {"CANCELLED"}

        props.shape_keys.add()
        props.num_rows = max(props.num_rows, len(props.shape_keys))

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
        ensure_shape_key_rows(props)

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
        addon_prefs = context.preferences.addons[
            "shading-rig-and-cel-character-tools"
        ].preferences
        if not addon_prefs.show_multikey:
            return

        ensure_shape_key_rows(props)

        # Icon configuration
        icons = {
            "trash": "TRASH" if addon_prefs.show_icons else "NONE",
            "shape_key": "SHAPEKEY_DATA" if addon_prefs.show_icons else "NONE",
            "collection": (
                "OUTLINER_OB_GROUP_INSTANCE" if addon_prefs.show_icons else "NONE"
            ),
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
            row.prop(shape_key, "name", icon=icons["shape_key"], text="")
            row.prop(shape_key, "value", text="")
            row.prop(shape_key, "enabled", text="")

        layout.separator()

        # Collection selection
        layout.prop(props, "collection", icon=icons["collection"])

        layout.separator()

        jawbone_box = layout.box()
        jawbone_box.label(text="Jawbone")
        jawbone_box.prop(props, "jawbone_armature")
        if props.jawbone_armature:
            jawbone_box.prop_search(
                props, "jawbone_bone_name", props.jawbone_armature.data, "bones"
            )
        else:
            jawbone_box.prop(props, "jawbone_bone_name")
        jawbone_box.prop(props, "update_jawbone")

        jawbone_box.separator()
        jawbone_box.label(text="Correspondences")
        jawbone_box.operator(
            "multikey.add_correspondence", text="Add Correspondence", icon="ADD"
        )
        for i in range(min(props.num_rows, len(props.shape_keys))):
            shape_key = props.shape_keys[i]

            row = jawbone_box.row(align=True)
            row.prop(shape_key, "name", text="Shape Key")

            row = jawbone_box.row(align=True)
            row.prop(shape_key, "jawbone_location", text="Loc")
            row.prop(shape_key, "jawbone_rotation", text="Rot")

            row = jawbone_box.row(align=True)
            op = row.operator(
                "multikey.set_jawbone_for_shape_key",
                text="Set Jawbone",
                icon="BONE_DATA",
            )
            op.shape_key_index = i

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


# ------------------------------------------------------------------------
#    Handler Functions
# ------------------------------------------------------------------------
def update_frame_handler(dummy):
    """Update frame property when frame changes"""
    if bpy.context.scene and hasattr(bpy.context.scene, "multikey_props"):
        bpy.context.scene.multikey_props.frame = bpy.context.scene.frame_current
