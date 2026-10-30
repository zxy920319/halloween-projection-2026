# Architecture and milestone status

The required capture path is preserved: a camera is connected to the Raspberry
Pi 5; the Pi captures/encodes frames; the desktop performs inference and
rendering. The current mock sender substitutes generated frames **on the Pi
side of that boundary** and does not provide a camera bypass architecture.

## M0/M1 implementation

- `scripts/pi_probe.sh`: read-only Linux/USB/V4L2/Python/SDK-library inspection.
- `pi_agent.camera.CameraSource`: source contract; the mock source is implemented.
- `shared.protocol`: versioned 4-byte length prefix + JSON metadata + JPEG packet.
- `pi_agent.main`: WebSocket sender, health packet, bounded exponential reconnect.
- `desktop.ingest`: binary packet validation, monotonic frame ID check, one-slot
  drop-old queue.
- `desktop.preview`: optional local in-memory preview; no image persistence.
- `desktop.pose`: optional MediaPipe Tasks inference, confidence/geometry
  filtering, 33-landmark output, per-track smoothing, and short-gap association
  by normalized bounding-box center. IDs are temporary session-local labels,
  not persistent identity recognition.
- `unity/Assets/Scripts/Tracking`: a three-slot skeleton pool and track-to-slot
  registry preserve character slots while track IDs remain active. This is a
  prototype seam, not proof of reliable identity through crossings or occlusion.

The desktop binds to loopback by default. For two physical devices, select the
desktop's trusted LAN interface explicitly, restrict its inbound firewall rule
to the Pi address, then set the Pi `--server` URL to that interface. The initial
prototype uses unauthenticated `ws://` and must remain on a trusted LAN; do not
port-forward or expose it to the Internet. Use a protected VPN/WSS plus device
authentication on untrusted networks.

## Boundaries

V4L2 and Orbbec/OpenNI2 are explicit unsupported adapters, not silent fallback
paths. A successful mock test does not establish Astra Pro Plus, RGB, depth,
ARM64 SDK, timing, real-person pose inference, projector, or site compatibility.
Synthetic tests cover protocol/schema behavior and selected multi-person
ordering and short-gap cases; they do not establish tracking quality under
crossings, occlusion, changing lighting, or a live camera stream. See
`docs/VALIDATION_REPORT.md` for current evidence and boundaries.
