bl_info = {
    "name": "Silhouette View Toggle",
    "blender": (3, 6, 13),
}

import bpy

previous_settings = {}
is_silhouette_view = False

def toggle_silhouette_view(self, context):
    global previous_settings, is_silhouette_view
    
    if not is_silhouette_view:
        previous_settings['shading_type'] = bpy.context.space_data.shading.type
        previous_settings['shading_light'] = bpy.context.space_data.shading.light
        previous_settings['background_type'] = bpy.context.space_data.shading.background_type
        previous_settings['background_color'] = bpy.context.space_data.shading.background_color[:]
        previous_settings['color_type'] = bpy.context.space_data.shading.color_type
        previous_settings['single_color'] = bpy.context.space_data.shading.single_color[:]
        previous_settings['show_cavity'] = bpy.context.space_data.shading.show_cavity
        previous_settings['show_xray'] = bpy.context.space_data.shading.show_xray
        previous_settings['show_shadows'] = bpy.context.space_data.shading.show_shadows
        previous_settings['show_overlays'] = bpy.context.space_data.overlay.show_overlays
        previous_settings['show_object_outline'] = bpy.context.space_data.shading.show_object_outline
        
        bpy.context.space_data.shading.type = 'SOLID'
        bpy.context.space_data.shading.light = 'FLAT'
        bpy.context.space_data.shading.background_type = "VIEWPORT"
        bpy.context.space_data.shading.background_color = (0, 0, 0)
        bpy.context.space_data.shading.color_type = 'SINGLE'
        bpy.context.space_data.shading.single_color = (1, 1, 1)
        bpy.context.space_data.shading.show_cavity = False
        bpy.context.space_data.shading.show_xray = False
        bpy.context.space_data.shading.show_shadows = False
        bpy.context.space_data.overlay.show_overlays = False
        bpy.context.space_data.shading.show_object_outline = False
        
        is_silhouette_view = True
    else:
        bpy.context.space_data.shading.type = previous_settings['shading_type']
        bpy.context.space_data.shading.light = previous_settings['shading_light']
        bpy.context.space_data.shading.background_type = previous_settings['background_type']
        bpy.context.space_data.shading.background_color = previous_settings['background_color']
        bpy.context.space_data.shading.color_type = previous_settings['color_type']
        bpy.context.space_data.shading.single_color = previous_settings['single_color']
        bpy.context.space_data.shading.show_cavity = previous_settings['show_cavity']
        bpy.context.space_data.shading.show_xray = previous_settings['show_xray']
        bpy.context.space_data.shading.show_shadows = previous_settings['show_shadows']
        bpy.context.space_data.overlay.show_overlays = previous_settings['show_overlays']
        bpy.context.space_data.shading.show_object_outline = previous_settings['show_object_outline']
        
        is_silhouette_view = False

class ToggleSilhouetteViewOperator(bpy.types.Operator):
    bl_idname = "wm.toggle_silhouette_view"
    bl_label = "Toggle Silhouette View"
    
    def execute(self, context):
        toggle_silhouette_view(self, context)
        return {'FINISHED'}

def draw_toggle_button(self, context):
    layout = self.layout
    layout.prop(context.scene, "is_silhouette_view", text="Matte", toggle=True, icon='MOD_MASK')

def register():
    bpy.utils.register_class(ToggleSilhouetteViewOperator)
    bpy.types.Scene.is_silhouette_view = bpy.props.BoolProperty(
        name="Silhouette View",
        description="Toggle Silhouette View",
        default=False,
        update=toggle_silhouette_view
    )
    bpy.types.VIEW3D_HT_header.append(draw_toggle_button)

def unregister():
    bpy.utils.unregister_class(ToggleSilhouetteViewOperator)
    del bpy.types.Scene.is_silhouette_view
    bpy.types.VIEW3D_HT_header.remove(draw_toggle_button)

if __name__ == "__main__":
    register()