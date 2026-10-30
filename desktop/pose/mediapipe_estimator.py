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


class MediaPipePoseEstimator:
    def __init__(
        self,
        model_path: str,
        max_persons: int = MAX_PERSONS,
        smooth_alpha: float = 0.5,
        min_person_confidence: float = 0.5,
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
            if confidence < self._min_person_confidence:
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
