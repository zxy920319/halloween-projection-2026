import unittest

from shared.pose_schema import Landmark, PoseFrame, TrackedPerson, validate_pose_frame


class PoseSchemaTests(unittest.TestCase):
    def test_empty_persons_is_valid(self):
        validate_pose_frame(PoseFrame(version=1, frame_id=1, timestamp=1))

    def test_requires_exact_landmark_count_and_unique_tracks(self):
        point = Landmark(0, 0, 0, 0, 1, 1)
        person = TrackedPerson("one", "tracked", 0.9, [point])
        with self.assertRaises(ValueError):
            validate_pose_frame(PoseFrame(1, 1, 1, [person]))
        person.landmarks = [point] * 33
        validate_pose_frame(PoseFrame(1, 1, 1, [person]))
        with self.assertRaises(ValueError):
            validate_pose_frame(PoseFrame(1, 2, 1, [person, person]))

    def test_rejects_non_finite_landmarks(self):
        import math

        invalid = Landmark(0, math.nan, 0, 0, 1, 1)
        person = TrackedPerson("one", "tracked", 0.9, [invalid] * 33)
        with self.assertRaises(ValueError):
            validate_pose_frame(PoseFrame(1, 1, 1, [person]))
