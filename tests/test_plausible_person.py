from desktop.pose.mediapipe_estimator import Landmark, is_plausible_person


def body(overrides=None):
    pts = {i: (0.5, 0.5, 0.9) for i in range(33)}
    pts[0] = (0.5, 0.2, 0.9)
    pts[11] = (0.42, 0.35, 0.95)
    pts[12] = (0.58, 0.35, 0.95)
    pts[23] = (0.45, 0.65, 0.95)
    pts[24] = (0.55, 0.65, 0.95)
    pts.update(overrides or {})
    return [Landmark(i, pts[i][0], pts[i][1], 0.0, pts[i][2], 1.0) for i in range(33)]


def test_accepts_upright_body():
    assert is_plausible_person(body())


def test_rejects_low_core_visibility():
    assert not is_plausible_person(body({11: (0.42, 0.35, 0.2), 12: (0.58, 0.35, 0.2)}))


def test_rejects_head_below_shoulders():
    assert not is_plausible_person(body({0: (0.5, 0.9, 0.9)}))


def test_rejects_degenerate_torso():
    assert not is_plausible_person(body({23: (0.42, 0.36, 0.95), 24: (0.58, 0.36, 0.95)}))


def test_suppress_duplicates_keeps_most_confident_overlapping_pose():
    from desktop.pose.mediapipe_estimator import suppress_duplicates

    a = ([], 0.9, [0.3, 0.1, 0.6, 0.9])
    ghost = ([], 0.6, [0.32, 0.15, 0.58, 0.85])
    other = ([], 0.7, [0.7, 0.1, 0.95, 0.9])
    assert suppress_duplicates([ghost, other, a]) == [a, other]
