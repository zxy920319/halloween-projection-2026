# Run book (Pi + desktop + Unity)

Commands below are the ones actually used for the working setup. Start order:
**desktop, then Pi, then Unity**. `100.83.94.65` is this setup's desktop address
(a Tailscale-range address); replace it with your own desktop IP.

## 1. Desktop (Windows PowerShell)

```powershell
cd <repo>
python -m desktop.main --host 100.83.94.65 --port 8765 --pose `
  --model .\models\pose_landmarker_lite.task --max-persons 3 --preview
```

- `--host` binds the frame receiver to that one interface only. Keep it off
  `0.0.0.0` and firewall inbound 8765 to the Pi.
- `--pose` publishes pose JSON on `ws://127.0.0.1:8766/poses` (loopback; Unity
  runs on the same PC).
- `--model` is a local official MediaPipe `.task` file in git-ignored `models/`.
  `pose_landmarker_full.task` is more accurate but slower than `lite`.
- `--max-persons` is 1, 2 or 3 (default 1).
- `--preview` shows a Tk window with the skeleton overlay. It does not record.

## 2. Raspberry Pi (SSH)

```bash
cd ~/halloween
python3 -m venv .venv && . .venv/bin/activate   # create once; activate in every new shell
cd halloween-projection-2026

python -m pi_agent.main --server ws://100.83.94.65:8765/frames \
  --backend v4l2 --device auto --width 640 --height 480 --fps 30
```

- `--server` must be the desktop address from step 1.
- `--device auto` picks the first USB node that offers MJPG; use `/dev/video0`
  to pin one. `--width/--height/--fps` are the capture mode (640x480@30 MJPG).
- Install dependencies once inside the venv: `pip install .`

## 3. Unity

Open the built player (or the Editor project) after the desktop is running:

```powershell
& "D:\Personal Projects\halloween-unity\unity.exe"
```

It connects to `ws://127.0.0.1:8766/poses` and reconnects automatically.
See [`UNITY_SETUP.md`](UNITY_SETUP.md) and [`PROJECTION_M5.md`](PROJECTION_M5.md).

## Expected output

- Desktop terminal: `pose fps=... persons=N` every ~2 s; preview status
  `pose ON | persons N | ms`.
- Pi terminal: connection and reconnect messages only.

## Notes

- Nothing is recorded or uploaded; frames stay in memory.
- If the Pi cannot connect, check the desktop is running first, that both
  machines share the network used by the IP above, and the firewall rule.
- Startup on boot: see [`DEPLOYMENT.md`](DEPLOYMENT.md).
