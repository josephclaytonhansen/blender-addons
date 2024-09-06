bl_info = {
    "name": "Multikey",
    "description": "Change shape keys on multiple objects and keyframe them",
    "author": "Joseph Hansen",
    "version": (1, 3, 2),
    "blender": (3, 6, 0),
    "location": "3D View > Animation",
    "category": "Animation",
}

import bpy
from bpy.props import (
    BoolProperty,
    FloatProperty,
    StringProperty,
    IntProperty,
    EnumProperty,
    PointerProperty,
    CollectionProperty,
)
from bpy.types import Panel, Operator, PropertyGroup

# ------------------------------------------------------------------------
# Scene Properties
# ------------------------------------------------------------------------

def get_collection_items(scene, context):
    return [(col.name, col.name, "") for col in bpy.data.collections]

class KeyData(PropertyGroup):
    enabled: BoolProperty(
        name="Enabled",
        description="Enable/disable this key",
        default=True,
    )
    value: FloatProperty(
        name="Value",
        description="Value (0.0 to 1.0) of the shape key",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    name: StringProperty(
        name="Name",
        description="Name of the shape key",
        default="",
        maxlen=64,
    )

class MultiKeyProperties(PropertyGroup):
    key_count: IntProperty(
        name="Number of Keys",
        description="Number of keys to show",
        default=6,
        min=1,
        max=10,
    )
    
    key_data: CollectionProperty(type=KeyData)

    collection_enum: EnumProperty(
        name="Collection",
        description="Collection containing objects to shape key",
        items=get_collection_items,
    )
    
    frame: IntProperty(name="Frame", description="Frame to add keyframes")

    def update_key_count(self, context):
        self.key_data.clear()
        for i in range(self.key_count):
            self.key_data.add()

# ------------------------------------------------------------------------
# Operators
# ------------------------------------------------------------------------

class MultiKeyOperatorBase(Operator):
    def get_properties(self, context):
        return context.scene.multi_key_props

    def get_objects(self):
        return bpy.data.collections[self.get_properties().collection_enum].all_objects

    def update_shape_keys(self, key, value, collection, frame, enabled):
        if not enabled:
            return
        
        for obj in self.get_objects():
            if hasattr(obj.data, "shape_keys"):
                shape_keys = obj.data.shape_keys.key_blocks
                for shape in shape_keys:
                    if shape.name == key:
                        shape.value = value
                        shape.keyframe_insert(data_path="value", frame=frame)

class WM_OT_ResetAll(MultiKeyOperatorBase):
    bl_label = "Set all to 1"
    bl_idname = "wm.mk_reset_all"
    def execute(self, context):
        props = self.get_properties()
        for i in range(props.key_count):
            key_data = props.key_data[i]
            key_data.value = 1.0
        return {'FINISHED'}

class WM_OT_CurrentFrame(MultiKeyOperatorBase):
    bl_label = "Get current frame"
    bl_idname = "wm.mk_current_frame"
    def execute(self, context):
        self.get_properties().frame = context.scene.frame_current
        return {'FINISHED'}

class WM_OT_AddKey(MultiKeyOperatorBase):
    bl_label = "Add keyframes at frame"
    bl_idname = "wm.mk_add_key"
    def execute(self, context):
        props = self.get_properties()
        for i in range(props.key_count):
            key_data = props.key_data[i]
            if key_data.enabled:
                self.update_shape_keys(key_data.name, key_data.value, props.collection_enum, props.frame, key_data.enabled)
        return {'FINISHED'}

class WM_OT_SetAll(MultiKeyOperatorBase):
    bl_label = "Set all to:"
    bl_idname = "wm.mk_set_all"
    def execute(self, context):
        props = self.get_properties()
        if props.key_data:
            value = props.key_data[0].value
            for i in range(props.key_count):
                key_data = props.key_data[i]
                key_data.value = value
        return {'FINISHED'}

class WM_OT_ToggleIcons(Operator):
    bl_label = "Toggle icons"
    bl_idname = "wm.mk_toggle_icons"
    def execute(self, context):
        context.scene.show_icons = not context.scene.get("show_icons", True)
        return {'FINISHED'}

# ------------------------------------------------------------------------
# Panels
# ------------------------------------------------------------------------

class OBJECT_PT_MultiKeyPanel(Panel):
    bl_label = "MultiKey"
    bl_idname = "OBJECT_PT_multi_key_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Multikey"

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        props = context.scene.multi_key_props

        # Add buttons for managing keys
        layout.operator("wm.mk_reset_all")
        layout.operator("wm.mk_current_frame")
        layout.operator("wm.mk_set_all")

        # Add keys dynamically
        for i in range(props.key_count):
            key_data = props.key_data[i]
            sub = layout.box()
            sub.prop(key_data, "name", text=f"Key {chr(65 + i)}")
            sub.prop(key_data, "value")
            sub.prop(key_data, "enabled")

        # Enum and Frame properties
        layout.prop(props, "collection_enum")
        layout.prop(props, "frame")

        layout.operator("wm.mk_add_key")
        layout.operator("wm.mk_toggle_icons")

# ------------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------------

def register():
    from bpy.utils import register_class
    register_class(KeyData)
    register_class(MultiKeyProperties)
    for cls in [WM_OT_ResetAll, WM_OT_CurrentFrame, WM_OT_AddKey, WM_OT_SetAll, WM_OT_ToggleIcons, OBJECT_PT_MultiKeyPanel]:
        register_class(cls)

    bpy.types.Scene.multi_key_props = PointerProperty(type=MultiKeyProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed([WM_OT_ResetAll, WM_OT_CurrentFrame, WM_OT_AddKey, WM_OT_SetAll, WM_OT_ToggleIcons, OBJECT_PT_MultiKeyPanel]):
        unregister_class(cls)
    del bpy.types.Scene.multi_key_props

if __name__ == "__main__":
    register()
