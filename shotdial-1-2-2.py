bl_info = {
    "name": "ShotDial",
    "author": "Joseph Hansen",
    "version": (1, 3, 1),
    "blender" : (3, 60, 13),
    "location": "",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D View"
}

import bpy
import random
import mathutils
from bpy.app.handlers import persistent

# Storage for shot data
class ShotData:
    def __init__(self, name, camera, color):
        self.name = name
        self.camera = camera
        self.color = color

# List to store all shots
shots = []
camera_index = 0
addon_keymaps = []

# Utility function to check if a face is visible from the camera
def is_face_visible(camera, obj, face):
    face_center = obj.matrix_world @ face.center
    direction = (face_center - camera.location).normalized()
    result, location, normal, index = obj.ray_cast(camera.location, direction)
    return result and index == face.index

# Operator to create a new shot
class SHOTDIAL_OT_NewShot(bpy.types.Operator):
    """Add a new shot and color visible faces"""
    bl_idname = "shotdial.new_shot"
    bl_label = "New Shot"

    def execute(self, context):
        global shots
        shot_name = f"Shot {len(shots) + 1}"
        shot_color = (random.random(), random.random(), random.random())

        # Create and link a new camera for the shot
        cam_data = bpy.data.cameras.new(name=f"{shot_name}_Camera")
        cam_obj = bpy.data.objects.new(name=f"{shot_name}_Camera", object_data=cam_data)
        context.scene.collection.objects.link(cam_obj)
        context.scene.camera = cam_obj

        new_shot = ShotData(name=shot_name, camera=cam_obj, color=shot_color)
        shots.append(new_shot)

        # Color visible faces only
        for obj in context.scene.objects:
            if obj.type == 'MESH':
                if "shot_color" not in obj.data.attributes:
                    obj.data.attributes.new(name="shot_color", type='FLOAT_COLOR', domain='FACE')
                color_layer = obj.data.attributes["shot_color"].data
                for poly in obj.data.polygons:
                    if is_face_visible(cam_obj, obj, poly):
                        color_layer[poly.index].color = shot_color
                    else:
                        color_layer[poly.index].color = (0, 0, 0, 0)  # Transparent for non-visible faces

        context.area.tag_redraw()
        self.report({'INFO'}, f"Shot '{shot_name}' created with visible face coloring")
        return {'FINISHED'}

# Panel to list shots and control them
class SHOTDIAL_PT_ShotPanel(bpy.types.Panel):
    """Shot control panel"""
    bl_label = "ShotDial Panel"
    bl_idname = "SHOTDIAL_PT_shot_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'ShotDial'

    def draw(self, context):
        layout = self.layout
        layout.operator("shotdial.new_shot", text="New Shot")

        for shot in shots:
            box = layout.box()
            
            # Shot name and renaming
            row = box.row()
            row.prop(shot, "name", text="Name")

            # Color picker to change shot color
            row = box.row()
            row.prop(shot, "color", text="Color")

            # Set Active Camera button
            row = box.row()
            row.operator("shotdial.set_active_camera", text="Set Active").shot_name = shot.name

# Operator to set active camera by shot
class SHOTDIAL_OT_SetActiveCamera(bpy.types.Operator):
    """Set the active camera for the selected shot"""
    bl_idname = "shotdial.set_active_camera"
    bl_label = "Set Active Camera"
    
    shot_name: bpy.props.StringProperty()

    def execute(self, context):
        shot = next((s for s in shots if s.name == self.shot_name), None)
        if shot:
            context.scene.camera = shot.camera
            self.report({'INFO'}, f"Set '{shot.name}' as active camera")
        else:
            self.report({'ERROR'}, "Shot not found")
        return {'FINISHED'}

# Operator to cycle through cameras (forward)
class OBJECT_OT_Spin(bpy.types.Operator):
    """Move between camera views (forwards)"""
    bl_idname = "shotdial.spin"
    bl_label = "Move between camera views (forwards)"
    
    def execute(self, context):
        global camera_index
        cameras = [shot.camera for shot in shots]

        if cameras:
            camera_index = (camera_index + 1) % len(cameras)
            context.scene.camera = cameras[camera_index]
            self.report({'INFO'}, f"Switched to {shots[camera_index].name}")
        else:
            self.report({'ERROR'}, "No cameras found")
        return {'FINISHED'}

# Operator to cycle through cameras (backward)
class OBJECT_OT_DeSpin(bpy.types.Operator):
    """Move between camera views (backwards)"""
    bl_idname = "shotdial.despin"
    bl_label = "Move between camera views (backwards)"
    
    def execute(self, context):
        global camera_index
        cameras = [shot.camera for shot in shots]

        if cameras:
            camera_index = (camera_index - 1) % len(cameras)
            context.scene.camera = cameras[camera_index]
            self.report({'INFO'}, f"Switched to {shots[camera_index].name}")
        else:
            self.report({'ERROR'}, "No cameras found")
        return {'FINISHED'}

# Keymap setup to bind shortcuts
def register_keymaps():
    global addon_keymaps
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        
        # Forward camera switch (Ctrl + W)
        kmi = km.keymap_items.new(OBJECT_OT_Spin.bl_idname, type='W', value='PRESS', ctrl=True)
        addon_keymaps.append((km, kmi))
        
        # Backward camera switch (Ctrl + Shift + W)
        kmi = km.keymap_items.new(OBJECT_OT_DeSpin.bl_idname, type='W', value='PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))
        
        # Add marker and bind camera (Alt + M)
        kmi = km.keymap_items.new(SHOTDIAL_OT_NewShot.bl_idname, type='M', value='PRESS', alt=True)
        addon_keymaps.append((km, kmi))

def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

# Registration
classes = [
    SHOTDIAL_OT_NewShot,
    SHOTDIAL_PT_ShotPanel,
    SHOTDIAL_OT_SetActiveCamera,
    OBJECT_OT_Spin,
    OBJECT_OT_DeSpin
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_keymaps()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    unregister_keymaps()

if __name__ == "__main__":
    register()
