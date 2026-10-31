# Projection V2 — position-tracking skeleton

V2 shows **one** skeleton that is hidden until a person is tracked and then follows
the person's horizontal position (walk left → right in the camera = skeleton moves
left → right on screen). Height is fixed. V1 (`ProjectionCalibration.unity`,
`SkeletonPool`) is unchanged.

## Setup
1. Unity menu: **Halloween Projection → Build Calibration Scene V2 (Position Tracking)**
   creates `Assets/Scenes/ProjectionCalibrationV2.unity`.
2. Run the Pi/desktop pipeline as usual; no protocol or Python changes.

## Behavior (`Tracking.SkeletonPoolV2`)
- Hidden at start and after `lostTimeoutSeconds` (0.75 s) with no tracked person.
- Follows the highest-confidence `tracked` person and sticks to that `track_id`
  while present. `occluded` freezes the skeleton in place.
- X anchor: hips (23, 24), else shoulders (11, 12); mapped across the camera width
  minus `edgeMargin`, honoring `mirrored_input`, then smoothed (`smoothTime`).
- Limb pose still comes from `SkeletonPoseDriver`; `HandRaised` events are raised.
  (The particle `ProjectionEffectsController` is not added to the V2 scene.)

## Calibration tunables
`xOffset`, `xScale`, `invertX` (flip if movement direction is reversed),
`edgeMargin`, `smoothTime`, `lostTimeoutSeconds`.

## Validation
`Unity -batchmode -projectPath unity -executeMethod SkeletonPoolV2Validation.Run`
(result in `unity/Library/SkeletonPoolV2Validation-result.txt`).
