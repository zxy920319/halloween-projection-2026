# Multi-person implementation and acceptance

The software prototype supports up to three detections. The MediaPipe adapter
assigns temporary session-local IDs using normalized bounding-box center
distance, retains tracks across short gaps, smooths landmarks independently by
track ID, and emits an empty `persons` list when no detection is accepted.
Unity's three-slot registry keeps an active track bound to its skeleton slot
and lays out multiple characters horizontally. These are software behaviors,
not evidence of reliable real-person identity tracking.

Automated tests (`tests/test_multiperson_lifecycle.py`, `tests/test_pose_pipeline.py`)
cover the synthetic 0→1→2→3→2→1→0 count sequence, shuffled detector order,
walking crossings, exit/re-entry inside and beyond the loss timeout, rejection
of more than three detections, and ambiguity reporting. The tracker predicts
each track's next position from its velocity; when a match has a close rival
(`ambiguity_margin`), the person is emitted as `occluded`. Unity keeps that
skeleton's slot but freezes it instead of driving it from an uncertain match.
These synthetic bounding boxes do not establish real-person crossing/occlusion
behavior or the Unity-side lifecycle.

## M6 live acceptance

M6 remains `NOT_TESTED` until a live Pi-to-desktop stream and Unity renderer are
available. Test person counts 0→1→2→3→2→1→0, detector result reordering,
side-by-side movement, crossing, partial/full occlusion, exit/re-entry,
per-track smoothing isolation, stale packets, and loss/recovery. An uncertain
identity must not silently transfer one person's motion to another skeleton.
Record tested hardware/software, lighting, FPS, coverage, ID switches,
recovery, and latency. Do not promote synthetic checks to field `PASS`.

## M7 live acceptance

Three-person software capacity is configurable, but M7 remains `NOT_TESTED`
until the intended camera view and site are measured with three people.
Evaluate full-body coverage, occlusion, inference rate, character layout, and
whether the view can safely support the intended interaction area. Keep the
three-person option disabled for a deployment that has not passed this check.
