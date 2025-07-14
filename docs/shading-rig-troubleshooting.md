# Troubleshooting
## Why am I not seeing an effect? 
### Reset Rotation
The most common problem I've encountered as people test this is that the Effect isn't showing. In 99% of cases I've observed, the problem is with **rotation** of the empty controlling the Effect. The first thing you should when troubleshooting is **reset the rotation of the Empty** (you can do this with Alt + R):
[<img src="../img/sr/qsrw-10.gif" width="100%"/>](img/sr/qsrw-10.gif)
Here, my Effect was not showing up. I reset the rotation, and it shows up. 
### Check Distance from Object
If that doesn't do it, move the empty closer to your object. The distance from the object matters:
[<img src="../img/sr/qsrw-11.gif" width="100%"/>](img/sr/qsrw-11.gif)
Keep your edits close to your object for best results. 
### Check Parameters
Increase the Hardness. At lower values, the Effect may not always show up.
### Did you change, disconnect, or rename something in the shader? 

WARNING: Don't!

There are things you can play with in the shader and **things you cannot**. Anything between the two red **Do not touch this!** frames, you must not alter in any way!

[<img src="../img/sr/touch-this.png" width="100%"/>](img/sr/touch-this.png)
[<img src="../img/sr/touch-this2.png" width="100%"/>](img/sr/touch-this2.png)

You can change, modify, rename, or do whatever with the **You Can Touch This** nodes. You cannot in any way alter the red **Do not touch this!** node after it. Don't look at it. Don't think about it. Purge it entirely from your mind and memory. If you modify one of these forbidden nodes or any of the nodes in between the two forbidden nodes, *you will break everything permanently.* The only way to fix this is to manually remove these nodes, delete the Effect, and recreate it. 

One last time, just for safety: **don't touch anything between and including red Do Not Touch This! nodes!!**





