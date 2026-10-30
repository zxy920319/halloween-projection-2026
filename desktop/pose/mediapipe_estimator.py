"""MediaPipe Pose Landmarker adapter. Frames stay in memory and are never stored."""

import time
from io import BytesIO

from desktop.ingest import LatestFrame
from desktop.pose.identity_tracker import SessionTrackIdFactory
from shared.pose_schema import Landmark, PoseFrame, TrackedPerson, validate_pose_frame

MAX_PERSONS = 3


def _clamp01(value: float | None, default: float = 0.0) -> float:
    if value is None or value != value:
        return default
    return min(1.0, max(0.0, float(value)))


CORE = (11, 12, 23, 24)


def is_plausible_person(lm: list[Landmark], min_core_visibility: float = 0.7) -> bool:
    """Reject hallucinated skeletons (clothes on chairs, etc.) using joint visibility and body geometry."""
    if sum(lm[i].visibility for i in CORE) / len(CORE) < min_core_visibility:
        return False
    if lm[0].visibility < 0.5:
        return False
    sx = abs(lm[11].x - lm[12].x)
    mid_sh = ((lm[11].x + lm[12].x) / 2, (lm[11].y + lm[12].y) / 2)
    mid_hip = ((lm[23].x + lm[24].x) / 2, (lm[23].y + lm[24].y) / 2)
    torso = ((mid_sh[0] - mid_hip[0]) ** 2 + (mid_sh[1] - mid_hip[1]) ** 2) ** 0.5
    if sx < 0.02 or torso < 0.05:
        return False
    if not 0.6 <= torso / sx <= 4.0:
        return False
    # Head above shoulders, shoulders above hips (upright person).
    if not (lm[0].y < mid_sh[1] < mid_hip[1]):
        return False
    # Hips of an upright body sit roughly below the shoulders, not far to the side.
    return abs(mid_sh[0] - mid_hip[0]) < torso * 0.8


class MediaPipePoseEstimator:
    def __init__(
        self,
        model_path: str,
        max_persons: int = MAX_PERSONS,
        smooth_alpha: float = 0.5,
        min_person_confidence: float = 0.5,
        confirm_frames: int = 6,
    ) -> None:
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision

        self._mp = mp
        options = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
            num_poses=min(max_persons, MAX_PERSONS),
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._smooth_alpha = smooth_alpha
        self._min_person_confidence = min_person_confidence
        self._prev: dict[int, list[Landmark]] = {}
        self._confirm_frames = confirm_frames
        self._streak = 0
        self._landmarker = vision.PoseLandmarker.create_from_options(options)
        self._ids = SessionTrackIdFactory()
        # Slot-based IDs: stable only while the same slot keeps detecting someone.
        self._slot_ids: dict[int, str] = {}
        self._last_ts_ms = -1

    def estimate(self, frame: LatestFrame) -> PoseFrame:
        import numpy as np
        from PIL import Image

        rgb = np.asarray(Image.open(BytesIO(frame.jpeg)).convert("RGB"))
        image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        ts_ms = max(int(time.monotonic() * 1000), self._last_ts_ms + 1)
        self._last_ts_ms = ts_ms
        result = self._landmarker.detect_for_video(image, ts_ms)

        persons: list[TrackedPerson] = []
        for points in result.pose_landmarks[:MAX_PERSONS]:
            slot = len(persons)
            landmarks = [
                Landmark(
                    id=i,
                    x=float(p.x),
                    y=float(p.y),
                    z=float(p.z),
                    visibility=_clamp01(p.visibility),
                    presence=_clamp01(p.presence, 1.0),
                )
                for i, p in enumerate(points)
            ]
            if len(landmarks) != 33:
                continue
            confidence = sum(l.visibility for l in landmarks) / 33
            if confidence < self._min_person_confidence or not is_plausible_person(landmarks):
                continue
            landmarks = self._smooth(slot, landmarks)
            if slot not in self._slot_ids:
                self._slot_ids[slot] = self._ids.new_track_id()
            xs = [l.x for l in landmarks]
            ys = [l.y for l in landmarks]
            persons.append(
                TrackedPerson(
                    track_id=self._slot_ids[slot],
                    tracking_state="tracked",
                    confidence=confidence,
                    landmarks=landmarks,
                    bbox=[min(xs), min(ys), max(xs), max(ys)],
                )
            )
        self._streak = self._streak + 1 if persons else 0
        if self._streak < self._confirm_frames:
            persons = []
        for slot in list(self._slot_ids):
            if slot >= len(persons):
                del self._slot_ids[slot]
                self._prev.pop(slot, None)

        pose = PoseFrame(
            version=1,
            frame_id=int(frame.metadata["frame_id"]),
            timestamp=time.monotonic_ns(),
            persons=persons,
        )
        validate_pose_frame(pose)
        return pose

    def _smooth(self, slot: int, landmarks: list[Landmark]) -> list[Landmark]:
        prev = self._prev.get(slot)
        if prev is not None and self._smooth_alpha < 1.0:
            a = self._smooth_alpha
            landmarks = [
                Landmark(
                    n.id,
                    a * n.x + (1 - a) * o.x,
                    a * n.y + (1 - a) * o.y,
                    a * n.z + (1 - a) * o.z,
                    n.visibility,
                    n.presence,
                )
                for n, o in zip(landmarks, prev)
            ]
        self._prev[slot] = landmarks
        return landmarks

    def close(self) -> None:
        self._landmarker.close()
