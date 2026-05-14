"""Windows foreground-window helpers for search-string paste experiments."""

import sys
import time


def get_foreground_window():
    """Return the current foreground window handle, or None outside Windows."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        return int(hwnd) if hwnd else None
    except Exception as exc:
        print(f"[WINDOW] GetForegroundWindow failed: {exc}")
        return None


def focus_window(hwnd, wait_seconds=0.12):
    """Best-effort foreground restore for a previously captured HWND."""
    if sys.platform != "win32" or not hwnd:
        return False

    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        hwnd = wintypes.HWND(hwnd)
        if not user32.IsWindow(hwnd):
            print("[WINDOW] target window no longer exists")
            return False

        SW_RESTORE = 9
        user32.ShowWindow(hwnd, SW_RESTORE)

        foreground = user32.GetForegroundWindow()
        current_thread = kernel32.GetCurrentThreadId()
        target_thread = user32.GetWindowThreadProcessId(hwnd, None)
        foreground_thread = user32.GetWindowThreadProcessId(foreground, None) if foreground else 0

        attached_target = False
        attached_foreground = False
        if target_thread and target_thread != current_thread:
            attached_target = bool(user32.AttachThreadInput(current_thread, target_thread, True))
        if foreground_thread and foreground_thread != current_thread:
            attached_foreground = bool(user32.AttachThreadInput(current_thread, foreground_thread, True))

        try:
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)
        finally:
            if attached_foreground:
                user32.AttachThreadInput(current_thread, foreground_thread, False)
            if attached_target:
                user32.AttachThreadInput(current_thread, target_thread, False)

        time.sleep(wait_seconds)
        return user32.GetForegroundWindow() == hwnd.value
    except Exception as exc:
        print(f"[WINDOW] focus_window failed: {exc}")
        return False
