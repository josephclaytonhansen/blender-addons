# Shading Rig Features

## Customize light and shadow exactly how you want it
[<img src="../img/sr/srf-1.png" width="100%"/>](img/sr/srf-1.png)

## What is Shading Rig?
> Shading Rig is a new framework for art-directing dynamic 3D toon shading, both on static and animated objects. It lets artists add illustrative details and animate how those details respond to lighting changes in real time...  we achieve this with a "rig" of shadow editing primitives designed based on fundamental artistic shading principles. These primitives can be animated to achieve highly stylised shading under dynamic lighting.

> [Lohit Petikam et al.](https://lohit.dev/ShadingRig/)

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/-gr0a0wAI5E?si=qCk0PBxgy472h7OQ" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

At Real-Time Live! SIGGRAPH 2021, Lohit Petikam and his team presented a shader rig for cel shaded characters.  However, this presentation was almost entirely theory and lacked technical or practical implementation. A functional implementation has never been made until now. I've both _implemented_ and _improved_ the original ideas presented in the paper, approaching it from an art direction perspective and coming up with creative solutions to make sure it is production-ready. Much of the math in the paper didn't end up working outside of specific test cases, so I've significantly reworked major portions. The final result is wholly unique and extremely powerful.

## Automatic smooth blending for a more natural look
[<img src="../img/sr/sr-hardness.gif" width="100%"/>](img/sr/sr-hardness.gif)

## Shape effects with precision
[<img src="../img/sr/srf-2.png" width="100%"/>](img/sr/srf-2.png)