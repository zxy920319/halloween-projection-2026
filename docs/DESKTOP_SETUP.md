# Desktop setup

Install Python 3.11+ and the project dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Loopback-only local mock run:

```powershell
python -m desktop.main --host 127.0.0.1 --port 8765 --preview
python -m pi_agent.main --server ws://127.0.0.1:8765/frames --backend mock
```

For a separate Pi, bind the desktop server only to its trusted LAN address:

```powershell
python -m desktop.main --host DESKTOP_LAN_IP --port 8765
```

Restrict inbound firewall access to the Pi's reserved address before using
unauthenticated `ws://` on the LAN. Do not expose port 8765 publicly. Set the
Pi sender's `--server` URL to `ws://DESKTOP_LAN_IP:8765/frames`.

`--preview` uses Tk and Pillow, displays in memory, and does not record frames.
The working start command with pose is in [`RUNBOOK.md`](RUNBOOK.md).
Optional pose inference requires the `pose` extra and a locally supplied
official MediaPipe Pose Landmarker `.task` model. See
[`POSE_M3.md`](POSE_M3.md) for installation, startup, and model guidance.
