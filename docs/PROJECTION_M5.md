# M5 — projection, effects, and runtime operations

## What is included

- `unity/Assets/Editor/ProjectionSceneBuilder.cs` creates
  `unity/Assets/Scenes/ProjectionCalibration.unity`, a black-background,
  orthographic projection scene with a projection camera, a calibration grid,
  the existing pose receiver/WebSocket client, the three-character skeleton
  pool, pose effects, and a runtime monitor. From Unity, run
  **Halloween Projection > Build Calibration Scene**.
- `ProjectionDisplayController` targets a selected Unity display, keeps the
  camera clear color black, supports optional fullscreen startup, and exposes
  runtime keyboard controls: **M** horizontal optical mirroring, **C**
  calibration grid, and **F** fullscreen. Mirror output is performed by
  flipping the camera projection and restoring render culling state around
  that camera's render. Set the physical projector as the extended display
  before launch; `targetDisplay` defaults to Unity Display 0.
- `ProjectionCalibrationGrid` draws a frame, center axes, and a 10-division
  screen-aligned grid. Use it to align the projected image with the actual
  reflective surface; this is a visual aid, not automatic keystone correction.
- `SkeletonPool` derives a rising-edge `HandRaised` event from the existing
  normalized-image wrist/shoulder landmarks. `ProjectionEffectsController`
  emits a small orange particle burst for that character. No action fields or
  other changes are made to the WebSocket protocol. Detection can be tuned
  with `actionMinVisibility` and `raisedHandMargin` in the pool Inspector.
- `PoseReceiver` exposes the count, ID, and local receipt time of accepted pose
  frames. `ProjectionRuntimeMonitor` logs connection transitions, stale-feed
  warnings, and periodic heartbeat/frame-age summaries. These are local
  receipt metrics; they are not camera exposure or photon/display timestamps.
- Restart examples: `deploy/pi/halloween-pi.service` for the Pi sender and
  `deploy/windows/Register-HalloweenDesktopTask.ps1` for the Windows desktop
  receiver/publisher.

## Scene and machine setup

Copy the `unity/Assets` scripts, FBX, prefab, and `.meta` files into the Unity
project, then copy `unity/Assets/Editor` as well. Open the generated
`ProjectionCalibration` scene. In Player Settings choose the intended display
resolution. Connect the projector as an extended display and check which Unity
Display number it maps to before changing `targetDisplay`. Run with the
calibration grid on; align the projected frame and center axes, then press **C**
to hide the grid and **M** to select the required optical reflection direction.
Press **F** to toggle fullscreen. The default scene starts windowed, unmirrored,
and with the calibration grid hidden so setup does not unexpectedly take over
the operator display.

Use the Pi unit after installing the repository and its virtual environment at
`/opt/halloween-projection`, creating a restricted `halloween` service account,
and editing the desktop IP in `ExecStart`. The unit selects V4L2 explicitly;
it does not silently claim Astra/OpenNI support. Install it with an operator
review:

```bash
sudo cp deploy/pi/halloween-pi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now halloween-pi.service
systemctl status halloween-pi.service
journalctl -u halloween-pi.service -f
```

On Windows, run `deploy/windows/Register-HalloweenDesktopTask.ps1` from an
elevated PowerShell session after installing the project in a stable directory.
Pass the project root, its virtual-environment `python.exe`, and the locally
provided MediaPipe model path. The default bind address is loopback-only; for
the Pi to connect, pass the desktop's trusted-LAN address and restrict the
firewall to the Pi. The pose publisher remains on loopback for Unity on the
same desktop.

```powershell
.\deploy\windows\Register-HalloweenDesktopTask.ps1 `
  -ProjectPath C:\HalloweenProjection `
  -PythonPath C:\HalloweenProjection\.venv\Scripts\python.exe `
  -PoseModelPath C:\HalloweenProjection\models\pose_landmarker_full.task `
  -BindAddress 192.168.1.100
Start-ScheduledTask -TaskName HalloweenProjectionDesktop
Get-ScheduledTaskInfo -TaskName HalloweenProjectionDesktop
```

The desktop launches `python -m desktop.main --pose`; it must have the optional
MediaPipe dependency installed and the local model file available. The M5
Unity scene alone does not provide pose inference. Keep images and model files
local; the example services do not enable recording or cloud upload.

## Latency and release validation

The Unity heartbeat reports the age of the last accepted pose message and
frame-ID progress. `server_monotonic_ns` is written by the desktop pose
estimator, so comparing it to Unity's monotonic clock can estimate desktop
pose-generation-to-Unity-receipt latency **on the same desktop**. It does not
include Pi capture-to-desktop transport, projector scanout, or photons reaching
the screen; do not subtract unrelated machine monotonic clocks.

For end-to-end testing, temporarily place a timestamped LED or visual timecode
in the camera's field of view and photograph both the physical motion/indicator
and projected response with a high-speed camera. Record at least 100 samples
after warm-up and report median, p95, maximum, dropped frames, tested
resolution/refresh rate, network path, and camera/pose settings. Repeat with
one person and with the intended projector mirror setting. Do not retain or
commit identifiable people footage without the required consent; aggregate
timings can be recorded in the release log. Measure at least a 30-minute
continuous run for initial acceptance and a two-hour on-site run before release.

## Verification record

The Unity **6000.6.7f1 batch-mode M5 validation passed** in the temporary
validation project: black background/display selection, horizontal mirror
projection, grid visibility, accepted-pose heartbeat fields, a deduplicated
raised-hand event, its particle effect, and calibration-scene generation.
Unity batch mode is not a physical projector test. No Blender executable was
available to run the asset generator or visually inspect the `.blend`; the
checked-in FBX was tested in Unity as supplied. No projector, reflective film,
Pi/Astra live feed, human motion test, 30-minute run, or end-to-end latency
measurement was available in this environment; those release checks remain
**NOT TESTED**.
