from unittest.mock import Mock, patch

from src.poetore.clipboard import read_item_clipboard


def test_uses_qt_clipboard_outside_windows():
    clipboard = Mock()
    clipboard.text.return_value = "日本語の本文"

    with patch("src.poetore.clipboard.sys.platform", "darwin"):
        assert read_item_clipboard(clipboard) == "日本語の本文"


def test_prefers_windows_unicode_clipboard_text():
    clipboard = Mock()
    clipboard.text.return_value = "Pandemonium Bane"

    with (
        patch("src.poetore.clipboard.sys.platform", "win32"),
        patch(
            "src.poetore.clipboard._read_windows_unicode_text",
            return_value="地獄の破滅",
        ),
    ):
        assert read_item_clipboard(clipboard) == "地獄の破滅"


def test_falls_back_to_qt_when_windows_unicode_text_is_unavailable():
    clipboard = Mock()
    clipboard.text.return_value = "fallback"

    with (
        patch("src.poetore.clipboard.sys.platform", "win32"),
        patch("src.poetore.clipboard._read_windows_unicode_text", return_value=""),
    ):
        assert read_item_clipboard(clipboard) == "fallback"
