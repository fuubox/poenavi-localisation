from __future__ import annotations

import sys


def read_item_clipboard(qt_clipboard) -> str:
    """WindowsではUnicode本文を直接読み、取得できなければQtへフォールバックする。"""
    if sys.platform == "win32":
        native_text = _read_windows_unicode_text()
        if native_text:
            return native_text
    return qt_clipboard.text()


def _read_windows_unicode_text() -> str:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    user32.GetClipboardData.restype = wintypes.HANDLE
    kernel32.GlobalLock.restype = wintypes.LPVOID

    if not user32.OpenClipboard(None):
        return ""
    try:
        handle = user32.GetClipboardData(13)  # CF_UNICODETEXT
        if not handle:
            return ""
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            return ""
        try:
            return ctypes.wstring_at(pointer)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()
