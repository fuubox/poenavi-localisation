import os
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "minimal")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.ui.map_viewer import MapImageDialog


def test_map_image_dialog_does_not_quit_the_application_when_closed():
    QApplication.instance() or QApplication([])
    with patch("src.utils.config_manager.ConfigManager.load_config", return_value={}):
        dialog = MapImageDialog("missing-map.png")

    assert not dialog.testAttribute(Qt.WA_QuitOnClose)
    dialog.close()
