"""Small typed representation of the versioned persons[] pose contract."""

from dataclasses import dataclass, field
import math
from typing import Literal


@dataclass(frozen=True)
class Landmark:
    id: int
    x: float
    y: float
    z: float
    visibility: float
    presence: float


@dataclass
class TrackedPerson:
    track_id: str
    tracking_state: Literal["tracked", "occluded", "lost"]
    confidence: float
    landmarks: list[Landmark] = field(default_factory=list)
    events: dict[str, bool] = field(default_factory=dict)
    bbox: list[float] | None = None


@dataclass
class PoseFrame:
    version: int
    frame_id: int
    timestamp: int
    persons: list[TrackedPerson] = field(default_factory=list)


def validate_pose_frame(frame: PoseFrame) -> None:
    if frame.version != 1:
        raise ValueError(f"unsupported pose protocol version: {frame.version}")
    if frame.frame_id < 0 or frame.timestamp < 0:
        raise ValueError("frame_id and timestamp must be non-negative")
    if len(frame.persons) > 3:
        raise ValueError("pose frame supports at most three persons")
    track_ids: set[str] = set()
    for person in frame.persons:
        if not person.track_id or person.track_id in track_ids:
            raise ValueError("track_id must be non-empty and unique per frame")
        track_ids.add(person.track_id)
        if not math.isfinite(person.confidence) or not 0 <= person.confidence <= 1:
            raise ValueError("person confidence must be finite and between 0 and 1")
        if len(person.landmarks) not in (0, 33):
            raise ValueError("landmarks must be empty or contain exactly 33 points")
        for landmark in person.landmarks:
            coordinates = (landmark.x, landmark.y, landmark.z)
            scores = (landmark.visibility, landmark.presence)
            if not all(math.isfinite(value) for value in (*coordinates, *scores)):
                raise ValueError("landmark values must be finite")
            if not all(0 <= score <= 1 for score in scores):
                raise ValueError("landmark visibility and presence must be between 0 and 1")
