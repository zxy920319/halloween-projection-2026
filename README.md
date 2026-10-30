# Halloween Skeleton Mirror

The Raspberry Pi 5 remains in the camera-to-renderer path:

```text
Camera/mock on Pi 5 -> JPEG over LAN WebSocket -> desktop pose service -> Unity
```

The repository implements the **M0 software probe and M1 mock JPEG transport**
and includes M4/M5 Unity assets and synthetic batch validations. Unity 6 batch
mode was available, but no Raspberry Pi, Astra Pro Plus, or physical projector
was available; hardware behavior is not claimed as verified.

## Requirements

- Python 3.11 or newer
- Install both components: `python -m pip install -e ".[dev]"`

The Pi transport and desktop receiver use `websockets`; mock frames use Pillow.
No camera SDK or model is downloaded automatically.

## Run a local M1 mock loop

Terminal 1 (desktop receiver):

```powershell
python -m desktop.main --host 127.0.0.1 --port 8765
```

Terminal 2 (Pi mock sender; same process/network simulation, no camera access):

```powershell
python -m pi_agent.main --server ws://127.0.0.1:8765/frames --backend mock
```

Use `--preview` on the desktop command to open a local Tk preview window.
`--host 0.0.0.0` is intentionally not the default; bind to a trusted LAN
interface only after restricting access with the host firewall.

Run the automated checks:

```powershell
python -m unittest discover -s tests -v
python scripts/smoke_test.py
```

To check desktop TCP reachability from the Pi without sending frame data:
`python scripts/check_network.py DESKTOP_LAN_IP --port 8765`.

## Raspberry Pi camera probe

On the Pi 5, run the read-only probe:

```bash
bash scripts/pi_probe.sh
```

It does not install packages, change drivers, or alter firmware. See
`docs/CAMERA_COMPATIBILITY.md` before interpreting its output.

## Current milestones

| Milestone | State |
|---|---|
| M0 probe script and compatibility reporting | `MOCK_PASS` for script inspection; actual Pi probe `NOT_TESTED` |
| M1 mock JPEG framing, WebSocket ingest, drop-old queue, reconnect | Local automated checks; no physical two-device test |
| M2 real camera from Pi | `NOT_TESTED` until Pi/Astra probe output and a real RGB stream are available |
| M3 pose inference | MediaPipe Tasks adapter, 33-point output, confidence filtering, preview, and short-gap ID association implemented; unit tests pass. No model file or Pi/test-video stream available for real-person validation |
| M4 Unity renderer | Supplied rigged FBX prefab and 3-slot pose driver; synthetic Unity 6 batch validation passed. Blender export, live human/WebSocket test not performed |
| M5 projection | Calibration scene, mirror controls, local pose effects, health heartbeat, and restart examples implemented; projector and 30-minute field acceptance not tested |
| M6 two-person tracking | Prototype association and three-slot Unity registry/layout are implemented. Synthetic ordering and short-gap tests pass; live crossings, occlusion, and identity acceptance remain `NOT_TESTED` |
| M7 three-person mode | Three-person software capacity is configurable, but tracking quality and site feasibility remain `NOT_TESTED` |

Real-person pose inference and robust identity tracking still require a local
official MediaPipe model and Pi RGB or compliant test-video validation.
`track_id` is temporary and not a production multi-person identity tracker.
The M4/M5 Unity checks use synthetic pose frames; the projector, Pi camera,
human movement, and end-to-end optical latency still require field validation.
See `docs/POSE_M3.md` and the remaining acceptance steps in `PROJECT_SPEC.md`.
