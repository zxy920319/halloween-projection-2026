"""Session-local IDs and short-lived detection association."""

from dataclasses import dataclass
from itertools import product
from math import hypot, isfinite
from uuid import uuid4


class SessionTrackIdFactory:
    def __init__(self) -> None:
        self._session_id = uuid4()

    def new_track_id(self) -> str:
        """Return a temporary, non-identifying ID unique within this session."""
        return f"{self._session_id}:{uuid4()}"


@dataclass
class _Track:
    track_id: str
    bbox: tuple[float, float, float, float]
    last_seen: float
    velocity: tuple[float, float] = (0.0, 0.0)

    def predicted_center(self, now: float) -> tuple[float, float]:
        cx, cy = _center(self.bbox)
        dt = min(max(now - self.last_seen, 0.0), 0.5)
        return cx + self.velocity[0] * dt, cy + self.velocity[1] * dt


def _center(box: tuple[float, float, float, float]) -> tuple[float, float]:
    return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2


class PoseIdentityTracker:
    """Associate detections by normalized box center for brief gaps and reordering."""

    def __init__(
        self,
        max_center_distance: float = 0.25,
        lost_track_timeout: float = 1.0,
        max_retained_tracks: int = 6,
        id_factory: SessionTrackIdFactory | None = None,
        ambiguity_margin: float = 0.05,
    ) -> None:
        if max_center_distance <= 0 or lost_track_timeout <= 0 or max_retained_tracks < 1:
            raise ValueError("tracking distance/timeout must be positive and track limit at least one")
        self._max_center_distance = max_center_distance
        self._lost_track_timeout = lost_track_timeout
        self._max_retained_tracks = max_retained_tracks
        self._id_factory = id_factory or SessionTrackIdFactory()
        self._ambiguity_margin = ambiguity_margin
        self._tracks: dict[str, _Track] = {}
        self._ambiguous: set[str] = set()

    @property
    def active_track_ids(self) -> set[str]:
        return set(self._tracks)

    @property
    def ambiguous_track_ids(self) -> set[str]:
        """Tracks from the last assign() whose match was close to another candidate."""
        return set(self._ambiguous)

    def assign(
        self,
        detections: list[list[float]],
        now: float,
    ) -> list[str]:
        """Return one unique temporary ID per detection, preserving input order."""
        if not isfinite(now):
            raise ValueError("tracking timestamp must be finite")
        if len(detections) > 3:
            raise ValueError("pose tracking supports at most three detections")
        self._tracks = {
            track_id: track
            for track_id, track in self._tracks.items()
            if now - track.last_seen <= self._lost_track_timeout
        }
        boxes = [self._validate_bbox(box) for box in detections]
        tracks = list(self._tracks.values())
        distances = [
            [
                hypot(
                    _center(box)[0] - track.predicted_center(now)[0],
                    _center(box)[1] - track.predicted_center(now)[1],
                )
                for track in tracks
            ]
            for box in boxes
        ]

        best_matches: dict[int, int] = {}
        best_score = (-1, float("inf"))
        for choices in product(range(-1, len(tracks)), repeat=len(boxes)):
            matched = [track_index for track_index in choices if track_index >= 0]
            if len(set(matched)) != len(matched):
                continue
            if any(
                track_index >= 0
                and distances[detection_index][track_index] > self._max_center_distance
                for detection_index, track_index in enumerate(choices)
            ):
                continue
            score = (
                len(matched),
                sum(
                    distances[detection_index][track_index]
                    for detection_index, track_index in enumerate(choices)
                    if track_index >= 0
                ),
            )
            if score[0] > best_score[0] or (
                score[0] == best_score[0] and score[1] < best_score[1]
            ):
                best_score = score
                best_matches = {
                    detection_index: track_index
                    for detection_index, track_index in enumerate(choices)
                    if track_index >= 0
                }

        track_ids: list[str] = []
        self._ambiguous = set()
        for detection_index, bbox in enumerate(boxes):
            track_index = best_matches.get(detection_index)
            velocity = (0.0, 0.0)
            if track_index is None:
                track_id = self._id_factory.new_track_id()
            else:
                track = tracks[track_index]
                track_id = track.track_id
                dt = now - track.last_seen
                if dt > 1e-6:
                    old, new = _center(track.bbox), _center(bbox)
                    velocity = ((new[0] - old[0]) / dt, (new[1] - old[1]) / dt)
                row = distances[detection_index]
                rivals = [
                    d for index, d in enumerate(row)
                    if index != track_index and d <= self._max_center_distance
                ]
                if rivals and min(rivals) - row[track_index] < self._ambiguity_margin:
                    self._ambiguous.add(track_id)
            self._tracks[track_id] = _Track(track_id, bbox, now, velocity)
            track_ids.append(track_id)
        if len(self._tracks) > self._max_retained_tracks:
            oldest = sorted(self._tracks.values(), key=lambda track: track.last_seen)
            for track in oldest[: len(self._tracks) - self._max_retained_tracks]:
                del self._tracks[track.track_id]
        return track_ids

    @staticmethod
    def _validate_bbox(box: list[float]) -> tuple[float, float, float, float]:
        if len(box) != 4:
            raise ValueError("bbox must contain [left, top, right, bottom]")
        left, top, right, bottom = map(float, box)
        if not all(map(isfinite, (left, top, right, bottom))):
            raise ValueError("bbox coordinates must be finite")
        if right < left or bottom < top:
            raise ValueError("bbox coordinates are inverted")
        return left, top, right, bottom
