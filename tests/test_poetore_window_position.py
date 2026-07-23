from PySide6.QtCore import QPoint, QRect, QSize

from src.poetore.window_position import calculate_panel_position


def test_cursor_on_right_places_panel_inward_from_inventory():
    position = calculate_panel_position(
        QRect(100, 50, 1920, 1080), QPoint(1700, 400), QSize(860, 720), margin=16,
    )
    assert position == QPoint(494, 50)


def test_cursor_on_left_places_panel_inward_from_stash():
    position = calculate_panel_position(
        QRect(100, 50, 1920, 1080), QPoint(300, 400), QSize(860, 720), margin=16,
    )
    assert position == QPoint(766, 50)


def test_1280p_layout_matches_awakened_horizontal_formula():
    position = calculate_panel_position(
        QRect(0, 0, 1920, 1280), QPoint(1750, 300), QSize(845, 710), margin=16,
    )
    assert position == QPoint(286, 0)


def test_panel_is_clamped_when_target_is_smaller():
    position = calculate_panel_position(
        QRect(-1280, 0, 800, 600), QPoint(-600, 100), QSize(860, 720), margin=16,
    )
    assert position == QPoint(-1264, 0)
