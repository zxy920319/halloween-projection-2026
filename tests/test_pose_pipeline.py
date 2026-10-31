import asyncio
import json
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from desktop.ingest import LatestFrame
from desktop.pose.publisher import PosePublisher, pose_to_json
from shared.pose_schema import Landmark, PoseFrame, TrackedPerson

MODEL = Path("models/pose_landmarker_lite.task")


def test_pose_to_json_matches_contract():
    lms = [Landmark(i, 0.5, 0.5, 0.0, 0.9, 1.0) for i in range(33)]
    pose = PoseFrame(1, 7, 123, [TrackedPerson("t:1", "tracked", 0.9, lms)])
    data = json.loads(pose_to_json(pose))
    assert data["type"] == "pose" and data["frame_id"] == 7
    assert data["coordinate_space"] == "normalized_image"
    assert len(data["persons"][0]["landmarks"]) == 33


def test_pose_estimator_rejects_missing_model_with_actionable_error(tmp_path):
    from desktop.pose.mediapipe_estimator import MediaPipePoseEstimator

    missing = tmp_path / "pose_landmarker_lite.task"
    with pytest.raises(FileNotFoundError, match="official Pose Landmarker"):
        MediaPipePoseEstimator(str(missing))


def test_pose_cli_fails_before_starting_servers_when_model_is_missing(
    monkeypatch, tmp_path
):
    from desktop.main import main

    missing = tmp_path / "pose_landmarker_lite.task"
    monkeypatch.setattr(
        "sys.argv",
        ["desktop.main", "--pose", "--model", str(missing)],
    )

    with pytest.raises(SystemExit, match="pose model not found"):
        main()


@pytest.mark.parametrize("max_persons", [0, 4])
def test_pose_estimator_rejects_person_limit_outside_protocol(max_persons, tmp_path):
    from desktop.pose.mediapipe_estimator import MediaPipePoseEstimator

    model = tmp_path / "model.task"
    model.touch()
    with pytest.raises(ValueError, match="max_persons"):
        MediaPipePoseEstimator(str(model), max_persons=max_persons)


def _synthetic_pose_landmarks(center_x):
    class Point:
        z = 0.0
        visibility = 0.95
        presence = 0.95

        def __init__(self, x, y):
            self.x = x
            self.y = y

    points = [Point(center_x, 0.5) for _ in range(33)]
    points[0] = Point(center_x, 0.15)
    points[11] = Point(center_x - 0.08, 0.35)
    points[12] = Point(center_x + 0.08, 0.35)
    points[23] = Point(center_x - 0.06, 0.65)
    points[24] = Point(center_x + 0.06, 0.65)
    return points


def _estimator_with_fake_landmarker(pose_landmarks, max_persons=3):
    from desktop.pose.identity_tracker import PoseIdentityTracker
    from desktop.pose.mediapipe_estimator import MediaPipePoseEstimator

    class FakeLandmarker:
        def detect_for_video(self, _image, _timestamp):
            return type("Result", (), {"pose_landmarks": pose_landmarks})()

    class FakeMediaPipe:
        ImageFormat = type("ImageFormat", (), {"SRGB": 1})

        @staticmethod
        def Image(**_kwargs):
            return object()

    estimator = MediaPipePoseEstimator.__new__(MediaPipePoseEstimator)
    estimator._mp = FakeMediaPipe
    estimator._max_persons = max_persons
    estimator._smooth_alpha = 1.0
    estimator._min_person_confidence = 0.5
    estimator._prev = {}
    estimator._last_seen = {}
    estimator._hold_seconds = 0.6
    estimator._confirm_frames = 1
    estimator._streak = 0
    estimator._landmarker = FakeLandmarker()
    estimator._identity = PoseIdentityTracker()
    estimator._last_ts_ms = -1
    return estimator


def test_estimator_emits_contract_landmarks_and_respects_person_limit():
    estimator = _estimator_with_fake_landmarker(
        [_synthetic_pose_landmarks(x) for x in (0.2, 0.5, 0.8)],
        max_persons=2,
    )
    image = BytesIO()
    Image.new("RGB", (320, 240)).save(image, "JPEG")

    pose = estimator.estimate(LatestFrame({"frame_id": 12}, image.getvalue()))

    assert pose.frame_id == 12
    assert len(pose.persons) == 2
    assert all(len(person.landmarks) == 33 for person in pose.persons)
    assert len({person.track_id for person in pose.persons}) == 2


def test_estimator_keeps_identity_when_detector_order_changes():
    estimator = _estimator_with_fake_landmarker(
        [_synthetic_pose_landmarks(0.2), _synthetic_pose_landmarks(0.8)],
    )
    image = BytesIO()
    Image.new("RGB", (320, 240)).save(image, "JPEG")

    first = estimator.estimate(LatestFrame({"frame_id": 1}, image.getvalue()))
    estimator._landmarker = _estimator_with_fake_landmarker(
        [_synthetic_pose_landmarks(0.8), _synthetic_pose_landmarks(0.2)],
    )._landmarker
    second = estimator.estimate(LatestFrame({"frame_id": 2}, image.getvalue()))

    assert [person.track_id for person in second.persons] == [
        first.persons[1].track_id,
        first.persons[0].track_id,
    ]


def test_estimator_merges_near_identical_poses_into_one_person():
    estimator = _estimator_with_fake_landmarker(
        [_synthetic_pose_landmarks(0.48), _synthetic_pose_landmarks(0.52)],
    )
    image = BytesIO()
    Image.new("RGB", (320, 240)).save(image, "JPEG")
    estimator.estimate(LatestFrame({"frame_id": 1}, image.getvalue()))
    pose = estimator.estimate(LatestFrame({"frame_id": 2}, image.getvalue()))

    assert len(pose.persons) == 1


def test_estimator_holds_dropped_person_as_occluded_then_releases():
    both = [_synthetic_pose_landmarks(0.2), _synthetic_pose_landmarks(0.8)]
    estimator = _estimator_with_fake_landmarker(both)
    image = BytesIO()
    Image.new("RGB", (320, 240)).save(image, "JPEG")
    first = estimator.estimate(LatestFrame({"frame_id": 1}, image.getvalue()))
    ids = {p.track_id for p in first.persons}

    estimator._landmarker = _estimator_with_fake_landmarker(both[:1])._landmarker
    second = estimator.estimate(LatestFrame({"frame_id": 2}, image.getvalue()))

    assert {p.track_id for p in second.persons} == ids
    assert sorted(p.tracking_state for p in second.persons) == ["occluded", "tracked"]

    estimator._hold_seconds = -1.0
    third = estimator.estimate(LatestFrame({"frame_id": 3}, image.getvalue()))
    assert len(third.persons) == 1


def test_estimator_emits_empty_persons_when_detection_is_absent():
    estimator = _estimator_with_fake_landmarker([])
    image = BytesIO()
    Image.new("RGB", (320, 240)).save(image, "JPEG")

    pose = estimator.estimate(LatestFrame({"frame_id": 13}, image.getvalue()))

    assert pose.persons == []


@pytest.mark.skipif(not MODEL.exists(), reason="pose model not downloaded")
def test_estimator_blank_frame_has_no_persons():
    pytest.importorskip("mediapipe")
    from desktop.pose.mediapipe_estimator import MediaPipePoseEstimator

    buf = BytesIO()
    Image.new("RGB", (320, 240), (128, 128, 128)).save(buf, "JPEG")
    est = MediaPipePoseEstimator(str(MODEL))
    pose = est.estimate(LatestFrame({"frame_id": 1}, buf.getvalue()))
    est.close()
    assert pose.persons == []


def test_publisher_broadcasts_to_client():
    from websockets.asyncio.client import connect

    pub = PosePublisher()
    pub.start("127.0.0.1", 18766)

    async def run():
        async with connect("ws://127.0.0.1:18766/poses") as ws:
            await asyncio.sleep(0.2)
            pub.publish('{"hello": 1}')
            return await asyncio.wait_for(ws.recv(), 2)

    assert asyncio.run(run()) == '{"hello": 1}'
