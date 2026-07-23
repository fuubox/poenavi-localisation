import json

from src.utils.lap_recorder import LapRecorder


def test_save_run_preserves_optional_completed_segments(tmp_path, monkeypatch):
    monkeypatch.setattr(LapRecorder, "RUNS_DIR", str(tmp_path))
    segments = [{"zone_id": "act1_area1", "zone_name": "黄昏の岸辺", "duration": 25.0}]

    path = LapRecorder.save_run([60.0, None], 60.0, segments=segments)

    assert json.loads(open(path, encoding="utf-8").read())["segments"] == segments
