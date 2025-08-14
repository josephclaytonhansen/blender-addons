import bpy

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