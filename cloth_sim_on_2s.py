bl_info = {
    "name": "Stepped Cloth Sim Interpolation",
    "author": "Joseph Hansen",
    "version": (1, 1),
    "blender": (3, 6, 5),
    "location": "Properties > Physics > Cloth > Bake",
    "description": "Convert a cloth simulation to stepped interpolation on 2s",
    "category": "Physics",
}

import bpy
import os

class OBJECT_OT_interpolate_bake(bpy.types.Operator):
    """Convert cloth simulations to stepped interpolation on 2s"""
    bl_idname = "object.interpolate_bake"
    bl_label = "Interpolate All Bakes on 2s"

    def execute(self, context):
        blend_file_path = bpy.data.filepath
        if not blend_file_path:
            self.report({'ERROR'}, "Please save your blend file before running this script.")
            return {'CANCELLED'}
        
        directory = os.path.dirname(blend_file_path)
        directory = os.path.join(directory, "blendcache_cloth")
        print(directory)

        if not os.path.exists(directory):
            self.report({'ERROR'}, f"Directory '{directory}' not found.")
            return {'CANCELLED'}
        
        suffixes = []
        
        for filename in os.listdir(directory):
            if filename.endswith('.bphys'):
                suffixes.append(filename.split('_')[2].split(".")[0])
                
        print(suffixes)
        
        for cache in suffixes:
            for filename in os.listdir(directory):
                if filename.endswith('.bphys') and filename.split('_')[2].split(".")[0] == cache:
                    file_number = int(filename.split('_')[1])
                    if file_number % 2 == 0:
                        print(file_number)
                        prev_file_number = file_number - 1
                        prev_filename = f"{filename.split('_')[0]}_{prev_file_number:06d}_{cache}.bphys"
                        with open(os.path.join(directory, prev_filename), 'rb') as prev_file:
                            content = prev_file.read()
                        with open(os.path.join(directory, filename), 'wb') as current_file:
                            current_file.write(content)
                            
        return {'FINISHED'}


def draw_func(self, context):
    layout = self.layout
    layout.operator("object.interpolate_bake", text="Interpolate All Bakes On 2s")


classes = (
    OBJECT_OT_interpolate_bake,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.PHYSICS_PT_cloth_cache.append(draw_func)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.PHYSICS_PT_cloth_cache.remove(draw_func)


if __name__ == "__main__":
    register()