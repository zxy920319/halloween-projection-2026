# Unity Halloween skeleton integration

This folder contains the protocol-compatible Unity scripts, Blender source,
and rigged, anatomically detailed 1.8 m skeleton model inspired by the
reference's front, side, and back views. The model includes an articulated
skull, full rib cage, vertebral column, pelvic ring, hands, and feet. To
regenerate the model files from the repository root:

```powershell
blender --background --python .\unity\Blender\generate_halloween_skeleton.py -- --out .\unity\Assets\Models
```

The generator writes `HalloweenSkeleton.blend`, `.fbx`, and `.glb`. It checks
that every mesh vertex has one 1.0 bone weight and runs a Blender arm-pose
deformation smoke test before saving/exporting. An FBX export error is fatal.
Open the `.blend` in Blender and inspect the Armature modifier, matching vertex
groups, and `LeftUpperArm` / `LeftLowerLeg` in Pose Mode as a visual check.

The supplied FBX is in `Assets/Models/HalloweenSkeleton.fbx`; the matching
`Assets/Prefabs/SkeletonCharacter.prefab` has the model and pose driver wired
with stable `.meta` references. Copy `Assets/Scripts`, `Assets/Models`, and
`Assets/Prefabs` into a Unity LTS project (2022.3+; Unity 6 is also suitable).
Copy `Assets/Editor` too if you want to run the batch validation.
Set the FBX Rig to **Generic**. Assign up to three prefab instances to
`SkeletonPool`; keep `PoseReceiver` and `PoseWebSocketClient` connected as
before. The pool prefers the pose driver and falls back to `SkeletonDrawer`
for roots without a rig. Do not add an Animator that writes to the same bones.

The retargeter uses normalized-image x/y landmarks for a basic 2.5D limb pose;
it is not calibrated 3D IK. `mirrorInput` is an additional per-character
horizontal flip and is combined with the message's existing `mirrored_input`
flag. The WebSocket endpoint and JSON schema are unchanged. See
`../docs/UNITY_SETUP.md` for the full import and verification procedure.

`Assets/Editor/SkeletonPoolValidation.cs` provides a batch-mode Unity check
for FBX rig/skin/material import, prefab creation, and synthetic 1/2/3-person
pool-driven poses. Its exact results and the Blender/Play Mode validation
limits are recorded in `../docs/UNITY_SETUP.md`.

M5 adds the generated `Assets/Scenes/ProjectionCalibration.unity` scene,
`Assets/Scripts/Projection`, local raised-hand effects, projection heartbeat,
and matching Pi/Windows restart examples. In play mode use **M** to toggle
optical mirroring, **C** to show/hide the alignment grid, and **F** to toggle
fullscreen. See `../docs/PROJECTION_M5.md` for setup, operations, and the
physical projector latency/release checklist.
