bl_info = {
    "name": "ShotDial",
    "author": "Joseph Hansen",
    "version": (1, 3, 20),
    "blender": (3, 60, 13),
    "location": "",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D View"
}

import bpy
import random
from bpy.props import StringProperty, FloatVectorProperty, CollectionProperty, BoolProperty
from mathutils import Vector
import math

# Storage for shot data as a PropertyGroup
class ShotData(bpy.types.PropertyGroup):
    name: StringProperty(name="Name", default="Shot")
    color: FloatVectorProperty(name="Color", subtype='COLOR', min=0, max=1, default=(1.0, 1.0, 1.0))
    camera: bpy.props.PointerProperty(type=bpy.types.Object)  # Store the camera object directly

# List to store all shots
camera_index = 0
addon_keymaps = []

# Function to construct the camera frustum as a bounding box
def construct_frustum_bb(cam, scn):
    cam_data = cam.data
    box = [[0, 0, 0] for _ in range(8)]

    aspx = scn.render.resolution_x * scn.render.pixel_aspect_x
    aspy = scn.render.resolution_y * scn.render.pixel_aspect_y

    ratiox = min(aspx / aspy, 1.0)
    ratioy = min(aspy / aspx, 1.0)

    angleofview = 2.0 * math.atan(cam_data.sensor_width / (2.0 * cam_data.lens))
    oppositeclipsta = math.tan(angleofview / 2.0) * cam_data.clip_start
    oppositeclipend = math.tan(angleofview / 2.0) * cam_data.clip_end

    box[2][0] = box[1][0] = -oppositeclipsta * ratiox
    box[0][0] = box[3][0] = -oppositeclipend * ratiox
    box[5][0] = box[6][0] = +oppositeclipsta * ratiox
    box[4][0] = box[7][0] = +oppositeclipend * ratiox
    box[1][1] = box[5][1] = -oppositeclipsta * ratioy
    box[0][1] = box[4][1] = -oppositeclipend * ratioy
    box[2][1] = box[6][1] = +oppositeclipsta * ratioy
    box[3][1] = box[7][1] = +oppositeclipend * ratioy
    box[0][2] = box[3][2] = box[4][2] = box[7][2] = -cam_data.clip_end
    box[1][2] = box[2][2] = box[5][2] = box[6][2] = -cam_data.clip_start

    return [cam.matrix_world @ Vector(i) for i in box]

# Function to construct the frustum planes
def construct_frustum_planes(cf):
    def construct_plane(p1, p2, p3):
        v1 = p3 - p1
        v2 = p2 - p1
        cp = v1.cross(v2).normalized()
        d = cp.dot(p3)
        return cp.x, cp.y, cp.z, -d

    return [
        construct_plane(cf[0], cf[2], cf[3]),
        construct_plane(cf[3], cf[2], cf[7]),
        construct_plane(cf[7], cf[6], cf[4]),
        construct_plane(cf[5], cf[0], cf[4]),
        construct_plane(cf[4], cf[0], cf[7]),
        construct_plane(cf[2], cf[1], cf[5])
    ]

# Function to check if a point is inside all frustum planes
def point_in_frustum(point, planes):
    for plane in planes:
        if plane[0] * point.x + plane[1] * point.y + plane[2] * point.z + plane[3] < 0:
            return False
    return True

# Update the SHOTDIAL_OT_NewShot operator
class SHOTDIAL_OT_NewShot(bpy.types.Operator):
    """Add a new shot and color visible faces"""
    bl_idname = "shotdial.new_shot"
    bl_label = "New Shot"

    def execute(self, context):
        cam_obj = context.scene.camera
        if not cam_obj:
            self.report({'ERROR'}, "No active camera in the scene")
            return {'CANCELLED'}

        # Get camera frustum
        scene = context.scene
        frustum_corners = construct_frustum_bb(cam_obj, scene)
        frustum_planes = construct_frustum_planes(frustum_corners)

        # Assign material to visible faces
        shot_check_mat = bpy.data.materials.get("ShotCheck") or bpy.data.materials.new(name="ShotCheck")
        shot_check_mat.use_nodes = True

        for obj in scene.objects:
            if obj.type != 'MESH':
                continue

            mesh = obj.data
            if shot_check_mat.name not in mesh.materials:
                mesh.materials.append(shot_check_mat)

            for poly in mesh.polygons:
                face_center = obj.matrix_world @ poly.center
                if point_in_frustum(face_center, frustum_planes):
                    poly.material_index = mesh.materials.find(shot_check_mat.name)
                else:
                    poly.material_index = -1

        self.report({'INFO'}, "New shot created with visible face coloring")
        return {'FINISHED'}


# Operator to rename the shot and its associated camera
class SHOTDIAL_OT_RenameShot(bpy.types.Operator):
    """Rename a selected shot and its associated camera"""
    bl_idname = "shotdial.rename_shot"
    bl_label = "Rename Shot"

    new_name: bpy.props.StringProperty()  # To store the new name from the UI

    def execute(self, context):
        shot = next((s for s in context.scene.shotdial_shots if s.name == self.new_name), None)
        if shot:
            old_name = shot.name  # Store the old name before renaming
            shot.name = self.new_name
            
            # Now directly access the camera object associated with the shot
            if shot.camera:  # Ensure that the shot has a camera
                shot.camera.name = self.new_name  # Rename the camera object
                self.report({'INFO'}, f"Shot and camera renamed to '{self.new_name}'")
            else:
                self.report({'ERROR'}, "Associated camera not found")
        else:
            self.report({'ERROR'}, "Shot not found")
        return {'FINISHED'}

class SHOTDIAL_PT_ShotPanel(Panel):
    bl_label = "ShotDial Panel"
    bl_idname = "SHOTDIAL_PT_shot_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'ShotDial'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator("shotdial.new_shot", text="New Shot")

        for shot in scene.shotdial_shots:
            box = layout.box()
            row = box.row()
            row.prop(shot, "name", text="")
            row.operator("shotdial.rename_shot", text="Rename").new_name = shot.name
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
            cam_obj = shot.camera  # Get the camera object directly from the shot
            if cam_obj:
                context.scene.camera = cam_obj
                bpy.ops.view3d.view_camera()
                self.report({'INFO'}, f"Set '{shot.name}' as active camera")
            else:
                self.report({'ERROR'}, "Camera not found")
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
            bpy.ops.view3d.view_camera()
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
            bpy.ops.view3d.view_camera()
            self.report({'INFO'}, f"Switched to {cameras[camera_index]}")
        else:
            self.report({'ERROR'}, "No cameras found")
        return {'FINISHED'}

# Register and unregister the classes
def register():
    bpy.utils.register_class(ShotData)
    bpy.utils.register_class(SHOTDIAL_OT_NewShot)
    bpy.utils.register_class(SHOTDIAL_PT_ShotPanel)
    bpy.utils.register_class(SHOTDIAL_OT_SetActiveCamera)
    bpy.utils.register_class(OBJECT_OT_Spin)
    bpy.utils.register_class(OBJECT_OT_DeSpin)
    bpy.utils.register_class(SHOTDIAL_OT_RenameShot)
    bpy.types.Scene.shotdial_shots = CollectionProperty(type=ShotData)

def unregister():
    bpy.utils.unregister_class(ShotData)
    bpy.utils.unregister_class(SHOTDIAL_OT_NewShot)
    bpy.utils.unregister_class(SHOTDIAL_PT_ShotPanel)
    bpy.utils.unregister_class(SHOTDIAL_OT_SetActiveCamera)
    bpy.utils.unregister_class(OBJECT_OT_Spin)
    bpy.utils.unregister_class(OBJECT_OT_DeSpin)
    bpy.utils.unregister_class(SHOTDIAL_OT_RenameShot)
    del bpy.types.Scene.shotdial_shots

if __name__ == "__main__":
    register()
