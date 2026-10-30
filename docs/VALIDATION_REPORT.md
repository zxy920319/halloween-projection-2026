# Validation report

| Area | Status | Evidence / boundary |
|---|---|---|
| Protocol and mock frame logic | `MOCK_PASS` | `python -m pytest -q`: 41 passed, 1 skipped; `python scripts/smoke_test.py`: `SMOKE_PASS`; synthetic frames only |
| Pi 5 / Astra USB and RGB | `NOT_TESTED` | No target hardware available |
| Astra depth/OpenNI2 on Pi ARM64 | `NOT_TESTED` | No target hardware or verified SDK |
| Pose pipeline software | `MOCK_PASS` | Synthetic/fake-landmarker tests cover schema, filtering, 33-point output, and person limit; model-dependent test skipped because no local model is present |
| Real-person pose inference | `NOT_TESTED` | No local model plus Pi RGB stream or compliant test-video validation |
| Multi-person association software | `MOCK_PASS` | Synthetic tests cover count sequence 0→1→2→3→2→1→0, detector reordering, walking crossing without ID swap, ambiguity → `occluded`, exit/re-entry, and the three-person limit; heuristic uses velocity-predicted bounding-box center distance |
| Live two-person identity acceptance (M6) | `NOT_TESTED` | No live camera/Unity run; crossing, occlusion, and identity-switch behavior unverified |
| Three-person site acceptance (M7) | `NOT_TESTED` | No three-person camera-coverage, quality, or field test |
| Unity rendering/retargeting | `MOCK_PASS` | Unity 6000.6.7f1 batch-mode validation is documented in `PROJECTION_M5.md`; synthetic poses only, not a live human/WebSocket test |
| Projection/site/latency/30-minute run | `NOT_TESTED` | No installed site or projector; no end-to-end optical latency or endurance measurement |

The Python checks were run in this Windows environment with Python 3.14.7.
`python -m unittest discover -s tests -v` also passed (20 tests), and the
repository's documented smoke test passed. Do not change any field test to
`PASS` without a reproducible command, environment, and evidence. Synthetic
tests must remain labeled `MOCK_PASS`.
