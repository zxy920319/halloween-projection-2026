# Test report

## Current implementation

- **M0**: probe script created. Script inspection only; target Pi test is
  `NOT_TESTED`.
- **M1**: mock frame source, binary protocol, WebSocket sender/receiver, newest
  frame queue, reconnect loop, smoke test, and unit/integration tests implemented.
  On Windows / Python 3.14.7, the current `python -m pytest -q` run passed 33
  tests with one real-model test skipped; an earlier
  `python scripts/smoke_test.py` reported `SMOKE_PASS`. `python -m compileall`
  passed. The local tests use generated frames, not a physical Pi or camera.
- **M2**: `BLOCKED_HARDWARE` pending Pi 5/Astra Pro Plus probe and real RGB stream.
- **M3**: MediaPipe inference adapter, 33-point pose schema, confidence
  filtering, preview, and short-gap association are implemented and covered by
  synthetic unit tests. No local `.task` model or Pi/test-video input was
  available; real-person inference is **NOT_TESTED**.
- **M4**: supplied rigged FBX prefab passed Unity 6000.6.7f1 batch validation
  for import, rig/skin/material, and synthetic 1/2/3-person pose driving.
  Blender export/visual inspection and live camera/WebSocket behavior remain
  **NOT_TESTED**.
- **M5**: Unity 6000.6.7f1 batch validation passed for projection controls,
  calibration grid, pose heartbeat, local action event/effect, and generated
  scene. Physical projector setup, live input, and site endurance remain
  **NOT_TESTED**.

No measured FPS, latency, depth accuracy, child tracking, or multi-person
reliability is claimed by mock tests.
