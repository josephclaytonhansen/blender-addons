bl_info = {
    "name": "ShotDial",
    "author": "Joseph Hansen",
    "version": (1, 3, 22),
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

# Storage for shot data as a PropertyGroup
class ShotData(bpy.types.PropertyGroup):
    name: StringProperty(name="Name", default="Shot")
    color: FloatVectorProperty(name="Color", subtype='COLOR', min=0, max=1, default=(1.0, 1.0, 1.0))
    camera: bpy.props.PointerProperty(type=bpy.types.Object)  # Store the camera object directly

# List to store all shots
camera_index = 0
addon_keymaps = []

# Function to check if a point is inside the camera's frustum
def point_in_frustum(point, planes, camera_location):
    point_local = point - camera_location
    for plane in planes:
        if plane.dot(point_local) < 0:
            return False
    return True

# Function to check if a face is visible from the camera
def is_face_visible(camera, obj, face):
    cam_matrix = camera.matrix_world
    cam_data = camera.data
    cam_location = camera.location
    planes = cam_data.view_frame(scene=bpy.context.scene)
    planes = [plane.normalized() for plane in planes]

    face_verts = [obj.data.vertices[i].co for i in face.vertices]
    face_verts_local = [cam_matrix.inverted() @ v for v in face_verts]

    return any(point_in_frustum(vert, planes, cam_location) for vert in face_verts_local)

# Operator to create a new shot and color visible faces
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
        new_shot.camera = cam_obj  # Store the camera object directly

        # Link the camera to the shot name
        cam_obj.name = shot_name  # This makes the camera's name match the shot's name

        # Create a boolean attribute for the new shot
        for obj in context.scene.objects:
            if obj.type == 'MESH':
                attr_name = f"shot_{shot_name}"
                if attr_name not in obj.data.attributes:
                    obj.data.attributes.new(name=attr_name, type='BOOLEAN', domain='FACE')
                bool_layer = obj.data.attributes[attr_name].data

                for poly in obj.data.polygons:
                    if is_face_visible(cam_obj, obj, poly):
                        bool_layer[poly.index].value = True
                    else:
                        bool_layer[poly.index].value = False

        # Create or get the "ShotCheck" material
        if "ShotCheck" not in bpy.data.materials:
            shot_check_mat = bpy.data.materials.new(name="ShotCheck")
            shot_check_mat.use_nodes = True
        else:
            shot_check_mat = bpy.data.materials["ShotCheck"]

        # Set the viewport display color to the shot color
        shot_check_mat.diffuse_color = (*shot_color, 1.0)

        # Assign the "ShotCheck" material to visible faces
        for obj in context.scene.objects:
            if obj.type == 'MESH':
                if shot_check_mat.name not in obj.data.materials:
                    obj.data.materials.append(shot_check_mat)
                attr_name = f"shot_{shot_name}"
                bool_layer = obj.data.attributes[attr_name].data

                for poly in obj.data.polygons:
                    if bool_layer[poly.index].value:
                        obj.data.polygons[poly.index].material_index = obj.data.materials.find(shot_check_mat.name)
                    else:
                        obj.data.polygons[poly.index].material_index = -1

        context.area.tag_redraw()
        self.report({'INFO'}, f"Shot '{shot_name}' created with visible face coloring")
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
