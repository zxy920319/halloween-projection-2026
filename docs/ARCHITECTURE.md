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
- `desktop.pose`: future inference interface and session-only ID allocation;
  neither implements detection or person association.

The desktop binds to loopback by default. For two physical devices, select the
desktop's trusted LAN interface explicitly, restrict its inbound firewall rule
to the Pi address, then set the Pi `--server` URL to that interface. The initial
prototype uses unauthenticated `ws://` and must remain on a trusted LAN; do not
port-forward or expose it to the Internet. Use a protected VPN/WSS plus device
authentication on untrusted networks.

## Boundaries

V4L2 and Orbbec/OpenNI2 are explicit unsupported adapters, not silent fallback
paths. A successful mock test does not establish Astra Pro Plus, RGB, depth,
ARM64 SDK, timing, pose inference, Unity, projector, or site compatibility.
Pose schema and Unity scripts establish integration seams only; multi-person
identity association and retargeting are future work.
