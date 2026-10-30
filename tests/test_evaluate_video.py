import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "evaluate_video", Path(__file__).resolve().parent.parent / "scripts" / "evaluate_video.py"
)
evaluate_video = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(evaluate_video)


def test_summary_counts_stable_and_switched_ids():
    stable = [[("a", "tracked"), ("b", "tracked")]] * 10
    assert evaluate_video.summarize(stable)["likely_id_switches"] == 0
    assert evaluate_video.summarize(stable)["unique_track_ids"] == 2

    switched = [[("a", "tracked")]] * 5 + [[("c", "tracked")]] * 5
    result = evaluate_video.summarize(switched)
    assert result["likely_id_switches"] == 1
    assert result["unique_track_ids"] == 2


def test_summary_reports_occluded_ratio_and_count_changes():
    frames = [[("a", "tracked")], [("a", "occluded")], []]
    result = evaluate_video.summarize(frames)
    assert result["occluded_ratio"] == 0.5
    assert result["person_count_changes"] == 1
