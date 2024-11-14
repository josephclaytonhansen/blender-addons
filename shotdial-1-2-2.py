import bpy
import random
import mathutils
from bpy.app.handlers import persistent
from bpy.props import StringProperty, FloatVectorProperty, CollectionProperty

# Storage for shot data as a PropertyGroup
class ShotData(bpy.types.PropertyGroup):
    name: StringProperty(name="Name", default="Shot")
    color: FloatVectorProperty(name="Color", subtype='COLOR', min=0, max=1, default=(1.0, 1.0, 1.0))

# List to store all shots
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
        # Get the active camera or create a new one
        if context.scene.camera:
            cam_obj = context.scene.camera
        else:
            cam_data = bpy.data.cameras.new(name="Camera")
            cam_obj = bpy.data.objects.new(name="Camera", object_data=cam_data)
            context.scene.collection.objects.link(cam_obj)
            context.scene.camera = cam_obj

        # Generate a unique name and color
        shot_name = f"Shot {len(context.scene.shotdial_shots) + 1}"
        shot_color = (random.random(), random.random(), random.random())

        # Create a new shot entry
        new_shot = context.scene.shotdial_shots.add()
        new_shot.name = shot_name
        new_shot.color = shot_color

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

        for shot in context.scene.shotdial_shots:
            box = layout.box()
            row = box.row()
            row.prop(shot, "name", text="Name")
            row = box.row()
            row.prop(shot, "color", text="Color")

            row = box.row()
            op = row.operator("shotdial.set_active_camera", text="Set Active")
            op.shot_name = shot.name

# Operator to set active camera by shot
class SHOTDIAL_OT_SetActiveCamera(bpy.types.Operator):
    """Set the active camera for the selected shot"""
    bl_idname = "shotdial.set_active_camera"
    bl_label = "Set Active Camera"
    
    shot_name: StringProperty()

    def execute(self, context):
        shot = next((s for s in context.scene.shotdial_shots if s.name == self.shot_name), None)
        if shot:
            context.scene.camera = bpy.data.objects.get(shot.name)
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
        cameras = [shot.name for shot in context.scene.shotdial_shots]

        if cameras:
            camera_index = (camera_index + 1) % len(cameras)
            context.scene.camera = bpy.data.objects.get(cameras[camera_index])
            self.report({'INFO'}, f"Switched to {cameras[camera_index]}")
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
        cameras = [shot.name for shot in context.scene.shotdial_shots]

        if cameras:
            camera_index = (camera_index - 1) % len(cameras)
            context.scene.camera = bpy.data.objects.get(cameras[camera_index])
            self.report({'INFO'}, f"Switched to {cameras[camera_index]}")
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
        
        kmi = km.keymap_items.new(OBJECT_OT_Spin.bl_idname, type='W', value='PRESS', ctrl=True)
        addon_keymaps.append((km, kmi))
        
        kmi = km.keymap_items.new(OBJECT_OT_DeSpin.bl_idname, type='W', value='PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))
        
        kmi = km.keymap_items.new(SHOTDIAL_OT_NewShot.bl_idname, type='M', value='PRESS', alt=True)
        addon_keymaps.append((km, kmi))

def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

# Registration
classes = [
    ShotData,
    SHOTDIAL_OT_NewShot,
    SHOTDIAL_PT_ShotPanel,
    SHOTDIAL_OT_SetActiveCamera,
    OBJECT_OT_Spin,
    OBJECT_OT_DeSpin
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.shotdial_shots = CollectionProperty(type=ShotData)
    register_keymaps()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.shotdial_shots
    unregister_keymaps()

if __name__ == "__main__":
    register()
