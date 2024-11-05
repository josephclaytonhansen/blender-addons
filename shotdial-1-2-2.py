import bpy
from bpy.app.handlers import persistent

bl_info = {
    "name": "ShotDial",
    "author": "Joseph Hansen",
    "version": (1, 2, 2),
    "blender" : (3, 60, 13),
    "location": "",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D View"
}
camera_index = 0

class OBJECT_OT_Spin(bpy.types.Operator):
    """Move between camera views (forwards)"""
    bl_idname = "shotdial.spin"
    bl_label = "Move between camera views (forwards)"
    
    def execute(self, context):
        global camera_index
        obj_in_scene = bpy.context.scene.collection.all_objects
        cameras = [obj for obj in obj_in_scene if obj.type == 'CAMERA']

        area = next((area for area in bpy.context.screen.areas if area.type == "VIEW_3D"), None)
        if not area:
            self.report({'ERROR'}, "No VIEW_3D area found")
            return {'CANCELLED'}

        region = next((region for region in area.regions if region.type == "WINDOW"), None)
        if not region:
            self.report({'ERROR'}, "No WINDOW region found")
            return {'CANCELLED'}

        space = area.spaces[0]
        context = bpy.context.copy()
        context['area'] = area
        context['region'] = region
        context['space_data'] = space
        
        high = len(cameras)
        camera_index += 1
        if camera_index == high:
            camera_index = 0
        bpy.context.scene.camera = cameras[camera_index]
        
        if space.region_3d.view_perspective == "CAMERA":
            bpy.ops.view3d.view_camera(context)
            bpy.ops.view3d.view_camera(context)
        else:
            bpy.ops.view3d.view_camera(context)
        return {'FINISHED'}

class OBJECT_OT_DeSpin(bpy.types.Operator):
    """Move between camera views (backwards)"""
    bl_idname = "shotdial.despin"
    bl_label = "Move between camera views (backwards)"
    
    def execute(self, context):
        global camera_index
        obj_in_scene = bpy.context.scene.collection.all_objects
        cameras = [obj for obj in obj_in_scene if obj.type == 'CAMERA']

        area = next((area for area in bpy.context.screen.areas if area.type == "VIEW_3D"), None)
        if not area:
            self.report({'ERROR'}, "No VIEW_3D area found")
            return {'CANCELLED'}

        region = next((region for region in area.regions if region.type == "WINDOW"), None)
        if not region:
            self.report({'ERROR'}, "No WINDOW region found")
            return {'CANCELLED'}

        space = area.spaces[0]
        context = bpy.context.copy()
        context['area'] = area
        context['region'] = region
        context['space_data'] = space
        
        high = len(cameras)
        camera_index -= 1
        if camera_index < 0:
            camera_index = high-1
        bpy.context.scene.camera = cameras[camera_index]
        
        if space.region_3d.view_perspective == "CAMERA":
            bpy.ops.view3d.view_camera(context)
            bpy.ops.view3d.view_camera(context)
        else:
            bpy.ops.view3d.view_camera(context)
        return {'FINISHED'}

addon_keymaps = []

class OBJECT_OT_addAndBind(bpy.types.Operator):
    """Add a marker and bind the current camera"""
    bl_idname = "shotdial.add_and_bind"
    bl_label = "Add a marker and bind the current camera"
    
    def execute(self, context):
        global camera_index
        obj_in_scene = bpy.context.scene.collection.all_objects
        cameras = [obj for obj in obj_in_scene if obj.type == 'CAMERA']
        
        try:
            marker = bpy.context.scene.timeline_markers.new(name = "F.SD."+str(bpy.context.scene.frame_current), frame=bpy.context.scene.frame_current)
            marker.camera = cameras[camera_index]
        except Exception as e:
            self.report({'ERROR'}, str(e))
        return{'FINISHED'}


@persistent
def SdSpin_HT_view3d(self, context):
    self.layout.operator(
        operator='shotdial.spin',
        icon='TRIA_RIGHT',
        text=''
    )

@persistent
def SdDeSpin_HT_view3d(self, context):
    self.layout.operator(
        operator='shotdial.despin',
        icon='TRIA_LEFT',
        text=''
    )

@persistent
def SdAddAndBind_HT_view3d(self, context):
    self.layout.operator(
        operator='shotdial.add_and_bind',
        icon='CAMERA_DATA',
        text=''
    )
    
def register():
    bpy.utils.register_class(OBJECT_OT_Spin)
    bpy.utils.register_class(OBJECT_OT_DeSpin)
    bpy.utils.register_class(OBJECT_OT_addAndBind)
    
    bpy.types.DOPESHEET_HT_header.append(SdDeSpin_HT_view3d)
    bpy.types.DOPESHEET_HT_header.append(SdAddAndBind_HT_view3d)
    bpy.types.DOPESHEET_HT_header.append(SdSpin_HT_view3d)
    

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(OBJECT_OT_Spin.bl_idname, type='W', value='PRESS', ctrl=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(OBJECT_OT_DeSpin.bl_idname, type='W', value='PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(OBJECT_OT_addAndBind.bl_idname, type='M', value='PRESS', ctrl=False, shift=False, alt=True)
        addon_keymaps.append((km, kmi))


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_Spin)
    bpy.utils.unregister_class(OBJECT_OT_DeSpin)
    bpy.utils.unregister_class(OBJECT_OT_addAndBind)
    
    bpy.types.DOPESHEET_HT_header.remove(SdSpin_HT_view3d)
    bpy.types.DOPESHEET_HT_header.remove(SdDeSpin_HT_view3d)
    bpy.types.DOPESHEET_HT_header.remove(SdAddAndBind_HT_view3d)

    
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()
