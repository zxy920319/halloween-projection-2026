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

4. Until a real adapter is implemented and hardware-verified, run only the
   explicit mock backend:

   ```bash
   python -m pi_agent.main --server ws://DESKTOP_LAN_IP:8765/frames --backend mock
   ```

No system packages, SDKs, firmware, or drivers are installed by project scripts.
Do not run a real-camera mode: V4L2 and Orbbec adapters intentionally report
unsupported.
