# Troubleshooting
Shading Rig is designed for intermediate to advanced users. It doesn't provide magic buttons- rather, it adds tools that enhance existing Blender functionality. 

To work effectively with Shading Rig, you need to be comfortable navigating and using the shader editor. You also need to be familiar with material assignments, material slots, and custom properties. You don't need in-depth experience with any of this, but you need to understand the basics. If you are a beginner to Blender, you should hold off on using Shading Rig until you are more comfortable with Blender as a whole. 

If you have a problem not addressed below, I will help you solve it if you have a seat license. Otherwise, you will have to find an answer through trial and error or elsewhere in the docs. 

## Why am I not seeing an effect? 
### Reset Rotation
The most common problem I've encountered as people test this is that the Effect isn't showing. In 99% of cases I've observed, the problem is with **rotation** of the empty controlling the Effect. The first thing you should when troubleshooting is **reset the rotation of the Empty** (you can do this with Alt + R):
[<img src="../img/sr/qsrw-10.gif" width="100%"/>](img/sr/qsrw-10.gif)
Here, my Effect was not showing up. I reset the rotation, and it shows up. 
### Check Distance from Object
If that doesn't do it, move the empty closer to your object. The distance from the object matters:
[<img src="../img/sr/qsrw-11.gif" width="100%"/>](img/sr/qsrw-11.gif)
Keep your effects close to your object for best results. 
### Check Parameters
Increase the Hardness. At lower values, the Effect may not always show up.
### Check Mode
When in doubt, switch back to Mode 0, which will always show up.

### Did you change, disconnect, or rename something in the shader? 
WARNING: Don't!

There are things you can play with in the shader and **things you cannot**. Anything between the two red "**Do not touch this!**" frames, you must not alter in any way!

[<img src="../img/sr/touch-this.jpeg" width="100%"/>](img/sr/touch-this.jpeg)
[<img src="../img/sr/touch-this2.jpeg" width="100%"/>](img/sr/touch-this2.jpeg)

You can change, modify, rename, or do whatever with the "**You Can Touch This**" nodes. You cannot in any way alter the red "**Do not touch this!**" node after it. Don't look at it. Don't think about it. Expunge it entirely from your mind and memory. If you modify one of these forbidden nodes or any of the nodes _in-between_ the two forbidden nodes, *you will break everything permanently.* The only way to fix this is to manually remove these nodes, delete the Effect, and recreate it.

One last time, just for safety: **don't touch anything between and including red "Do Not Touch This!" nodes!!**

## I add another effect and suddenly everything turns white/black!
You've moved your data to a range beyond what can be displayed. Change the mode of your effect, and try clamping. (See [Material Tricks](shading-rig-material-tricks.md) for details.) Be especially careful with combining multiple *Add* and *Subtract* mode effects. If you *Add* to an *Add*, you have now moved your data from a [0,1] range to a [1,2] range. If you *Subtract* from a *Subtract*, your data is now in a [-1,0] range. In either case, you will see only white or only black. 

## I add an effect and my material doesn't show any shading?
Scale down your Effect. If the scale is too large, it will flood the whole object. 

## I can't append the required nodes?
Set a **Character Name**.

## I can't add a correspondence?
Your Effect doesn't have a light set.

## Parameter X doesn't seem to do anything when I change it?
Some values only show up when you scale or rotate the effect. Reset your rotation, then rotate. Play around. 

## All the parameters do nothing?
You've most likely broken the custom properties on your object. This happens from time to time if you aggressively undo or otherwise screw with your data. You can tell really easily, pull up the custom properties on your object:
[<img src="../img/sr/srt-2.jpeg" width="100%"/>](img/sr/srt-2.jpeg)
Adjust parameters:
[<img src="../img/sr/srt-1.jpeg" width="100%"/>](img/sr/srt-1.jpeg)
If the custom property changes, everything is fine. Reset your rotation and scale down your empty. If it doesn't change, you've broken something. The simplest fix is to simply remove the custom property, remove the effects, and redo.

## My Effect is jumping suddenly between correlations as I rotate the light?
The reason for this behavior is explained in [Correlations](shading-rig-correlations.md). Try removing some of your correlations and use less correlations. The more correlations, the more likely jumpiness is. 

## I deleted the `ShadingRigBase_00x` material from my object, now I cannot get the Effects to show up!
Make sure whatever material you are using has the two required nodes (see [Material Tricks](shading-rig-material-tricks.md)). Note that it's the node *name*, not the node *label* that matters. It's easy to get tripped up by this, because the name isn't displayed in the Shader Editor. For example, this will work: 
[<img src="../img/sr/srt-3.jpeg" width="100%"/>](img/sr/srt-3.jpeg)

This will **not** work:
[<img src="../img/sr/srt-4.jpeg" width="100%"/>](img/sr/srt-34.jpeg)

## I get a popup error `AttributeError: 'NoneType' object has no attribute 'get'` when I try to add/edit/remove an effect!
Remember in the **Quick Start** when I said: 

DANGER: You must never, under any circumstances, delete this empty `ShadingRigProperties_{character name}`?

Well, this empty has been deleted. Yikes. Undo if you can. If that doesn't work- all you can do now to fix this is reset everything- remove any custom properties from any objects, delete all effects, effect materials, and export all objects into a new scene and new Blender file. Your current Blender file is permanently broken now. You can only move forward by resetting and moving your objects to a new file. 

## I try and add a correlation but I get the popup error `AttributeError: 'NoneType' object has no attribute 'get'`? 

See the previous answer. Your Blender file is permanently broken. Reset into a new file. 

## I try and do X but I get the popup error `AttributeError: 'NoneType' object has no attribute 'get'`? 

You deleted the undeletable empty. Your Blender file is permanently broken. Reset into a new file.


