bl_info = {
    "name": "Multikey",
    "description": "Change shape keys on multiple objects and keyframe them",
    "author": "Joseph Hansen",
    "version": (1, 3, 1),
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
)
from bpy.types import Panel, Operator, PropertyGroup

# ------------------------------------------------------------------------
# Scene Properties
# ------------------------------------------------------------------------

def get_collection_items(scene, context):
    return [(col.name, col.name, "") for col in bpy.data.collections]

class MultiKeyProperties(PropertyGroup):
    key_count: IntProperty(
        name="Number of Keys",
        description="Number of keys to show",
        default=6,
        min=1,
        max=10,
    )
    
    key_data: bpy.props.CollectionProperty(type=PropertyGroup)

    my_enum: EnumProperty(
        name="Collection",
        description="Collection containing objects to shape key",
        items=get_collection_items,
    )
    
    my_int: IntProperty(name="Frame", description="Frame to add keyframes")

    def update_key_count(self, context):
        self.key_data.clear()
        for i in range(self.key_count):
            self.key_data.add()

# Define Key Properties
def create_key_properties():
    properties = {}
    for i in range(10):
        properties[f"key_{i}_enabled"] = BoolProperty(
            name=f"Enable Key {chr(65 + i)}",
            description=f"Enable/disable this key {chr(65 + i)}",
            default=True,
        )
        properties[f"key_{i}_value"] = FloatProperty(
            name=f"Value {chr(65 + i)}",
            description=f"Value (0.0 to 1.0) of the shape key {chr(65 + i)}",
            default=1.0,
            min=0.0,
            max=1.0,
        )
        properties[f"key_{i}_name"] = StringProperty(
            name=f"Key {chr(65 + i)}",
            description=f"Name of the shape key {chr(65 + i)}",
            default="",
            maxlen=64,
        )
    return properties

MultiKeyProperties.key_data.add = create_key_properties()

# ------------------------------------------------------------------------
# Operators
# ------------------------------------------------------------------------

class MultiKeyOperatorBase(Operator):
    def get_properties(self, context):
        return context.scene.multi_key_props

    def get_objects(self):
        return bpy.data.collections[self.get_properties().my_enum].all_objects

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
        for i in range(10):
            getattr(props, f"key_{i}_value") = 1.0
        return {'FINISHED'}

class WM_OT_CurrentFrame(MultiKeyOperatorBase):
    bl_label = "Get current frame"
    bl_idname = "wm.mk_current_frame"
    def execute(self, context):
        self.get_properties().my_int = context.scene.frame_current
        return {'FINISHED'}

class WM_OT_AddKey(MultiKeyOperatorBase):
    bl_label = "Add keyframes at frame"
    bl_idname = "wm.mk_add_key"
    def execute(self, context):
        props = self.get_properties()
        for i in range(10):
            if getattr(props, f"key_{i}_enabled"):
                key_name = getattr(props, f"key_{i}_name")
                key_value = getattr(props, f"key_{i}_value")
                self.update_shape_keys(key_name, key_value, props.my_enum, props.my_int, getattr(props, f"key_{i}_enabled"))
        return {'FINISHED'}

class WM_OT_SetAll(MultiKeyOperatorBase):
    bl_label = "Set all to:"
    bl_idname = "wm.mk_set_all"
    def execute(self, context):
        props = self.get_properties()
        for i in range(10):
            getattr(props, f"key_{i}_value") = props.key_data[0].value
        return {'FINISHED'}

class WM_OT_Light(Operator):
    bl_label = "Toggle icons"
    bl_idname = "wm.mk_toggle_icons"
    def execute(self, context):
        context.scene.show_icons = not context.scene.show_icons
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
            sub = layout.box()
            sub.prop(props.key_data[i], "key_{i}_name", text=f"Key {chr(65 + i)}")
            sub.prop(props.key_data[i], "key_{i}_value")
            sub.prop(props.key_data[i], "key_{i}_enabled")

        # Enum and Frame properties
        layout.prop(props, "my_enum")
        layout.prop(props, "my_int")

        layout.operator("wm.mk_add_key")
        layout.operator("wm.mk_toggle_icons")

# ------------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------------

def register():
    from bpy.utils import register_class
    register_class(MultiKeyProperties)
    for cls in [WM_OT_ResetAll, WM_OT_CurrentFrame, WM_OT_AddKey, WM_OT_SetAll, WM_OT_Light, OBJECT_PT_MultiKeyPanel]:
        register_class(cls)

    bpy.types.Scene.multi_key_props = PointerProperty(type=MultiKeyProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed([WM_OT_ResetAll, WM_OT_CurrentFrame, WM_OT_AddKey, WM_OT_SetAll, WM_OT_Light, OBJECT_PT_MultiKeyPanel]):
        unregister_class(cls)
    del bpy.types.Scene.multi_key_props

if __name__ == "__main__":
    register()
