# Raspberry Pi setup

Use Raspberry Pi OS 64-bit on a Pi 5. Connect the selected camera to the Pi;
the architecture intentionally does not route capture directly to the desktop.

1. Copy/clone this repository onto the Pi and inspect `docs/CAMERA_COMPATIBILITY.md`.
2. Run `bash scripts/pi_probe.sh` before attempting a real camera adapter.
3. Install Python 3.11+ and this project in a virtual environment using the
   package manager/process approved for the device:

   ```bash
   python3 -m venv .venv
   . .venv/bin/activate
   python -m pip install .
   ```

4. Run the V4L2 camera backend (MJPG passthrough, verified on Pi 5 with the
   Astra Pro Plus RGB sensor); use `--backend mock` for a camera-free test:

   ```bash
   python -m pi_agent.main --server ws://DESKTOP_IP:8765/frames --backend v4l2 --device auto --width 640 --height 480 --fps 30
   ```

   See [`RUNBOOK.md`](RUNBOOK.md) for the full start sequence.

No system packages, SDKs, firmware, or drivers are installed by project scripts.
The Orbbec/OpenNI2 depth backend still reports unsupported.
