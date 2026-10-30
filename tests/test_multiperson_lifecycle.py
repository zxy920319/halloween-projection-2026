import unittest

from desktop.pose.identity_tracker import PoseIdentityTracker


def box(center_x, center_y=0.5, half_w=0.08, half_h=0.3):
    return [center_x - half_w, center_y - half_h, center_x + half_w, center_y + half_h]


class MultiPersonLifecycleTests(unittest.TestCase):
    def test_count_sequence_0_1_2_3_2_1_0_keeps_surviving_ids(self):
        tracker = PoseIdentityTracker()
        left, middle, right = 0.2, 0.5, 0.8
        t = 0.0
        self.assertEqual(tracker.assign([], t), [])

        t += 0.1
        a = tracker.assign([box(left)], t)[0]
        t += 0.1
        two = tracker.assign([box(left), box(right)], t)
        self.assertEqual(two[0], a)
        b = two[1]
        t += 0.1
        three = tracker.assign([box(left), box(middle), box(right)], t)
        self.assertEqual([three[0], three[2]], [a, b])
        t += 0.1
        self.assertEqual(tracker.assign([box(left), box(right)], t), [a, b])
        t += 0.1
        self.assertEqual(tracker.assign([box(right)], t), [b])
        t += 0.1
        self.assertEqual(tracker.assign([], t), [])

    def test_shuffled_detector_order_never_changes_ids(self):
        tracker = PoseIdentityTracker()
        boxes = [box(0.2), box(0.5), box(0.8)]
        ids = tracker.assign(boxes, 0.0)
        by_box = {tuple(b): i for b, i in zip(boxes, ids)}
        for step, order in enumerate([(2, 0, 1), (1, 2, 0), (0, 2, 1)], start=1):
            shuffled = [boxes[i] for i in order]
            result = tracker.assign(shuffled, step * 0.1)
            self.assertEqual(result, [by_box[tuple(b)] for b in shuffled])

    def test_walking_crossing_keeps_ids_and_flags_ambiguity(self):
        tracker = PoseIdentityTracker()
        a, b = tracker.assign([box(0.2), box(0.8)], 0.0)
        flagged = set()
        steps = 20
        for step in range(1, steps + 1):
            fraction = step / steps
            xa = 0.2 + 0.6 * fraction
            xb = 0.8 - 0.6 * fraction
            ids = tracker.assign([box(xa), box(xb)], step * 0.1)
            flagged |= tracker.ambiguous_track_ids
            self.assertEqual(ids, [a, b], f"identity swapped at step {step}")
        self.assertTrue(flagged, "close crossing must be reported as uncertain")

    def test_well_separated_people_are_not_ambiguous(self):
        tracker = PoseIdentityTracker()
        tracker.assign([box(0.2), box(0.8)], 0.0)
        tracker.assign([box(0.21), box(0.79)], 0.1)
        self.assertEqual(tracker.ambiguous_track_ids, set())

    def test_exit_and_reentry_within_timeout_recovers_id_after_timeout_gets_new(self):
        tracker = PoseIdentityTracker(lost_track_timeout=1.0)
        a, b = tracker.assign([box(0.2), box(0.8)], 0.0)
        self.assertEqual(tracker.assign([box(0.8)], 0.2), [b])
        self.assertEqual(tracker.assign([box(0.2), box(0.8)], 0.6)[0], a)
        tracker.assign([box(0.8)], 0.7)
        tracker.assign([box(0.8)], 1.5)
        reentered = tracker.assign([box(0.2), box(0.8)], 2.5)
        self.assertNotEqual(reentered[0], a)
        self.assertEqual(reentered[1], b)

    def test_departed_person_motion_not_transferred_to_remaining_person(self):
        tracker = PoseIdentityTracker(max_center_distance=0.25)
        a, b = tracker.assign([box(0.2), box(0.8)], 0.0)
        result = tracker.assign([box(0.5)], 0.1)
        self.assertEqual(len(result), 1)
        self.assertNotIn(result[0], {a, b}, "far-away detection must not inherit an old ID")

    def test_more_than_three_detections_are_rejected(self):
        with self.assertRaises(ValueError):
            PoseIdentityTracker().assign([box(x) for x in (0.1, 0.3, 0.5, 0.7)], 0.0)


if __name__ == "__main__":
    unittest.main()
