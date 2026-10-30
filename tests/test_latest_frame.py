import unittest
from desktop.ingest import LatestFrame, LatestFrameStore


class LatestFrameTests(unittest.TestCase):
    def test_replaces_old_frame_and_rejects_reordering(self):
        store = LatestFrameStore()
        store.publish(LatestFrame({"frame_id": 1}, b"one"))
        store.publish(LatestFrame({"frame_id": 2}, b"two"))
        self.assertEqual(store.queue.get_nowait().jpeg, b"two")
        self.assertEqual(store.dropped_frames, 1)
        store.publish(LatestFrame({"frame_id": 1}, b"old"))
        self.assertTrue(store.queue.empty())
        self.assertEqual(store.dropped_frames, 2)
