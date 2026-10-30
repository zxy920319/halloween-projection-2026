import unittest

from desktop.pose.identity_tracker import SessionTrackIdFactory


class TrackIdFactoryTests(unittest.TestCase):
    def test_ids_are_unique_and_session_scoped(self):
        factory = SessionTrackIdFactory()
        first = factory.new_track_id()
        second = factory.new_track_id()
        self.assertNotEqual(first, second)
        self.assertEqual(first.split(":")[0], second.split(":")[0])
        self.assertNotEqual(first.split(":")[0], SessionTrackIdFactory().new_track_id().split(":")[0])
