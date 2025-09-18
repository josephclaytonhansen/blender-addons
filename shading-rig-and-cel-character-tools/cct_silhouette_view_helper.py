import bpy
bpy.is_silhouette_view = False

bpy.cct_silhouette_view_previous_settings = {
    'shading_type': None,
    'shading_light': None,
    'background_type': None,
    'background_color': None,
    'color_type': None,
    'single_color': None,
    'show_cavity': None,
    'show_xray': None,
    'show_shadows': None,
    'show_overlays': None,
    'show_object_outline': None
}

def toggle_silhouette_view(self, context):
    if not bpy.is_silhouette_view:
        bpy.cct_silhouette_view_previous_settings['shading_type'] = bpy.context.space_data.shading.type
        bpy.cct_silhouette_view_previous_settings['shading_light'] = bpy.context.space_data.shading.light
        bpy.cct_silhouette_view_previous_settings['background_type'] = bpy.context.space_data.shading.background_type
        bpy.cct_silhouette_view_previous_settings['background_color'] = bpy.context.space_data.shading.background_color[:]
        bpy.cct_silhouette_view_previous_settings['color_type'] = bpy.context.space_data.shading.color_type
        bpy.cct_silhouette_view_previous_settings['single_color'] = bpy.context.space_data.shading.single_color[:]
        bpy.cct_silhouette_view_previous_settings['show_cavity'] = bpy.context.space_data.shading.show_cavity
        bpy.cct_silhouette_view_previous_settings['show_xray'] = bpy.context.space_data.shading.show_xray
        bpy.cct_silhouette_view_previous_settings['show_shadows'] = bpy.context.space_data.shading.show_shadows
        bpy.cct_silhouette_view_previous_settings['show_overlays'] = bpy.context.space_data.overlay.show_overlays
        bpy.cct_silhouette_view_previous_settings['show_object_outline'] = bpy.context.space_data.shading.show_object_outline
        
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
        
        bpy.is_silhouette_view = True
    else:
        bpy.context.space_data.shading.type = bpy.cct_silhouette_view_previous_settings['shading_type']
        bpy.context.space_data.shading.light = bpy.cct_silhouette_view_previous_settings['shading_light']
        bpy.context.space_data.shading.background_type = bpy.cct_silhouette_view_previous_settings['background_type']
        bpy.context.space_data.shading.background_color = bpy.cct_silhouette_view_previous_settings['background_color']
        bpy.context.space_data.shading.color_type = bpy.cct_silhouette_view_previous_settings['color_type']
        bpy.context.space_data.shading.single_color = bpy.cct_silhouette_view_previous_settings['single_color']
        bpy.context.space_data.shading.show_cavity = bpy.cct_silhouette_view_previous_settings['show_cavity']
        bpy.context.space_data.shading.show_xray = bpy.cct_silhouette_view_previous_settings['show_xray']
        bpy.context.space_data.shading.show_shadows = bpy.cct_silhouette_view_previous_settings['show_shadows']
        bpy.context.space_data.overlay.show_overlays = bpy.cct_silhouette_view_previous_settings['show_overlays']
        bpy.context.space_data.shading.show_object_outline = bpy.cct_silhouette_view_previous_settings['show_object_outline']
        
        bpy.is_silhouette_view = False