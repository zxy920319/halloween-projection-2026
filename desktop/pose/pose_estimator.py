from typing import Protocol

from desktop.ingest import LatestFrame
from shared.pose_schema import PoseFrame


class PoseEstimator(Protocol):
    """Interface implemented by the desktop MediaPipe pose estimator."""

    def estimate(self, frame: LatestFrame) -> PoseFrame:
        """Produce a pose frame or an empty persons list when no person is found."""
        ...
