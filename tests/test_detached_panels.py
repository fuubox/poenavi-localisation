import os

os.environ.setdefault("QT_QPA_PLATFORM", "minimal")

from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from src.ui.main_window import MainWindow
from src.utils.config_manager import ConfigManager


def _app():
    return QApplication.instance() or QApplication([])


def _window():
    _app()
    host = QWidget()
    layout = QVBoxLayout(host)
    content = QWidget()
    layout.addWidget(content)
    window = MainWindow.__new__(MainWindow)
    window.config = {"detached_panels": {"timer": {"detached": False}}}
    window.panel_registry = {"timer": {"content": content, "host": host, "layout": layout, "index": 0, "title": "タイマー"}}
    window.detached_panel_windows = {}
    return window, content, layout


def test_detach_panel_moves_content_out_of_main_layout(monkeypatch):
    window, content, layout = _window()
    monkeypatch.setattr(ConfigManager, "save_config", lambda _config: None)

    window.detach_panel("timer")

    assert layout.indexOf(content) == -1
    assert window.detached_panel_windows["timer"].content is content


def test_restore_panel_returns_content_to_original_layout(monkeypatch):
    window, content, layout = _window()
    monkeypatch.setattr(ConfigManager, "save_config", lambda _config: None)
    window.detach_panel("timer")

    window.restore_panel("timer")

    assert layout.indexOf(content) == 0
    assert window.detached_panel_windows == {}
