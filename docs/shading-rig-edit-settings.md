# Effect Settings
Setting up an Edit gives you a circular effect, which is nice, but you probably will want more control and complexity fairly quickly. Each Edit can be customized to exactly what you need.

## Parameters
You'll want to combine these parameters to create the effect you want, most effects require altering all of these parameters.

### Elongation
[<img src="../img/sr/sr-elongation.gif" width="100%"/>](img/sr/sr-elongation.gif)
Elongation changes the width to height ratio of the Edit. 

NOTE: In the original paper, this is referred to as Anisotropy. However, it's not actually Anisotropy, and Elongation felt more accurate. 

### Sharpness
[<img src="../img/sr/sr-sharpness.gif" width="100%"/>](img/sr/sr-sharpness.gif)
Sharpness "puckers" the horizontal corners of the Edit, or draws them as sharp corners. 

INFO: Positive Elongation combined with Sharpness creates a wide diamond shape. 

### Hardness
Hardness changes the way the Edit blends with other shading. An Hardness of 1 means the Edit will have hard edges and move like a decal. A lower hardness means the Edit will blend with the shading more, creating a smooth effect not unlike what you see with SDF modeling or metaballs. It's difficult to describe, so please compare and contrast what happens when this Edit is moved with an hardness of .1, .3, and 1:
[<img src="../img/sr/sr-hardness.gif" width="100%"/>](img/sr/sr-hardness.gif)

For hard highlights or shadows, such as a "eyelight", Rembrandt triangle, or an under-nose shadow, you will want a higher value. For more generalized shading, a lower value will work better. 

### Bulge
[<img src="../img/sr/sr-bulge.gif" width="100%"/>](img/sr/sr-bulge.gif)
Bulge thickens one end of the Edit, creating a pear-shaped effect. 

NOTE: Bulge applies along a diagonal access. You can use Rotation to correct this. 

### Bend
Bend thickens the effect similar to Bulge, but it applies on the opposite diagonal axis.
[<img src="../img/sr/sr-bend.jpeg" width="100%"/>](img/sr/sr-bend.jpeg)
It's very difficult to explain Bulge and Bend, but they work well in combination to create a variety of effects. For example:
[<img src="../img/sr/sr-bulge-and-bend.jpeg" width="100%"/>](img/sr/sr-bulge-and-bend.jpeg)

### Rotation
Rotates the effect's effect.

## Edit Settings
[<img src="../img/sr/edit-settings.jpeg" width="100%"/>](img/sr/edit-settings.jpeg)
The first three fields are for the empty object, light object, and affected material. 
### Empty Object
Here you can change the empty object that the Edit uses. There's not generally a reason why you would do this, but you can.
### Light Object
An Edit is tied to the rotation of one Light. If a specific light is not set, this field will automatically fill with the default light set in the Settings sub-panel. If you set a specific light, the Edit will instead respond to that light's rotation. 
### Material
An Edit affects one Material. This way, you can have multiple materials affected by Edits. 

WARNING: You probably should avoid changing this unless you have a specific reason to do so. The better workflow is to **Set Up Shading Rig on Object**, which will automatically set the material for you. However, if you need multiple effected materials per object, this will be useful.

Note that if you change the material, you need to re-attach the Edit to the material. Click **Add Edit to Material** to do this. 
### Display Type
This sets the viewport display shape of the Edit's empty. 

### Parent Object
In order for an Edit to properly work on a character, it needs to track the character's rotation and position. I've provided the functionality to do this without breaking Correlations here- just set the Parent Object to the character's object. 

WARNING: Please don't parent an Edit directly to something- it won't work and you will be sad. Use the Parent Object field to set up this relationship exclusively. 

### Renaming an Edit
You can double-click on an Edit in the effects list to rename it.

### Removing an Edit
Click the - button while an Edit is selected in the effects list to remove it.