# Unity rigged skeleton setup

The existing `PoseModels.cs`, `PoseReceiver.cs`, and `PoseWebSocketClient.cs`
remain the transport path. `PoseFrame` / `TrackedPerson` are unchanged; the
`SkeletonPool` still assigns tracked `track_id` values to at most three slots.
It now prefers `SkeletonPoseDriver` and retains `SkeletonDrawer` as a debug
fallback.

## Generate and inspect the Blender asset

From the repository root, run Blender 3.6+:

```powershell
blender --background --python .\unity\Blender\generate_halloween_skeleton.py -- --out .\unity\Assets\Models
```

The output includes `HalloweenSkeleton.blend` and `HalloweenSkeleton.fbx` (and
a GLB when the installed Blender exporter supports it). Generation validates
the armature parent/modifier, checks every mesh vertex has exactly one weight
of 1.0 mapped to a rig bone, and rotates `LeftUpperArm` to verify the evaluated
mesh deforms. The generator fails if the FBX export fails.

Open the `.blend` and visually confirm `HalloweenSkeleton_Rig`,
`HalloweenSkeleton_SkinnedMesh`, the `Armature_Skin` modifier, and the vertex
groups. In Pose Mode, rotate `LeftUpperArm` and `LeftLowerLeg`; the corresponding
geometry should follow.

## Import into Unity

This repository is a Unity asset scaffold, not a complete Unity project. Copy
`unity/Assets/Scripts`, `unity/Assets/Models`, and `unity/Assets/Prefabs` into an
existing project, preserving the `.meta` files. To run the included validation,
also copy `unity/Assets/Editor`. The supplied
`SkeletonCharacter.prefab` contains the FBX instance and a
`SkeletonPoseDriver` whose `Rig Root` references that instance. Set the FBX Rig
to **Generic** (the checked-in importer settings already do this). Do not put an
Animator on the same rig unless it is intentionally coordinated with this
driver.

Assign up to three instances of `SkeletonCharacter.prefab` to
`SkeletonPool.skeletonRoots`. Assign the pool to `PoseReceiver`, then assign
the receiver to `PoseWebSocketClient`. The WebSocket URL and pose JSON
protocol are unchanged. The driver maps normalized-image landmark x/y
directions to the arms, legs, and approximate spine; it is a 2.5D prototype,
not a calibrated 3D retargeter. Its `mirrorInput` setting is combined with the
frame's existing `mirrored_input` metadata.

## Reproducible Unity validation

After copying the assets into a Unity project, run this Editor validation with
Unity installed:

```powershell
& "C:\Program Files\Unity\Hub\Editor\6000.6.7f1\Editor\Unity.exe" `
  -batchmode -nographics -projectPath . `
  -executeMethod SkeletonPoolValidation.Run -quit `
  -logFile .\skeleton-validation.log
```

`Assets/Editor/SkeletonPoolValidation.cs` sets the FBX to Generic if needed,
checks the required bone names, a skinned renderer with imported weights, and
the red `Cursed_Red_Eyes` material; then it creates/updates
`Assets/Prefabs/SkeletonCharacter.prefab`. It feeds synthetic normalized-image
frames to the real pool and imported rig, checking arm movement and independent
rotations for 1, 2, and 3 people, slot placement, and hiding unused characters.
The result is written to `Library/SkeletonPoolValidation-result.txt`.

## Verification status

The local environment did not have a Blender executable, so the generator was
not run here and the `.blend` was not opened for a Blender Pose Mode visual
check. The supplied Milestone 4 `.blend`, `.fbx`, and `.glb` files were
included as provided; the Unity FBX import was tested against that supplied
FBX, not a newly exported model.

Unity **6000.6.7f1** batch validation passed in a temporary Unity project:
33 imported transforms, 1 `SkinnedMeshRenderer`, 3 materials, the expected
body bones, and a red `Cursed_Red_Eyes` material assigned to the skinned mesh.
Every imported vertex passed the one-valid-bone-weight, weight-sum-1.0 check.
Unity created the Generic-rig `SkeletonCharacter` prefab and bound all 9/9
pose segments on each of three instances. The editor smoke test passed
single-person arm movement, distinct 1/2/3-person arm rotations, pool slot
positions, and hiding unused characters. This was an Editor batch smoke test
with synthetic pose frames, not a live WebSocket/camera or visual Play Mode
test.

The M5 calibration scene, optical-mirror controls, local pose-event effects,
heartbeat, restart examples, and physical projector test limits are documented
in `PROJECTION_M5.md`.
