bl_info = {
    "name": "Quick Corrective Blendshapes",
    "author": "Joseph Hansen",
    "version": (1, 0, 8),
    "blender": (3, 6, 13),
    "location": "Object Data Properties > Shape Keys",
    "description": "Makes it simple to create corrective blendshapes",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}

import bpy

class ArpCbsProperties(bpy.types.PropertyGroup):
    show_properties: bpy.props.BoolProperty(default=False)
    use_two_bones: bpy.props.BoolProperty(name="Use Two Bones")
    distance_or_rotation: bpy.props.EnumProperty(name="Comparison Relation", items=[("distance", "Distance", ""), ("rotation", "Rotation", "")])
    root_name: bpy.props.StringProperty(name="Comparison Bone", default="root.x")
    rig: bpy.props.PointerProperty(name="Rig", type=bpy.types.Object, poll=lambda self, obj: obj.type == 'ARMATURE')
    bone1: bpy.props.StringProperty(name="Bone 1")
    bone2: bpy.props.StringProperty(name="Bone 2")
    bone1rest: bpy.props.FloatProperty(name="Bone 1 Rest")
    bone2rest: bpy.props.FloatProperty(name="Bone 2 Rest")
    bone1deform: bpy.props.FloatProperty(name="Bone 1 Deform")
    bone2deform: bpy.props.FloatProperty(name="Bone 2 Deform")
    invert: bpy.props.BoolProperty(name="Invert")
    combinationMethod: bpy.props.EnumProperty(name="Combination Method", items=[("max", "Max", ""), ("min", "Min", ""), ("average", "Average", "")])

class ARP_OT_corrective_blendshape(bpy.types.Operator):
    bl_idname = "arp.corrective_blendshape"
    bl_label = "Corrective Blendshape"

    def execute(self, context):
        context.object.arp_cbs_props.show_properties = True
        return {'FINISHED'}

class ARP_OT_create_driver(bpy.types.Operator):
    bl_idname = "arp.create_driver"
    bl_label = "Create Driver"

    def execute(self, context):
        obj = context.object
        arp_cbs_props = obj.arp_cbs_props
        shape_key = obj.data.shape_keys.key_blocks[obj.active_shape_key_index]
        driver = shape_key.driver_add("value")
        driver.driver.type = 'SCRIPTED'
        
        for var in driver.driver.variables:
            driver.driver.variables.remove(var)
        driver.driver.expression = ""

        var = driver.driver.variables.new()
        var.name = "dist"
        var.type = 'LOC_DIFF' if arp_cbs_props.distance_or_rotation.lower() == 'distance' else 'ROTATION_DIFF'
        var.targets[0].id = arp_cbs_props.rig
        var.targets[0].bone_target = arp_cbs_props.bone1

        var.targets[1].id = arp_cbs_props.rig
        var.targets[1].bone_target = arp_cbs_props.root_name
        
        deform1 = driver.driver.variables.new()
        deform1.name = "deform1"
        deform1.type = 'SINGLE_PROP'
        deform1.targets[0].id = context.object
        deform1.targets[0].data_path = "arp_cbs_props.bone1deform"
        
        rest1 = driver.driver.variables.new()
        rest1.name = "rest1"
        rest1.type = 'SINGLE_PROP'
        rest1.targets[0].id = context.object
        rest1.targets[0].data_path = "arp_cbs_props.bone1rest"
        
        if arp_cbs_props.invert:
            expr1 = "(" + var.name + " - " + rest1.name + ") / (" + deform1.name + " - " + rest1.name + ")"
        else:
            expr1 = "(" + var.name + " - " + deform1.name + ") / (" + rest1.name + " - " + deform1.name + ")"
        driver.driver.expression = expr1
        
        if arp_cbs_props.use_two_bones:
            var2 = driver.driver.variables.new()
            var2.name = "dist2"
            var2.type = 'LOC_DIFF' if arp_cbs_props.distance_or_rotation.lower() == 'distance' else 'ROTATION_DIFF'
            var2.targets[0].id = arp_cbs_props.rig
            var2.targets[0].bone_target = arp_cbs_props.bone2
            var2.targets[1].id = arp_cbs_props.rig
            var2.targets[1].bone_target = "root.x"
            
            deform2 = driver.driver.variables.new()
            deform2.name = "deform2"
            deform2.type = 'SINGLE_PROP'
            deform2.targets[0].id = context.object
            deform2.targets[0].data_path = "arp_cbs_props.bone2deform"
            
            rest2 = driver.driver.variables.new()
            rest2.name = "rest2"
            rest2.type = 'SINGLE_PROP'
            rest2.targets[0].id = context.object
            rest2.targets[0].data_path = "arp_cbs_props.bone2rest"

            if arp_cbs_props.invert:
                expr2 = "(" + var2.name + " - " + rest2.name + ") / (" + deform2.name + " - " + rest2.name + ")"
            else:
                expr2 = "(" + var2.name + " - " + deform2.name + ") / (" + rest2.name + " - " + deform2.name + ")"
            if arp_cbs_props.combinationMethod == "average":
                driver.driver.expression =  "(" + expr1 + " + " + expr2 + ") / 2"
            else:
                driver.driver.expression =  arp_cbs_props.combinationMethod + "(" + expr1 + ", " + expr2 + ")"
                

        return {'FINISHED'}

def draw_func(self, context):
    layout = self.layout
    arp_cbs_props = context.object.arp_cbs_props

    layout.operator(ARP_OT_corrective_blendshape.bl_idname)
    if arp_cbs_props.show_properties:
        layout.prop(arp_cbs_props, "use_two_bones")
        layout.prop_search(arp_cbs_props, "rig", bpy.context.scene, "objects")
        layout.prop(arp_cbs_props, "distance_or_rotation")
        layout.prop(arp_cbs_props, "root_name")
        if arp_cbs_props.rig and arp_cbs_props.rig.type == 'ARMATURE':
            layout.prop(arp_cbs_props, "bone1")
            if arp_cbs_props.use_two_bones:
                layout.prop(arp_cbs_props, "bone2")

        layout.prop(arp_cbs_props, "bone1rest")
        layout.prop(arp_cbs_props, "bone1deform")
        if arp_cbs_props.use_two_bones:
            layout.prop(arp_cbs_props, "bone2rest")
            layout.prop(arp_cbs_props, "bone2deform")
            layout.prop(arp_cbs_props, "combinationMethod")
        layout.prop(arp_cbs_props, "invert")
        layout.operator(ARP_OT_create_driver.bl_idname)

def register():
    bpy.utils.register_class(ArpCbsProperties)
    bpy.utils.register_class(ARP_OT_corrective_blendshape)
    bpy.utils.register_class(ARP_OT_create_driver)
    bpy.types.Object.arp_cbs_props = bpy.props.PointerProperty(type=ArpCbsProperties)
    bpy.types.DATA_PT_shape_keys.append(draw_func)

def unregister():
    bpy.utils.unregister_class(ARP_OT_create_driver)
    bpy.utils.unregister_class(ARP_OT_corrective_blendshape)
    bpy.utils.unregister_class(ArpCbsProperties)
    bpy.types.DATA_PT_shape_keys.remove(draw_func)

if __name__ == "__main__":
    register()