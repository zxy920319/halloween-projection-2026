# Test report

## Current implementation

- **M0**: probe script created. Script inspection only; target Pi test is
  `NOT_TESTED`.
- **M1**: mock frame source, binary protocol, WebSocket sender/receiver, newest
  frame queue, reconnect loop, smoke test, and unit/integration tests implemented.
  On Windows / Python 3.14.7, `python -m pytest -q` passed 13 tests;
  `python scripts/smoke_test.py` reported `SMOKE_PASS`; `python -m compileall`
  passed. The local tests use generated frames, not a physical Pi or camera.
- **M2**: `BLOCKED_HARDWARE` pending Pi 5/Astra Pro Plus probe and real RGB stream.
- **M3/M4/M5**: not complete; no inference/model, complete Unity renderer,
  projector setup, or site run is claimed.

No measured FPS, latency, depth accuracy, child tracking, or multi-person
reliability is claimed by mock tests.
