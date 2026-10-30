# Halloween Skeleton Mirror

The Raspberry Pi 5 remains in the camera-to-renderer path:

```text
Camera/mock on Pi 5 -> JPEG over LAN WebSocket -> desktop pose service -> Unity
```

The repository currently implements the **M0 software probe and M1 mock JPEG
transport**. No Raspberry Pi, Astra Pro Plus, projector, or Unity Editor was
available for this implementation, so hardware and Unity runtime behavior are
not claimed as verified.

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
| M2 real camera from Pi | `BLOCKED_HARDWARE` until Pi/Astra probe output is available |
| M3 pose inference | Protocol/interface groundwork only; no model inference implemented |
| M4 Unity renderer | Minimal track-based skeleton pool scaffold; Unity Editor not available |

The `persons[]` pose schema and Unity track registry are scaffolding, not
implemented multi-person identity tracking. Follow the remaining milestones in
`PROJECT_SPEC.md`.
