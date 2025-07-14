# Correlations
## Editing Correlations 
Once a correlation is added, you can change the values manually if you want. Turn off **Read-Only Correlations** in the panel settings (which is on by default), select a correlation, and you can change the values in the lowest panel.
[<img src="../img/sr/correlations-panel.jpeg" width="250"/>](img/sr/correlations-panel.jpeg)

## Renaming Correlations
Double-click a correlation in the list to rename it.

## Correlation Limits
There is no limit to the number of correlations you can have per effect. That said, the higher the amount, the less smooth the interpolation will be. With two correlations, the Effect will move smoothly along a line between two points. With three, it will gracefully curve around a triangle. At numbers higher than 3, you run the risk of overlap, which will cause the Effect to jump around in unexpected ways. That is to say- if you visualize the Effect positions as points in space, vertices of an n-gon, the n-gon will either be manifold (no crossing/overlapping edges) or non-manifold:
 [<img src="../img/sr/hexagons.jpeg" width="250"/>](img/sr/hexagons.jpeg)

INFO: If this is hurting your head, don't worry about it. Just know that the higher the number of correlations, the higher the risk of the Effect jumping erratically. 

Generally, I find that 3-6 correlations works best. Your case may vary, but if your Effects are jumping around, consider using less correlations.

## How do correlations work?
Earlier I said:
> If you have two correlations, the Effect will move between the two positions as the light rotates between the two rotations. If you have more correlations, the Effect will move between all of them as the light rotates through all of them. 
This is true, but it's a surface level explanation. Understanding how the effects move will help you better predict where they will be when the light is at a certain rotation. 

INFO: If you're not interested in the details, that's fine. All you need to know about correlations is this: rotate the Light. Move and scale the Empty (Effect). Add a Correlation. Do it again repeatedly. Click the - button to remove a correlation. 

## The Math and the Nitty-Gritty
The basic idea is that given a list of light rotations -> empty positions and a current light rotation, we need to interpolate the empty position. This is a **weighting** problem, not dissimilar to how bones interact with vertex groups. It helps to think of this as two triangles. Given 3 correlations, A, B, and C, there is a Light Rotation triangle with points A, B, and C, and an Empty Position triangle with points A, B, and C. (Because the light rotation is just a 3D vector, it can be mapped into space as a triangle just the same as the position.)

Let us say the current light rotation is Point N, represented by this black dot: 
[<img src="../img/sr/cor-triangles.jpeg" width="250"/>](img/sr/cor-triangles.jpeg)

We can easily visually see where the correlation is for Point N in the Empty position triangle. As N is nearly halfway between A and B, and point N is nearly at B and far from C, the Empty point N should also be nearly halfway between A and B, and nearly at B and far from C. 

The above triangles are identical. What if they're not? We can still visually interpolate the position of N in the Empty triangle with a similar process: 
[<img src="../img/sr/cor-triangles-2.jpeg" width="250"/>](img/sr/cor-triangles-2.jpeg)

What we're doing visually here is what's being done mathematically, just with normalized inverse distance weights and "n-gons" instead of "triangles" (truly, there's no visual elements involved at all.) 

Since we're also storing the scale, this is technically interpolating between a set of 3D vectors and a set of 4D vectors, but that's impossible to visualize.