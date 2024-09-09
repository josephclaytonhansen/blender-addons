bl_info = {
    "name": "Searchable Vertex Group Panel",
    "author": "Joseph Hansen",
    "version": (0,0,1),
    "blender": (4,1,0),
    "category":"Object",
}

import bpy
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty

class SimpleOperator(Operator):
    bl_idname = "object.simple_operator"
    bl_label = "Simple Object Operator"

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        return {'FINISHED'}

class SimplePanel(Panel):
    bl_label = "Vertex Group Search"
    bl_idname = "OBJECT_PT_simple_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool

        layout.prop(mytool, "my_string", text="")

        for i, group in enumerate(bpy.context.object.vertex_groups):
            if mytool.my_string.lower() in group.name.lower():
                op = layout.operator("object.vertex_group_set_active", text=group.name)
                op.group = group.name

class MySettings(PropertyGroup):
    my_string: StringProperty(
        name="",
        description="Search Vertex Groups",
        default="",
        maxlen=1024,
    )

def register():
    bpy.utils.register_class(SimpleOperator)
    bpy.utils.register_class(SimplePanel)
    bpy.utils.register_class(MySettings)

    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MySettings)

def unregister():
    bpy.utils.unregister_class(SimpleOperator)
    bpy.utils.unregister_class(SimplePanel)
    bpy.utils.unregister_class(MySettings)

    del bpy.types.Scene.my_tool

if __name__ == "__main__":
    register()
