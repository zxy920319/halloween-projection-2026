# Frame and pose protocols

## Pi to desktop binary frame packet

Each WebSocket binary message is:

```text
[4-byte unsigned big-endian metadata byte length]
[UTF-8 JSON object]
[JPEG bytes]
```

The current decoder caps metadata at 16 KiB and payload at 5 MiB. It rejects
unknown protocol versions, malformed JSON, unsupported message types, incomplete
headers, invalid frame metadata, and non-JPEG frame envelopes. The desktop
receiver additionally drops non-increasing frame IDs and replaces queued unread
frames with the latest frame.

Frame metadata includes `version`, `type`, `source`, `frame_id`,
`capture_monotonic_ns`, dimensions, `encoding`, JPEG quality, and
`depth_available`. Health messages contain no payload. Monotonic timestamps are
host-local; never subtract Pi and desktop clocks to claim one-way latency.

## Desktop to Unity pose contract

`shared/pose_schema.py` defines version 1 `PoseFrame` with `persons[]`. Frames
support at most three people; each tracked person has a session-local `track_id`,
state, confidence, event map, and either no landmarks or exactly 33. Empty
`persons` represents no detected people. Track association is not implemented.

See `shared/schemas/pose.schema.json` for the JSON shape. Estimated MediaPipe
world coordinates must not be represented as measured Orbbec depth.
