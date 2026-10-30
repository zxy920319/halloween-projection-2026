# Validation report

| Area | Status | Evidence / boundary |
|---|---|---|
| Protocol and mock frame logic | `MOCK_PASS` | 13 tests pass on Windows / Python 3.14.7; synthetic frames only |
| Pi 5 / Astra USB and RGB | `NOT_TESTED` | No target hardware available |
| Astra depth/OpenNI2 on Pi ARM64 | `NOT_TESTED` | No target hardware or verified SDK |
| One-person pose tracking | `NOT_TESTED` | Inference not implemented |
| Two-person tracking | `NOT_TESTED` | Identity association not implemented |
| Three-person tracking | `NOT_TESTED` | Identity association not implemented |
| Unity rendering/retargeting | `NOT_TESTED` | Scaffold only; no Unity Editor |
| Projection/site/latency/30-minute run | `NOT_TESTED` | No installed site or projector |

Do not change a status to `PASS` without a reproducible command, environment,
and evidence. Synthetic tests must remain labeled `MOCK_PASS`.
