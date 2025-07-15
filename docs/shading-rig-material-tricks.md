# Material Tricks
Showing Shading Rig on a test sphere is all fine and well, but it's obviously not a recreation of a production character. For this part of the docs, I'm going to use this bust, which already has a complex material with textures:
[<img src="../img/sr/srmt-1.jpeg" width="100%"/>](img/sr/srmt-1.jpeg)

My goal here is to integrate a shading rig on this bust without breaking the existing materials and show real production techniques.

NOTE: Due to the limitations of Blender, you can only have 8 edits per material. In this section, we'll go over how to get around this limitation.

## Adding a Shading Rig to an Existing Material
When you have a complex material, you can still add a shading rig to it. You just have to add the neccesary nodes from the Shading Rig to your existing material.

Click **Set Up Shading Rig on Object** like you normally would. 

When you **Set Up Shading Rig on Object**, you will have a new material slot added and a new material set to it:
[<img src="../img/sr/srmt-1a.jpeg" width="100%"/>](img/sr/srmt-1a.jpeg)
Your existing material(s) will be untouched. It is necessary to **Set Up Shading Rig on Object**, but you don't need to use this material. Let's get back to our existing material. Remove the slot and the material `ShadingRigBase_00x`. We're going to recreate the crucial elements of this material on our existing material.

The Shadin Rig looks for `ShadingRig_Entry` and `ShadingRig_Ramp` nodes. `ShadingRig_Entry` is the diffuse, glossy, or otherwise pre-existing shading, converted to RGB. On your materials, this will likely mean renaming your Shader to RGB node to `ShadingRig_Entry`. Note that you must actually rename the node, not just change the label! 

In my case, I have a DiffuseToRGB shader group that outputs diffuse lighting as RGB, so I'm going to rename this node. You can change the name of a node in the Shader Editor sidebar:
[<img src="../img/sr/srmt-2.jpeg" width="300px"/>](img/sr/srmt-2.jpeg)

INFO:  What if want to use Glossy or something other than Diffuse? 
If you want to use Glossy or something other than Diffuse, you can do that. You just need to make sure that the final node is named `ShaderRig_Entry`. 

Next, I'll add a color ramp before the final, hard (constant) color ramp and name it `ShadingRig_Ramp`. 
Now we have this:
[<img src="../img/sr/srmt-3.jpeg" width="100%"/>](img/sr/srmt-3.jpeg)

At this point, there should not be any nodes between `ShaderRig_Entry` and `ShadingRig_Ramp`. 

You are now ready to start using this material. Let's switch our Material in the **Settings**: 
[<img src="../img/sr/srmt-4.jpeg" width="100%"/>](img/sr/srmt-4.jpeg)
And add an Effect:
[<img src="../img/sr/srmt-5a.jpeg" width="100%"/>](img/sr/srmt-5a.jpeg)
When we **Add Effect to Material**, we will have a shading rig that works with our existing material. I've added three edits as an example: 
[<img src="../img/sr/srmt-6.jpeg" width="100%"/>](img/sr/srmt-6.jpeg)

## Clamping
When stacking multiple Effects, you will go outside of a normalized range of [0,1]. If an Effect is behaving strangely or you are having difficulty controlling it, you may need to clamp it. In your nodes, find the `ShadingRigEffect_SR_Effect_*` node. In my case, I've clamped `ShadingRigEffect_SR_Effect_Bust_003`:
[<img src="../img/sr/srmt-7.jpeg" width="100%"/>](img/sr/srmt-7.jpeg)

To do this, put a Math node set to Add (with second input 0) between `ShadingRigEffect_SR_Effect_Bust_003` and all of its outputs. It's much easier to do this if you add a reroute, as I've done. Then you can toggle clamping as desired. Compare clamping on:
[<img src="../img/sr/srmt-8.jpeg" width="100%"/>](img/sr/srmt-8.jpeg)
Versus clamping off:
[<img src="../img/sr/srmt-9.jpeg" width="100%"/>](img/sr/srmt-9.jpeg)

## Isolating an Effect
Sometimes, it can be difficult to pinpoint exactly where an Effect is, especially on a complex mesh. Here, I am using the Blender realistic female basemesh as an example. I have an Effect, but I'm not sure it's doing what I want:
[<img src="../img/sr/srmt-10.jpeg" width="350px"/>](img/sr/srmt-10.jpeg)

To preview *just* an Effect without everything else going on, find the `ShadingRigEffect_SR_Effect_*` node- in my case,  `ShadingRigEffect_SR_Effect_BlenderBasemesh_001` and Preview it by Ctrl + Shift + Left Click: 
[<img src="../img/sr/srmt-11.jpeg" width="100%"/>](img/sr/srmt-11.jpeg)
I want to add some shading to the arm around the elbow. I'm going to do this with careful manipulation of the Effect, including scale, location, and rotation. To get the shader back how it should be, find your ramps and connect the final ramp back to the Material Output: 
[<img src="../img/sr/srmt-12.jpeg" width="100%"/>](img/sr/srmt-12.jpeg)

Now my arm looks great, but the legs have undesired shading from the Effect. Effects affect the entire object, so you will generally need to split your object up into multiple materials. Here, I've separated the section I want this Effect to affect:
[<img src="../img/sr/srmt-13.jpeg" width="100%"/>](img/sr/srmt-13.jpeg)

I'm now going to modify both materials so they look identical. By giving my new material the required nodes, I can add Effects to this material as well. I'm going to copy four nodes from the other material:
[<img src="../img/sr/srmt-14.jpeg" width="100%"/>](img/sr/srmt-14.jpeg)

Compare:
[<img src="../img/sr/srmt-15.jpeg" width="100%"/>](img/sr/srmt-15.jpeg)
With: 
[<img src="../img/sr/srmt-16.jpeg" width="100%"/>](img/sr/srmt-16.jpeg)

NOTE: It may feel strange to consider breaking your object up into many materials that look and behave the same. However, this is the best way to work around the limitation of having only 8 Effects per material. With the simple two-material split I've done here, I can now have 16 total Effects for this object. So, for best results, split your object into major "chunks" by material (i.e. hair, head, shirt, pants, shoes, etc).

I know this way is not ideal, but until Blender fixes this particular issue, this is the best way to work with the Shading Rig.