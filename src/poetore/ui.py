from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication, QHBoxLayout, QLabel, QMessageBox, QPushButton, QSplitter,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QPlainTextEdit, QHeaderView,
)

from .parser import ItemParseError, parse_item_text


class PoetoreWindow(QWidget):
    """貼り付け解析だけを行う、Trade API未接続のローカル試作画面。"""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("ぽえとれ（ローカル試作・日本語名対応版）")
        self.resize(860, 620)
        layout = QVBoxLayout(self)
        note = QLabel("PoEで詳細コピーしたアイテム文章を貼り付けて解析します。価格検索APIは未接続です。")
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QHBoxLayout()
        paste_button = QPushButton("クリップボードから貼り付け")
        paste_button.clicked.connect(self.paste_from_clipboard)
        buttons.addWidget(paste_button)
        parse_button = QPushButton("解析")
        parse_button.clicked.connect(self.parse_current_text)
        buttons.addWidget(parse_button)
        buttons.addStretch()
        layout.addLayout(buttons)

        splitter = QSplitter(Qt.Horizontal)
        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("ここにアイテムの詳細コピー文を貼り付けます")
        splitter.addWidget(self.input_edit)
        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderLabels(["項目", "解析結果"])
        self.result_tree.setAlternatingRowColors(True)
        self.result_tree.setRootIsDecorated(True)
        self.result_tree.setUniformRowHeights(True)
        self.result_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.result_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        splitter.addWidget(self.result_tree)
        splitter.setSizes([430, 430])
        layout.addWidget(splitter, stretch=1)

    def paste_from_clipboard(self):
        self.input_edit.setPlainText(QApplication.clipboard().text())
        self.parse_current_text()

    def parse_current_text(self):
        try:
            item = parse_item_text(self.input_edit.toPlainText())
        except ItemParseError as exc:
            QMessageBox.warning(self, "解析できませんでした", str(exc))
            return
        self.result_tree.clear()
        for label, value in (
            ("アイテムクラス", item.item_class), ("レアリティ", item.rarity),
            ("名前", item.name), ("ベースタイプ", item.base_type),
            ("カテゴリ", item.category), ("アイテムレベル", item.item_level),
            ("状態", ", ".join(item.flags) or "なし"),
        ):
            QTreeWidgetItem(self.result_tree, [label, "" if value is None else str(value)])
        properties = QTreeWidgetItem(self.result_tree, ["プロパティ", str(len(item.properties))])
        for label, value in item.properties.items():
            QTreeWidgetItem(properties, [label, value])
        modifiers = QTreeWidgetItem(self.result_tree, ["Mod", str(len(item.modifiers))])
        for mod in item.modifiers:
            values = ", ".join(f"{value:g}" for value in mod.values)
            QTreeWidgetItem(modifiers, [mod.kind, f"{mod.text}" + (f"  [{values}]" if values else "")])
        self.result_tree.expandAll()
        self.result_tree.scrollToTop()


def show_poetore_window(owner):
    """ownerが参照を保持し、二重起動せず再表示できる公開エントリ。"""
    window = getattr(owner, "_poetore_window", None)
    if window is None:
        window = PoetoreWindow(owner)
        owner._poetore_window = window
    window.show()
    window.raise_()
    window.activateWindow()
    return window
