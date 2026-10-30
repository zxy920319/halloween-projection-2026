import unittest

from desktop.pose.identity_tracker import PoseIdentityTracker, SessionTrackIdFactory


class TrackIdFactoryTests(unittest.TestCase):
    def test_ids_are_unique_and_session_scoped(self):
        factory = SessionTrackIdFactory()
        first = factory.new_track_id()
        second = factory.new_track_id()
        self.assertNotEqual(first, second)
        self.assertEqual(first.split(":")[0], second.split(":")[0])
        self.assertNotEqual(first.split(":")[0], SessionTrackIdFactory().new_track_id().split(":")[0])


class PoseIdentityTrackerTests(unittest.TestCase):
    def test_detection_order_changes_preserve_track_ids(self):
        tracker = PoseIdentityTracker()
        first = tracker.assign([[0.1, 0.2, 0.3, 0.8], [0.7, 0.2, 0.9, 0.8]], 1.0)

        reordered = tracker.assign([[0.7, 0.2, 0.9, 0.8], [0.1, 0.2, 0.3, 0.8]], 1.1)

        self.assertEqual(reordered, [first[1], first[0]])

    def test_short_gap_recovers_id_and_expired_track_gets_new_id(self):
        tracker = PoseIdentityTracker(lost_track_timeout=1.0)
        box = [0.1, 0.2, 0.3, 0.8]
        track_id = tracker.assign([box], 1.0)[0]

        self.assertEqual(tracker.assign([box], 1.8), [track_id])
        self.assertNotEqual(tracker.assign([box], 3.0)[0], track_id)

    def test_unmatched_detections_get_distinct_ids(self):
        tracker = PoseIdentityTracker()

        track_ids = tracker.assign(
            [[0.0, 0.1, 0.2, 0.9], [0.4, 0.1, 0.6, 0.9], [0.8, 0.1, 1.0, 0.9]],
            1.0,
        )

        self.assertEqual(len(set(track_ids)), 3)

    def test_invalid_bbox_is_rejected(self):
        with self.assertRaises(ValueError):
            PoseIdentityTracker().assign([[0.3, 0.2, 0.1, 0.8]], 1.0)

    def test_retained_tracks_are_bounded(self):
        tracker = PoseIdentityTracker(max_center_distance=0.1, max_retained_tracks=4)

        for index in range(10):
            left = (index % 2) * 0.8
            tracker.assign([[left, 0.2, left + 0.1, 0.8]], index / 100)

        self.assertLessEqual(len(tracker.active_track_ids), 4)
