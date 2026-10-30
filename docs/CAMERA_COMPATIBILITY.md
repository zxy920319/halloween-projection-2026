# Camera compatibility and M0 results

## Current status

**Pi 5 / Astra Pro Plus: `NOT_TESTED`.** This development environment is
Windows and has no access to the target Pi or camera. No driver, firmware, SDK,
or device stream has been tested. The mock path is not evidence of hardware
support.

Run on Raspberry Pi OS 64-bit, with the camera connected directly to the Pi:

```bash
bash scripts/pi_probe.sh
```

Save the terminal output locally and review it alongside the camera's USB
identity and the actual `/dev/video*` formats. Do not upload images or
child-related data. `v4l2-ctl`, `lsusb`, and `file` are read-only probe tools;
if missing, install only through a human-approved OS package operation. The
script itself never installs anything or requests `sudo`.

## Interpret results conservatively

- `aarch64` establishes the system architecture only; it does not prove a
  camera driver or SDK library can stream.
- A `/dev/video*` node does not prove it belongs to the Astra, supports a
  usable RGB format, or can sustain the target FPS.
- A listed SDK shared library does not establish that it is official, compatible,
  loadable, or able to access the device.
- Probe output cannot establish depth registration, synchronization, frame
  quality, night performance, or end-to-end latency.
- Orbbec SDK v2 support for Astra Pro Plus must not be assumed. Validate any
  old OpenNI2 path against official sources and the exact Pi OS/ARM64 setup.

## Evidence template

Record date, Pi model/OS/kernel, camera USB VID:PID, USB topology, video node
formats, SDK/library architecture and source, and the exact command/output for
each test. Mark streaming and RGB/depth separately as `PASS`, `BLOCKED_HARDWARE`,
or `NOT_TESTED`. Never infer device success from software installation alone.

### Current evidence

| Capability | Result | Evidence |
|---|---|---|
| Linux probe script | `MOCK_PASS` (static/script review only) | Not run on target Pi |
| Astra USB enumeration | `NOT_TESTED` | No Pi/camera access |
| RGB/V4L2 stream | `NOT_TESTED` | No Pi/camera access |
| OpenNI2/depth stream | `NOT_TESTED` | No Pi/camera access |
