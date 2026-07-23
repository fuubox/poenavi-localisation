from src.utils.log_path_detector import fill_missing_client_log_paths


def test_fill_missing_client_log_paths_preserves_manual_value(monkeypatch):
    config = {"client_log_paths": {"poe1": "D:/manual/Client.txt", "poe2": ""}}
    monkeypatch.setattr(
        "src.utils.log_path_detector.detect_client_log_paths",
        lambda: {"poe1": "C:/auto/poe1/Client.txt", "poe2": "C:/auto/poe2/Client.txt"},
    )

    assert fill_missing_client_log_paths(config) is True
    assert config["client_log_paths"] == {
        "poe1": "D:/manual/Client.txt",
        "poe2": "C:/auto/poe2/Client.txt",
    }
