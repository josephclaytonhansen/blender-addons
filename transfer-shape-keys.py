bl_info = {
	"name": "Transfer Shape Keys",
	"author": "Joseph Hansen",
 	"blender": (4,2,0),
 	"version": (1,0,0)
}

import bpy

class TransferShapeKeysOperator(bpy.types.Operator):
    bl_idname = "object.transfer_shape_keys"
    bl_label = "Transfer Shape Keys"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        source = context.active_object
        target = context.selected_objects[1] if context.selected_objects[0] == source else context.selected_objects[0]

        assert source.data and source.data.shape_keys, "Source object has no shape key data."

        blocks = source.data.shape_keys.key_blocks

        if not context.mode == "OBJECT" and context.active_object:
            bpy.ops.object.mode_set(mode="OBJECT")

        bpy.ops.object.select_all(action="DESELECT")
        source.select_set(True)
        target.select_set(True)
        context.view_layer.objects.active = target

        basis = target.data.shape_keys.key_blocks["Basis"]

        for block in blocks:
            if block.name == "Basis":
                continue

            target.shape_key_add(name=block.name, from_mix=False)
            target_key_block = target.data.shape_keys.key_blocks[block.name]
            target_key_block.relative_key = basis

            for index, vertex in enumerate(block.data):
                target_key_block.data[index].co = vertex.co

            self.report({"INFO"}, f"Transferred shape {block.name} from {source.name} to {target.name}")

        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(TransferShapeKeysOperator.bl_idname)

def register():
    bpy.utils.register_class(TransferShapeKeysOperator)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(menu_func)

def unregister():
    bpy.utils.unregister_class(TransferShapeKeysOperator)
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func)

if __name__ == "__main__":
    register()
