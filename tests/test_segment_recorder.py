from src.utils.segment_recorder import SegmentRecorder


def test_records_elapsed_time_between_distinct_area_entries():
    recorder = SegmentRecorder()

    assert recorder.record_entry("act1_area1", "黄昏の岸辺", 10.0) is None
    completed = recorder.record_entry("act1_area2", "海岸", 42.5)

    assert completed == {
        "zone_id": "act1_area1",
        "zone_name": "黄昏の岸辺",
        "visit": 1,
        "started_at": 10.0,
        "ended_at": 42.5,
        "duration": 32.5,
    }
    assert recorder.segments == [completed]


def test_ignores_duplicate_entry_and_records_reentry_as_a_new_visit():
    recorder = SegmentRecorder()

    recorder.record_entry("act1_area1", "黄昏の岸辺", 0.0)
    assert recorder.record_entry("act1_area1", "黄昏の岸辺", 1.0) is None
    recorder.record_entry("act1_area2", "海岸", 20.0)
    recorder.record_entry("act1_area1", "黄昏の岸辺", 40.0)

    assert [(segment["zone_id"], segment["visit"], segment["duration"]) for segment in recorder.segments] == [
        ("act1_area1", 1, 20.0),
        ("act1_area2", 1, 20.0),
    ]


def test_slowest_segments_returns_at_most_three_longest_completed_segments():
    recorder = SegmentRecorder()
    recorder.segments = [
        {"zone_id": "a", "duration": 10.0},
        {"zone_id": "b", "duration": 40.0},
        {"zone_id": "c", "duration": 30.0},
        {"zone_id": "d", "duration": 20.0},
    ]

    assert [segment["zone_id"] for segment in recorder.slowest_segments()] == ["b", "c", "d"]


def test_summary_returns_latest_and_three_slowest_segments():
    recorder = SegmentRecorder([
        {"zone_id": "a", "zone_name": "海岸", "duration": 10.0},
        {"zone_id": "b", "zone_name": "海底洞窟", "duration": 30.0},
        {"zone_id": "c", "zone_name": "罪人の通路", "duration": 20.0},
        {"zone_id": "d", "zone_name": "牢獄", "duration": 40.0},
    ])

    summary = recorder.summary()

    assert summary["latest"]["zone_id"] == "d"
    assert [segment["zone_id"] for segment in summary["slowest"]] == ["d", "b", "c"]
