bl_info = {
    "name": "TapTapSwap",
    "description": "Add some useful swapping shortcut",
    "author": "Samuel Bernou, Tonton, based on Cédric Lepiller/Hjalti Hjalmarsson ideas, Joseph Hansen",
    "version": (1, 7, 7),
    "blender": (3, 6, 5),
    "location": "Hit TAB swap outliner/property editor, \
        Ctrl+TAB swap outliner mode, add Shift to reverse, \
        Z swap dopesheet/graph editor, shift+Z in timeline, \
        Ctrl+Shift+Alt+X swap active object's properties tabs from anywhere",
    "warning": "",
    "doc_url": "https://github.com/Pullusb/TapTapSwap",
    "category": "User Interface"}

import bpy

def set_panel(panel):
    '''take a panel name and apply it to properties zone'''
    if bpy.context.area.type == 'PROPERTIES':
        bpy.context.area.spaces.active.context = panel
        return

    for area in bpy.context.screen.areas:
        if area.type == 'PROPERTIES':
            for space in area.spaces:
                if space.type == 'PROPERTIES':
                    space.context = panel
                    return

def get_panel():
    '''return active panel name of the properties zone'''
    if bpy.context.area.type == 'PROPERTIES':
        return bpy.context.area.spaces.active.context

    for area in bpy.context.screen.areas:
        if area.type == 'PROPERTIES':
            for space in area.spaces:
                if space.type == 'PROPERTIES':
                    return space.context

def bone_has_physics(ob):
    if ob.rigid_body or ob.rigid_body_constraint:
        return 1
    else:
        return 0

def has_physics(ob):
    if ob.rigid_body or ob.rigid_body_constraint:
        return 1
    
    if ob.type == 'MESH' and ob.collision and ob.collision.use:
        return 1

    if hasattr(ob, 'field') and ob.field and ob.field.type != 'NONE':
        return 1

    if has_mod(ob):
        for m in ob.modifiers:
            if m.type in ['CLOTH', 'SOFT_BODY', 'FLUID_SIMULATION', 'DYNAMIC_PAINT', 'SMOKE']:
                return 1
    return 0

def has_mod(ob):
    if ob.type == 'GPENCIL':
        return len(ob.grease_pencil_modifiers)
    else:
        return len(ob.modifiers)

def has_gp_fx(ob):
    return len(ob.shader_effects)

def has_const(ob):
    return len(ob.constraints)

def has_mat(ob):
    return len(ob.material_slots)

def has_particles(ob):
    return len(ob.particle_systems)

def swap_properties_panel():
    obj = bpy.context.object
    if not obj:
        return (1, 'must select an active object')

    pan = get_panel()
    if not pan:
        return (1, '"properties" region must be visible on screen')

    objects_dic = {
    'MESH': ['DATA','MATERIAL','OBJECT','MODIFIER','PARTICLES','PHYSICS','CONSTRAINT',],
    'CURVE' : ['DATA','MATERIAL','OBJECT','MODIFIER','PHYSICS','CONSTRAINT',],
    'EMPTY': ['DATA','PHYSICS', 'OBJECT','CONSTRAINT',],
    'ARMATURE': ['DATA', 'BONE','BONE_CONSTRAINT', 'PHYSICS', 'OBJECT','CONSTRAINT',],
    'CAMERA' : ['DATA','OBJECT','CONSTRAINT',],
    'LATTICE' : ['DATA','OBJECT','MODIFIER','CONSTRAINT',],
    'LIGHT' : ['DATA','PHYSICS','OBJECT','CONSTRAINT',],
    'FONT' : ['DATA','MATERIAL','PHYSICS','OBJECT','CONSTRAINT', 'MODIFIER',],
    'GPENCIL' : ['DATA','MATERIAL','OBJECT','MODIFIER', 'SHADERFX','PHYSICS', 'CONSTRAINT',]
    }

    props = objects_dic[obj.type]

    # Actualize props list to keep only available
    for p in list(props):
        if p == 'PARTICLES' and not has_particles(obj):
            props.remove(p)
        elif p == 'MODIFIER' and not has_mod(obj):
            props.remove(p)
        elif p == 'SHADERFX' and not has_gp_fx(obj):
            props.remove(p)
        elif p == 'MATERIAL' and not has_mat(obj):
            props.remove(p)
        elif p == 'CONSTRAINT' and not has_const(obj):
            props.remove(p)
        elif p == 'PHYSICS' and not has_physics(obj):
            props.remove(p)

    if pan in props:
        nextpan = props[(props.index(pan) + 1) % len(props)]
    else:
        nextpan = props[0]

    set_panel(nextpan)

class UI_OT_swap_panel_prop(bpy.types.Operator):
    bl_idname = "taptap.swap_panel_prop"
    bl_label = "Swap Panel Properties"
    bl_description = "Swap panel on properties"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        swap_properties_panel()
        return {"FINISHED"}
    
class UI_OT_swap_timeline_dopesheet_mode(bpy.types.Operator):
    bl_idname = "taptap.swap_timeline_dopesheet_mode"
    bl_label = "Swap Timeline and Dopesheet"
    bl_description = "Swap Timeline and Dopesheet editor"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        space = context.area.spaces.active # context.area.spaces[0]
        space.mode = 'DOPESHEET' if space.mode == 'TIMELINE' else 'TIMELINE'
        return {"FINISHED"}

def set_outliner_mode(mode):
    '''take a panel name and apply it to properties zone'''
    area = bpy.context.area
    if area.type == 'OUTLINER':
        area.spaces[0].display_mode = mode
        return 1
    return 0

def get_outliner_mode():
    '''return active panel name of the properties zone'''
    area = bpy.context.area
    if area.type == 'OUTLINER':
        return area.spaces[0].display_mode
    return 0

def swap_outliner_mode(revert=False):
    modes = [
        "SCENES",
        "VIEW_LAYER",
        "SEQUENCE",
        "LIBRARIES",
        "DATA_API",
        "LIBRARY_OVERRIDES",
        "ORPHAN_DATA",
        ]

    mode = get_outliner_mode()
    if not mode:
        return (1, 'No active outliner')

    idx = modes.index(mode)
    offset = -1 if revert else 1
    nextmode = modes[(idx + offset) % len(modes)]
    set_outliner_mode(nextmode)

class UI_OT_swap_outliner_mode(bpy.types.Operator):
    bl_idname = "taptap.swap_outliner_mode"
    bl_label = "Swap Outliner Mode"
    bl_description = "Swap outliner mode"
    bl_options = {"REGISTER", "INTERNAL"}

    revert : bpy.props.BoolProperty(name="Revert")

    def execute(self, context):
        swap_outliner_mode(revert=self.revert)
        return {"FINISHED"}

###--KEYMAPS

addon_keymaps = []

def register_keymaps():
    addon = bpy.context.window_manager.keyconfigs.addon

    ###### Object Property swap

    ## All editor:
    km = addon.keymaps.new(name = "Window", space_type='EMPTY', region_type='WINDOW')
    ## ctrl+shift+X taken by carver ! so add alt
    kmi = km.keymap_items.new("taptap.swap_panel_prop", type = "X", value = "PRESS", shift = True, ctrl = True, alt = True)
    addon_keymaps.append((km, kmi))

    ###### Outliner / Properties Swap

    ## From Properties to Outliner - Tab
    km = addon.keymaps.new(name = "Property Editor",space_type='PROPERTIES', region_type='WINDOW')
    kmi = km.keymap_items.new("wm.context_set_enum", type = "TAB", value = "PRESS")
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'OUTLINER'
    addon_keymaps.append((km, kmi))

    ## From Outliner to Properties - Tab
    km = addon.keymaps.new(name = "Outliner",space_type='OUTLINER', region_type='WINDOW')
    kmi = km.keymap_items.new("wm.context_set_enum", type = "TAB", value = "PRESS")
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'PROPERTIES'
    addon_keymaps.append((km, kmi))
    
    ## From Shader Nodes to Geometry Nodes - Shift + Tilde
    km = addon.keymaps.new(name = "Node Editor", space_type='NODE_EDITOR', region_type='WINDOW')
    kmi = km.keymap_items.new("node.switch_to_geometry", type = "ACCENT_GRAVE", value = "PRESS", shift=True)
    addon_keymaps.append((km, kmi))

    ## From Geometry Nodes to Shader Nodes - Shift + Tilde
    km = addon.keymaps.new(name = "Node Editor", space_type='NODE_EDITOR', region_type='WINDOW')
    kmi = km.keymap_items.new("node.switch_to_shader", type = "ACCENT_GRAVE", value = "PRESS", shift=True)
    addon_keymaps.append((km, kmi))

    ## Outliner mode swap
    kmi = km.keymap_items.new("taptap.swap_outliner_mode", type = "TAB", value = "PRESS", ctrl = True)
    kmi.properties.revert=False
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("taptap.swap_outliner_mode", type = "TAB", value = "PRESS", ctrl = True, shift=True)
    kmi.properties.revert=True
    addon_keymaps.append((km, kmi))

    ###### Dopesheet / Timeline / GraphEditor Swap - Z

    km = addon.keymaps.new(name = "Dopesheet", space_type='DOPESHEET_EDITOR', region_type='WINDOW')

    ## Dopesheet -> Graph - Z
    kmi = km.keymap_items.new("wm.context_set_enum", type = "Z", value = "PRESS")
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'GRAPH_EDITOR'
    addon_keymaps.append((km, kmi))

    ## Dopesheet <-> Timeline Swap - shift Z
    kmi = km.keymap_items.new("taptap.swap_timeline_dopesheet_mode", type = "Z", value = "PRESS", shift = True)
    addon_keymaps.append((km, kmi))

    ## Graph -> dopesheet - Z
    km = addon.keymaps.new(name = "Graph Editor",space_type='GRAPH_EDITOR', region_type='WINDOW')
    kmi = km.keymap_items.new("wm.context_set_enum", type = "Z", value = "PRESS")
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'DOPESHEET_EDITOR'
    addon_keymaps.append((km, kmi))

def unregister_keymaps():
    for km, kmi in addon_keymaps:
        if kmi in km.keymap_items[:]:
            # check first to skip, kmi registered in 'Window' (avoir error: Cannot be removed from window)
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()


class NODE_OT_switch_to_geometry(bpy.types.Operator):
    bl_idname = "node.switch_to_geometry"
    bl_label = "Switch to Geometry Nodes"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

    def execute(self, context):
        context.space_data.tree_type = 'GeometryNodeTree'
        return {'FINISHED'}

class NODE_OT_switch_to_shader(bpy.types.Operator):
    bl_idname = "node.switch_to_shader"
    bl_label = "Switch to Shader Nodes"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'GeometryNodeTree'

    def execute(self, context):
        context.space_data.tree_type = 'ShaderNodeTree'
        return {'FINISHED'}

classes = (
    UI_OT_swap_panel_prop,
    UI_OT_swap_timeline_dopesheet_mode,
    UI_OT_swap_outliner_mode,
    NODE_OT_switch_to_geometry,
    NODE_OT_switch_to_shader
    
)

###--REGISTER

def register():
    if bpy.app.background:
        return

    for cls in classes:
        bpy.utils.register_class(cls)

    register_keymaps()

def unregister():
    if bpy.app.background:
        return

    unregister_keymaps()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()

