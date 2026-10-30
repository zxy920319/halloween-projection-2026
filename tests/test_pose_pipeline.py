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

