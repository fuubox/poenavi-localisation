# 切り離し可能なメインパネル実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or executing-plans. Steps use checkbox syntax.

**Goal:** タイマー、ガイド、マップを独立ウィンドウへ切り離し、本体への復帰と状態復元を可能にする。

**Architecture:** `MainWindow` が各パネルの既存ウィジェット、元のレイアウト、復帰位置を登録する。`DetachedPanelWindow` は一つの既存パネルと本体へ戻す操作を保持する。パネルの内容は複製せず、親子付けだけを切り替える。

**Tech Stack:** Python、PySide6、pytest、ConfigManager。

## Global Constraints

- パネルIDは `timer`、`guide`、`map` の固定値。
- 本体と独立ウィンドウへ同じパネルを同時表示しない。
- テストは `QT_QPA_PLATFORM=minimal python -X faulthandler -m pytest -p no:unraisableexception -q` を使う。

---

### Task 1: 保存状態を追加する

**Files:** `default_config.json`、`src/utils/config_manager.py`、`tests/test_config_manager.py`

- [ ] 失敗するテストを追加する。

```python
def test_load_config_adds_detached_panel_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv(ConfigManager.ENV_USER_DATA_DIR, str(tmp_path))
    assert ConfigManager.load_config()["detached_panels"] == {
        "timer": {"detached": False},
        "guide": {"detached": False},
        "map": {"detached": False},
    }
```

- [ ] テストが `KeyError: 'detached_panels'` で失敗することを確認する。
- [ ] `default_config.json` とマイグレーションに同じ既定値を追加する。
- [ ] `tests/test_config_manager.py` を通す。
- [ ] `git commit -m "feat: persist detached panel state"` を実行する。

### Task 2: 独立ウィンドウ管理を追加する

**Files:** `src/ui/main_window.py`、`tests/test_detached_panels.py`

- [ ] 失敗するテストを追加する。

```python
def test_detach_panel_moves_content_out_of_main_layout(qapp):
    window = make_panel_window(qapp)
    content = window.panel_registry["timer"]["content"]
    window.detach_panel("timer")
    assert content.parentWidget() is window.detached_panel_windows["timer"]
```

- [ ] `detach_panel` 未定義で失敗することを確認する。
- [ ] `DetachedPanelWindow`、`detach_panel(panel_id)`、`restore_panel(panel_id)` を追加する。独立ウィンドウには `↙ 本体へ戻す` を置き、復帰時は保存した元のレイアウト位置へ戻す。
- [ ] `tests/test_detached_panels.py` を通す。
- [ ] `git commit -m "feat: add detachable panel windows"` を実行する。

### Task 3: タイマー・ガイド・マップを登録する

**Files:** `src/ui/main_window.py:4008-4687`、`tests/test_detached_panels.py`

- [ ] 3パネルそれぞれの切り離し・復帰を確認する失敗テストを追加する。

```python
@pytest.mark.parametrize("panel_id", ["timer", "guide", "map"])
def test_each_supported_panel_can_detach_and_restore(qapp, panel_id):
    window = make_panel_window(qapp)
    window.detach_panel(panel_id)
    window.restore_panel(panel_id)
    assert window.panel_registry[panel_id]["content"].parentWidget() is window.panel_registry[panel_id]["host"]
```

- [ ] 未登録パネルで失敗することを確認する。
- [ ] タイマーはトグルとタイマーコンテナ、ガイドはトグルとガイドコンテナ、マップはトグルとサムネイルだけを可搬コンテナにする。ジェム取得は含めない。
- [ ] 各ヘッダーへ `↗ 切り離す` を追加する。
- [ ] 関連するGUIテストを通す。
- [ ] `git commit -m "feat: detach timer guide and map panels"` を実行する。

### Task 4: 復元と終了処理を実装する

**Files:** `src/ui/main_window.py`、`tests/test_detached_panels.py`

- [ ] 保存済みジオメトリが復元される失敗テストを追加する。

```python
def test_restore_detached_panels_applies_saved_geometry(qapp):
    window = make_panel_window(qapp)
    window.config["detached_panels"] = {"timer": {"detached": True, "x": 30, "y": 40, "width": 420, "height": 280}}
    window._restore_detached_panels()
    assert window.detached_panel_windows["timer"].geometry().getRect() == (30, 40, 420, 280)
```

- [ ] 復元メソッド未定義で失敗することを確認する。
- [ ] `setup_ui()` 完了後に復元し、移動・リサイズ・復帰・終了時に設定を保存する。不正なサイズは既定値へ戻す。
- [ ] 関連テストを通す。
- [ ] `git commit -m "feat: restore detached panel layouts"` を実行する。

### Task 5: 最終検証とPR更新

**Files:** PR #8説明文（必要な場合のみ）

- [ ] 全テストを実行する。

```bash
QT_QPA_PLATFORM=minimal python -X faulthandler -m pytest -p no:unraisableexception -q
```

- [ ] `git diff --check` と `git status --short --branch` を確認する。
- [ ] `git push fork codex/mini-navi-and-log-autodetect` を実行する。
