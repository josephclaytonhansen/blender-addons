# Shading Rig Quick Start
## Definitions
Shading Rig affects materials through **Effects**, which are connected to Lights through **Correlations**.

- **Effects** are empties that you use to art-direct your shading. They are the building blocks of your shading rig.
- **Correlations** define how Effects respond to lighting changes. A correlation connects a Light rotation to an Effect position and scale. 
## Panel Overview
Shading Rig is designed to be easy to use. However, it is a complex addon. Taking a moment to familiarize yourself with the panel will help you get a better workflow. The panel is arranged in the order in which you generally do things- move from top to bottom as you work on your shading rig.
<img src="../img/sr/start-panel.jpeg" width="250"/>

### Step 1: Set a Character Name
Let's start from scratch, with a blank file. 

In **Section 1**, the Settings sub-panel, you can set a character name and a default light. The character name is used to identify the shading rig- you'll need to set this first. For this example, I'm going to name my character "Sphere".

Once you set a character name, you can **Append Required Nodes**, and you'll have an empty added to your scene called `ShadingRigProperties_{character name}`:
<img src="../img/sr/character-name.jpeg" width="100%"/>

DANGER: You must never, under any circumstances, delete this empty `ShadingRigProperties_{character name}`. You're welcome to hide it or move it, but it's an essential component for getting multiple Shading Rigs to work in tandem.

You can set a light per effect, but if you want all the effects to use the same light, you can save a step by setting a default light here.

You now have a button in **Section 2** that says "Append Required Nodes" clickable. Click it! 😁

### Step 2: Append Required Nodes
You'll get a helpful notification: `Appended 4 node groups and 1 material(s).` 🤘🏻

### Step 3: Add an Object to Shade
Now that we have everything ready to go, I'm going to add a UV sphere and a light. I now have the option to **Set up Shading Rig on Object**: 
<img src="../img/sr/qsrw-1.jpeg" width="100%"/>

Click it!

Clicking this button adds a new material slot to your object and assigns a copy of the base material. This base material splits empty Effects and diffuse lighting into a hard shadow/lit area in black and white. For now, we're going to leave this material alone. You can learn more about modifiying this material or making Shading Rig work with your materials in the [Material Tricks](shading-rig-material-tricks.md) section.

### Step 4: Add Effects
Now, you will see something like this (assuming you have a light source):
<img src="../img/sr/qsrw-2.jpeg" width="100%"/>

In **Section 3**, the Effects list, you can add a new Effect by clicking the + button.

Effects are created at cursor location, so I'm going to click outside the sphere to make sure the Effect is outside the sphere. This will make it easier to find and move. 

Once you add an Effect, the panel will change: 
<img src="../img/sr/qsrw-3.jpeg" width="100%"/>

The **Active Effect Settings** control the parameters of your new Effect. We will go into detail about those in the [Effect Settings](shading-rig-edit-settings.md) section. For now, we want to actually see the effect on our sphere. Let's do that!

### Step 5: Add the Effect to the Material
In the panel at the bottom of the **Active Effect Settings**, you'll see **Select a set-up mesh object**. For us, this is our sphere. Let's select it and see what happens:
<img src="../img/sr/qsrw-4.jpeg" width="100%"/>

Shading Rig works best on roughly human-sized character, so if you're working on a correctly sized human, you probably won't see this.. Our sphere is a bit too big, so I'm going to scale it down until I see an **Add Effect to Material** button:
<img src="../img/sr/qsrw-5.jpeg" width="100%"/>

INFO: Don't worry about the object scale- it will be automatically applied when you **Add Effect to Material**.

Now, we see the button, but we can't click it. Hovering over the button tells us why — the empty needs to be closer to the object. The proximity of the empty to the object affects the size of the Effect. If it is too far away, the Effect will be too small to see. Let's move it closer, until we can click that button, which we will then click: 
<img src="../img/sr/qsrw-6.jpeg" width="100%"/>

Wow! The Effect!

You can start playing around with the Effect immediately — it updates in realtime. You can move it around, rotate it, scale it, and change the parameters in the **Active Effect Settings**. 

### Step 6: Add Correlations
In **Section 4**, the Correlations list, you have a + button. This adds a new correlation. Before you click it, though, here's how correlations work. 

When you click the + button, the current Light rotation and the current Effect position/scale are saved as a 1:1 pair. If you have two correlations, the Effect will move between the two positions as the light rotates between the two rotations. If you have more correlations, the Effect will move between all of them as the light rotates through all of them. 

This is much easier to demonstrate visually: 
<img src="../img/sr/two-correlations.gif" width="100%"/>

Although it is _not_ a driver-driven relationship, it does act like one. 

That's all you need to know to get started. For more advanced usage and settings, please continue through the documentation.