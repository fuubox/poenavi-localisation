from unittest.mock import Mock, patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
import pytest

from src.poetore.ui import PoetoreWindow, show_poetore_window
from src.poetore.trade import PriceListing, PriceResult, TradeStatFilter


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_poetore_window_always_accepts_mouse_input(qapp):
    window = PoetoreWindow()
    try:
        assert window.isEnabled()
        assert not window.testAttribute(Qt.WA_TransparentForMouseEvents)
        assert not bool(window.windowFlags() & Qt.WindowTransparentForInput)
        assert window.trade_status_combo.currentData() == "instant"
        assert window.trade_status_combo.count() == 3
    finally:
        window.close()


def test_show_poetore_window_is_independent_from_owner(qapp):
    owner = Mock()
    owner._poetore_window = None

    with patch.object(PoetoreWindow, "show"), patch.object(PoetoreWindow, "raise_"), patch.object(
        PoetoreWindow, "activateWindow"
    ):
        window = show_poetore_window(owner)

    try:
        assert window.parent() is None
        assert owner._poetore_window is window
    finally:
        window.close()


def test_price_result_is_rendered_in_japanese(qapp):
    window = PoetoreWindow()
    window._show_price_result(PriceResult("Mirage", "q", 42, (
        PriceListing(4, "chaos", "seller1", "Doom Sever", "Reaver Sword"),
        PriceListing(6, "chaos", "seller2", "Foe Bite", "Reaver Sword"),
    )))
    assert "Mirage" in window.price_status.text()
    assert "候補42件" in window.price_status.text()
    assert "中央値 5 chaos" in window.price_status.text()
    assert window.price_list.topLevelItemCount() == 2
    assert window.price_list.topLevelItem(0).text(1) == "4 chaos"
    assert window.price_list.topLevelItem(0).text(2) == "Doom Sever / Reaver Sword"
    assert window.price_list.topLevelItem(0).text(3) == "seller1"
    window.close()


def test_mod_filters_are_checkable_and_minimum_is_editable(qapp):
    window = PoetoreWindow()
    window._populate_stat_filters((TradeStatFilter(
        "explicit.stat_1", "命中力 +55", 55, "prefix", False,
    ),))
    row = window.mod_filter_tree.topLevelItem(0)
    assert row.checkState(0) == Qt.Unchecked
    editor = window.mod_filter_tree.itemWidget(row, 3)
    assert editor.text() == "55"
    row.setCheckState(0, Qt.Checked)
    editor.setText("50")
    assert window._selected_stat_filters() == (
        TradeStatFilter("explicit.stat_1", "命中力 +55", 50, "prefix", True),
    )
    window.close()
