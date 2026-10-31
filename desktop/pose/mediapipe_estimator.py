"""MediaPipe Pose Landmarker adapter. Frames stay in memory and are never stored."""

import time
from io import BytesIO
from pathlib import Path

from desktop.ingest import LatestFrame
from desktop.pose.identity_tracker import PoseIdentityTracker
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


def _overlap_ratio(a: list[float], b: list[float]) -> float:
    """Intersection area over the smaller box's area (1.0 = one box fully inside the other)."""
    iw = min(a[2], b[2]) - max(a[0], b[0])
    ih = min(a[3], b[3]) - max(a[1], b[1])
    if iw <= 0 or ih <= 0:
        return 0.0
    smaller = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
    return iw * ih / smaller if smaller > 0 else 1.0


def _bbox_of(landmarks: list[Landmark]) -> list[float]:
    xs = [l.x for l in landmarks if l.visibility >= 0.5] or [l.x for l in landmarks]
    ys = [l.y for l in landmarks if l.visibility >= 0.5] or [l.y for l in landmarks]
    return [min(xs), min(ys), max(xs), max(ys)]


def suppress_duplicates(
    detections: list[tuple[list[Landmark], float, list[float]]], max_overlap: float = 0.45
) -> list[tuple[list[Landmark], float, list[float]]]:
    """Drop ghost skeletons that overlap a more confident detection (one body, several poses)."""
    kept: list[tuple[list[Landmark], float, list[float]]] = []
    for det in sorted(detections, key=lambda d: d[1], reverse=True):
        if all(_overlap_ratio(det[2], k[2]) < max_overlap for k in kept):
            kept.append(det)
    return kept


class MediaPipePoseEstimator:
    def __init__(
        self,
        model_path: str,
        max_persons: int = MAX_PERSONS,
        smooth_alpha: float = 0.5,
        min_person_confidence: float = 0.5,
        confirm_frames: int = 6,
    ) -> None:
        if not 1 <= max_persons <= MAX_PERSONS:
            raise ValueError(f"max_persons must be between 1 and {MAX_PERSONS}")
        if not 0 <= smooth_alpha <= 1:
            raise ValueError("smooth_alpha must be between 0 and 1")
        if not 0 <= min_person_confidence <= 1:
            raise ValueError("min_person_confidence must be between 0 and 1")
        if confirm_frames < 1:
            raise ValueError("confirm_frames must be at least 1")
        if not Path(model_path).is_file():
            raise FileNotFoundError(
                f"MediaPipe pose model not found: {model_path}. "
                "Place an official Pose Landmarker .task model at this path."
            )

        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision

        self._mp = mp
        self._max_persons = max_persons
        options = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
            num_poses=max_persons,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._smooth_alpha = smooth_alpha
        self._min_person_confidence = min_person_confidence
        self._prev: dict[str, list[Landmark]] = {}
        self._last_seen: dict[str, float] = {}
        self._hold_seconds = 0.6
        self._confirm_frames = confirm_frames
        self._streak = 0
        self._landmarker = vision.PoseLandmarker.create_from_options(options)
        self._identity = PoseIdentityTracker()
        self._last_ts_ms = -1

    def estimate(self, frame: LatestFrame) -> PoseFrame:
        import numpy as np
        from PIL import Image

        rgb = np.asarray(Image.open(BytesIO(frame.jpeg)).convert("RGB"))
        image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        ts_ms = max(int(time.monotonic() * 1000), self._last_ts_ms + 1)
        self._last_ts_ms = ts_ms
        result = self._landmarker.detect_for_video(image, ts_ms)

        detections: list[tuple[list[Landmark], float, list[float]]] = []
        for points in result.pose_landmarks[: self._max_persons]:
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
            xs = [l.x for l in landmarks if l.visibility >= 0.5] or [l.x for l in landmarks]
            ys = [l.y for l in landmarks if l.visibility >= 0.5] or [l.y for l in landmarks]
            detections.append((landmarks, confidence, [min(xs), min(ys), max(xs), max(ys)]))
        detections = suppress_duplicates(detections)

        now = time.monotonic()
        track_ids = self._identity.assign([bbox for _, _, bbox in detections], now)
        persons: list[TrackedPerson] = []
        ambiguous = self._identity.ambiguous_track_ids
        for track_id, (landmarks, confidence, bbox) in zip(track_ids, detections):
            landmarks = self._smooth(track_id, landmarks)
            self._last_seen[track_id] = now
            persons.append(
                TrackedPerson(
                    track_id=track_id,
                    tracking_state="occluded" if track_id in ambiguous else "tracked",
                    confidence=confidence,
                    landmarks=landmarks,
                    bbox=bbox,
                )
            )
        # Briefly keep people the detector dropped for a frame or two, frozen as
        # "occluded", so their skeleton slot is not released and re-created.
        seen_now = set(track_ids)
        for track_id, landmarks in self._prev.items():
            if (
                track_id not in seen_now
                and track_id in self._identity.active_track_ids
                and now - self._last_seen.get(track_id, -1e9) <= self._hold_seconds
                and len(persons) < self._max_persons
                and not any(
                    p.bbox is not None and _overlap_ratio(p.bbox, _bbox_of(landmarks)) >= 0.3
                    for p in persons
                )
            ):
                persons.append(
                    TrackedPerson(
                        track_id=track_id,
                        tracking_state="occluded",
                        confidence=0.0,
                        landmarks=landmarks,
                    )
                )
        active = self._identity.active_track_ids
        self._prev = {t: l for t, l in self._prev.items() if t in active}
        self._last_seen = {t: s for t, s in self._last_seen.items() if t in active}
        self._streak = self._streak + 1 if track_ids else 0
        if self._streak < self._confirm_frames:
            persons = []

        pose = PoseFrame(
            version=1,
            frame_id=int(frame.metadata["frame_id"]),
            timestamp=time.monotonic_ns(),
            persons=persons,
        )
        validate_pose_frame(pose)
        return pose

    def _smooth(self, track_id: str, landmarks: list[Landmark]) -> list[Landmark]:
        prev = self._prev.get(track_id)
        if prev is not None and self._smooth_alpha < 1.0:
            # Adaptive EMA: heavy smoothing for jitter, light for real motion
            # (keeps fast movement responsive without per-frame flicker).
            lo = self._smooth_alpha * 0.4
            hi = min(1.0, self._smooth_alpha + 0.4)
            out = []
            for n, o in zip(landmarks, prev):
                speed = ((n.x - o.x) ** 2 + (n.y - o.y) ** 2) ** 0.5
                a = lo + (hi - lo) * min(1.0, speed / 0.05)
                av = 0.5
                out.append(
                    Landmark(
                        n.id,
                        a * n.x + (1 - a) * o.x,
                        a * n.y + (1 - a) * o.y,
                        a * n.z + (1 - a) * o.z,
                        av * n.visibility + (1 - av) * o.visibility,
                        n.presence,
                    )
                )
            landmarks = out
        self._prev[track_id] = landmarks
        return landmarks

    def close(self) -> None:
        self._landmarker.close()
