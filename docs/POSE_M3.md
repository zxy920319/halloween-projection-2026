# M3 — desktop pose inference

## Implementation

With the optional `pose` dependency installed, `desktop.pose.mediapipe_estimator`
uses MediaPipe Tasks Pose Landmarker in video mode and publishes the existing
version-1 `/poses` contract. It emits 33 normalized-image landmarks per accepted
person, filters low-confidence and implausible detections, smooths landmarks
per track, and returns `persons: []` when no detection is accepted. The
`--max-persons` option selects one, two, or three detections; the default is
one. Session-local IDs are associated by normalized bounding-box center across
detection reordering and short gaps (up to one second). These temporary IDs
are not identity recognition; crowded crossings and long occlusions still
need live testing and conservative tuning.

The local `--preview` window overlays the accepted skeleton and reports the
frame ID, dropped frames, person count, and inference time. Frames are processed
in memory and are not recorded.

## Run on a desktop receiving Pi frames

Install the optional dependencies and place an official MediaPipe Pose
Landmarker `.task` model at `models/pose_landmarker_lite.task`. The `models`
directory is intentionally git-ignored; do not commit model files or camera
footage. Model choices and setup are described in the
[MediaPipe Pose Landmarker Python guide](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python).

```powershell
python -m pip install -e ".[dev,pose]"
python -m desktop.main `
  --host 192.168.1.100 --port 8765 `
  --pose --model .\models\pose_landmarker_lite.task `
  --max-persons 1 --preview
```

Replace the example address with the desktop's trusted LAN IP and restrict the
firewall to the Pi. The Pi remains the camera-capture and JPEG-transport
device; do not connect the demo camera directly to the desktop as a substitute
for the project path. Unity connects to `ws://127.0.0.1:8766/poses`. Increase
`--max-persons` to two or three only after the corresponding live test.

Missing model files fail with an explicit path and setup hint. A synthetic
blank-image test does not prove that the model recognizes people.

## Verification record

- Unit tests cover the versioned pose JSON, normalized 33-point output,
  confidence/geometry filtering, person limit, detection-order association,
  short-gap recovery, track expiry, and invalid boxes.
- In this environment, the complete suite reported **41 passed, 1 skipped**.
  The skipped real-model test had no model file under `models/`. MediaPipe
  1.2.0 is installed, but no Pi RGB stream or consented local test video was
  available. Therefore real-person inference, live FPS, one/two/three-person
  tracking quality, and identity behavior under crossings remain **NOT
  TESTED**; M3 is implemented but field acceptance is pending.
