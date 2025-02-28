bl_info = {
    "name": "Select by UV Map",
    "blender": (3, 60, 13),
    "author": "Joseph Hansen"
}

import bpy

class OBJECT_OT_select_by_uv_map(bpy.types.Operator):
    bl_idname = "object.select_by_uv_map"
    bl_label = "Select by UV Map"
    bl_options = {'REGISTER', 'UNDO'}

    uv_map_name: bpy.props.StringProperty(name="UV Map Name")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        uv_map_name = self.uv_map_name
        selected_objects = []

        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                for uv_map in obj.data.uv_layers:
                    if uv_map.name == uv_map_name:
                        selected_objects.append(obj)
                        break

        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected_objects:
            obj.select_set(True)

        if selected_objects:
            context.view_layer.objects.active = selected_objects[0]

        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_select_by_uv_map.bl_idname)

def register():
    bpy.utils.register_class(OBJECT_OT_select_by_uv_map)
    bpy.types.VIEW3D_MT_select_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_select_by_uv_map)
    bpy.types.VIEW3D_MT_select_object.remove(menu_func)

if __name__ == "__main__":
    register()
