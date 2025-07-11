# Material Tricks
Showing Shading Rig on a test sphere is all fine and well, but it's obviously not a recreation of a production character. For this part of the docs, I'm going to use this bust, which already has a complex material with textures:
[<img src="../img/sr/bust2.png" width="100%"/>](img/sr/bust2.png)

My goal here is to integrate a shading rig on this bust without breaking the existing materials and show real production techniques.

## Adding a Shading Rig to an Existing Material
When you have a complex material, you can still add a shading rig to it. You just have to add the neccesary nodes from the Shading Rig to your existing material.

In this case, I've **Added Edit to Material** on our character, which has added a new material that looks bad:
[<img src="../img/sr/bust3.png" width="100%"/>](img/sr/bust3.png)

We need to copy some nodes over from the Shading Rig material to our existing material. Specifically, we need to copy **DiffuseToRGB_ShadingRig** and **DiffuseToRGB_ShadingRig**.

Copy those two nodes and switch back to your original material. Paste them: 
[<img src="../img/sr/nodes-to-copy.png" width="100%"/>](img/sr/nodes-to-copy.png)

In order to know how to add these in, we need to know what they do. 

### DiffuseToRGB_ShadingRig
This node is a node group containing a Diffuse BSDF and a Shader To RGB node. 
[<img src="../img/sr/dtr.png" width="100%"/>](img/sr/dtr.png)

I assume you're familar with how cel shading works in Blender, these nodes should be very familiar to you. 

NOTE: If you have complex or non-diffuse shading, that's fine- I will address how to incorporate this in a later section. 

However, the actual node here doesn't matter, just the name. All that matters is that **DiffuseToRGB_ShadingRig** outputs RGB information about lighting. 

In my case, my cel shader already has a DiffuseToRGB shader group that is essentially identical to the one in the Shading Rig.The important thing is the *name* of the node. The Shading Rig relies on the name of these two nodes. You can either rename your existing Shader to RGB node to match the name, or you can swap the DiffuseToRGB_ShadingRig node with your existing Shader to RGB node. I'm going to use both methods here in the docs to show you how they work. I'm going to start with a swap. This is my current node setup: 
[<img src="../img/sr/node-swap1.png" width="100%"/>](img/sr/node-swap1.png)

I'm going to link my inputs and outputs to the DiffuseToRGB_ShadingRig node:
[<img src="../img/sr/node-swap2.png" width="100%"/>](img/sr/node-swap2.png)

Then I can remove the old node and rearrange: 
[<img src="../img/sr/node-swap3.png" width="100%"/>](img/sr/node-swap3.png)

### What if want to use Glossy or something other than Diffuse? 
If you want to use Glossy or something other than Diffuse, you can do that. You just need to make sure that the final node is named **DiffuseToRGB_ShadingRig**. Like this:
[<img src="../img/sr/glossy.png" width="100%"/>](img/sr/glossy.png)
Here, I've renamed a Shader to RGB node.

INFO: This is the easiest way- just build your shader and rename the last Shader to RGB node to **DiffuseToRGB_ShadingRig**.

### ColorRamp_ShadingRig

This node is a Color Ramp node that is used for better blending. Unlike **DiffuseToRGB_ShadingRig**, you should not modify or replace this node. Instead, integrate it with your existing nodes. Generally, you will put this node directly before the color ramp that splits your shading into hard shadow and light areas. 

Currently, I have this:
[<img src="../img/sr/bust4.png" width="100%"/>](img/sr/bust4.png)

I'm going to attach the **ColorRamp_ShadingRig** node:
[<img src="../img/sr/bust5.png" width="100%"/>](img/sr/bust5.png)

At this point, there should not be any nodes between **DiffuseToRGB_ShadingRig** and **ColorRamp_ShadingRig**. 

You are now ready to start using this material. Let's switch our Material in the **Settings**: 
[<img src="../img/sr/bust6.png" width="100%"/>](img/sr/bust6.png)

Now, when we add an Edit and **Add Edit to Material**, we will have a shading rig that works with our existing material:
[<img src="../img/sr/bust7.png" width="100%"/>](img/sr/bust7.png)

## Changing the Influence of the Shading Rig
Now, we have something like this (after some tweaking):
[<img src="../img/sr/bust8.png" width="350px"/>](img/sr/bust8.png)

I like the patch of light on her cheek, but I don't like what's happening with the forehead. I want to add shadow in using an Edit. How can I do this? 

First, I'm going to add a second edit: 
[<img src="../img/sr/bust9.png" width="350px"/>](img/sr/bust9.png)

In my material, I have nodes for both edits:
[<img src="../img/sr/bust10.png" width="100%"/>](img/sr/bust10.png)

I'm going to change the **Lighten** node to **Subtract** for the second edit:
[<img src="../img/sr/bust11.png" width="100%"/>](img/sr/bust11.png)

**Multiply** also works well- here, I wanted more shadow on the side of the face, and I added a third edit with the blend set to **Multiply**: 
<div style = "display:flex">
<img src="../img/sr/bust12.png" />
<img src="../img/sr/bust13.png" />
</div>
(The third edit is visible on the right.)

Ultimately, you can play around with different blending modes and see what feels right. 
