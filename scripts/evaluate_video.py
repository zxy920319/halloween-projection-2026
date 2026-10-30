"""Run a local video through the pose pipeline and report tracking stability.

Frames are processed in memory only; nothing is recorded or uploaded. Use only
footage you are authorized to use and keep it out of the repository.

    python scripts/evaluate_video.py clip.mp4 --model models/pose_landmarker_full.task --max-persons 2
"""

import argparse
import sys
from collections import Counter
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from desktop.ingest import LatestFrame  # noqa: E402


def summarize(frames: list[list[tuple[str, str]]]) -> dict:
    """frames: per-frame list of (track_id, tracking_state)."""
    total = len(frames)
    ids_seen: list[str] = []
    for frame in frames:
        for track_id, _ in frame:
            if track_id not in ids_seen:
                ids_seen.append(track_id)
    states = Counter(state for frame in frames for _, state in frame)
    person_frames = sum(len(frame) for frame in frames)
    count_changes = sum(
        1 for previous, current in zip(frames, frames[1:]) if len(previous) != len(current)
    )
    # A person whose ID disappears and a new ID appears soon after is a likely ID switch.
    reappeared = 0
    last_present: dict[str, int] = {}
    first_seen: dict[str, int] = {}
    for index, frame in enumerate(frames):
        for track_id, _ in frame:
            first_seen.setdefault(track_id, index)
            last_present[track_id] = index
    for track_id, start in first_seen.items():
        if start == 0:
            continue
        if any(0 < start - end <= 15 for other, end in last_present.items() if other != track_id):
            reappeared += 1
    return {
        "frames": total,
        "unique_track_ids": len(ids_seen),
        "person_frames": person_frames,
        "occluded_ratio": round(states.get("occluded", 0) / person_frames, 3) if person_frames else 0.0,
        "person_count_changes": count_changes,
        "likely_id_switches": reappeared,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video")
    parser.add_argument("--model", default="models/pose_landmarker_lite.task")
    parser.add_argument("--max-persons", type=int, default=2)
    parser.add_argument("--max-frames", type=int, default=0, help="0 means whole video")
    args = parser.parse_args()

    try:
        import cv2
    except ImportError:
        raise SystemExit("OpenCV is required for this script: python -m pip install opencv-python")
    from PIL import Image

    from desktop.pose.mediapipe_estimator import MediaPipePoseEstimator

    capture = cv2.VideoCapture(args.video)
    if not capture.isOpened():
        raise SystemExit(f"cannot open video: {args.video}")
    estimator = MediaPipePoseEstimator(args.model, max_persons=args.max_persons, confirm_frames=1)
    frames: list[list[tuple[str, str]]] = []
    try:
        index = 0
        while args.max_frames <= 0 or index < args.max_frames:
            ok, bgr = capture.read()
            if not ok:
                break
            buffer = BytesIO()
            Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).save(buffer, "JPEG", quality=85)
            pose = estimator.estimate(LatestFrame({"frame_id": index}, buffer.getvalue()))
            frames.append([(p.track_id, p.tracking_state) for p in pose.persons])
            index += 1
    finally:
        capture.release()
        estimator.close()

    for key, value in summarize(frames).items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
