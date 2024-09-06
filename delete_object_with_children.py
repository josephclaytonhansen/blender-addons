bl_info = {
    "name": "Delete Object with Children",
    "author": "Joseph Hansen",
    "version": (0, 0, 3),
    "blender": (3, 6, 0),
    "category": "Object",
}

import bpy


class OBJECT_OT_delete_with_children(bpy.types.Operator):
    bl_idname = "object.delete_with_children"
    bl_label = "Delete Object with Children"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        for obj in selected_objects:
            self.delete_object_and_children(obj)

        return {'FINISHED'}

    def delete_object_and_children(self, obj):
        for child in obj.children:
            self.delete_object_and_children(child)
        bpy.data.objects.remove(obj, do_unlink=True)
        
def register():
    bpy.utils.register_class(OBJECT_OT_delete_with_children)
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.default
    km = kc.keymaps['3D View']
    kmi = km.keymap_items.new(OBJECT_OT_delete_with_children.bl_idname, 'X', 'PRESS')
    kmi.active = True

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_delete_with_children)
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.default
    km = kc.keymaps['3D View']

    for kmi in km.keymap_items:
        if kmi.idname == OBJECT_OT_delete_with_children.bl_idname:
            km.keymap_items.remove(kmi)
            break

if __name__ == "__main__":
    register()
