# Performance Optimization Implementation Plan

> **For agentic workers:** Execute the tasks inline, one task at a time. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 起動と常駐時の不要なディスクI/Oを減らし、変更効果を開発時に計測できるようにする。

**Architecture:** JSON読込はファイルの更新時刻をキーにしたプロセス内キャッシュを利用し、ユーザーが外部編集したデータは次回読込で反映する。設定保存は正規化後のJSONが保存済み内容と一致する場合に書込みを省略する。性能ログは環境変数でのみ有効化する。

**Tech Stack:** Python 3.14, PySide6, `json`, `pathlib`, `time.perf_counter`, pytest

## Global Constraints

- 通常利用時のUI、設定JSON形式、ログ監視間隔を変更しない。
- キャッシュはプロセス内だけに限定し、ファイルの更新時刻が変化したら再読込する。
- 計測ログは `POENAVI_PROFILE=1` のときだけ出力する。
- 既存のユーザー設定とガイド外部編集を失わない。

---

### Task 1: 開発時だけ有効な性能計測ヘルパー

**Files:**
- Create: `src/utils/performance_metrics.py`
- Test: `tests/test_performance_metrics.py`

**Interfaces:**
- Produces: `measure(operation: str)` — `POENAVI_PROFILE=1` のとき `[Performance] <operation>: <milliseconds> ms` を出力するコンテキストマネージャ。

- [ ] **Step 1: Write the failing test**

```python
@patch.dict(os.environ, {"POENAVI_PROFILE": "1"})
@patch("src.utils.performance_metrics.perf_counter", side_effect=[1.0, 1.0125])
def test_measure_prints_elapsed_milliseconds(mock_clock, capsys):
    with measure("guide reload"):
        pass
    assert "[Performance] guide reload: 12.5 ms" in capsys.readouterr().out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_performance_metrics.py -q`

Expected: FAIL because `src.utils.performance_metrics` does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
from contextlib import contextmanager
import os
from time import perf_counter

@contextmanager
def measure(operation: str):
    if os.environ.get("POENAVI_PROFILE") != "1":
        yield
        return
    started = perf_counter()
    yield
    print(f"[Performance] {operation}: {(perf_counter() - started) * 1000:.1f} ms")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_performance_metrics.py -q`

Expected: `2 passed` (有効・無効の両方をテストする)。

- [ ] **Step 5: Commit**

```bash
git add src/utils/performance_metrics.py tests/test_performance_metrics.py
git commit -m "feat: add optional performance measurements"
```

### Task 2: ガイド・ゾーンマスタ読込の更新検知キャッシュ

**Files:**
- Modify: `src/utils/guide_data.py:load_guide_data`
- Modify: `src/utils/zone_master_data.py:load_zone_master_data`
- Create: `tests/test_data_load_caching.py`

**Interfaces:**
- Produces: 同一パス・同一`st_mtime_ns`の呼出しでは前回読込済みの辞書を返し、更新後は新しいJSONを返す。

- [ ] **Step 1: Write the failing tests**

```python
def test_load_guide_data_reuses_unchanged_file(monkeypatch, tmp_path):
    path = tmp_path / "guide_data.json"
    path.write_text('{"zone": {}}', encoding="utf-8")
    monkeypatch.setattr(guide_data, "get_guide_path", lambda _version: str(path))
    guide_data._GUIDE_DATA_CACHE.clear()
    with patch("builtins.open", wraps=open) as mocked_open:
        guide_data.load_guide_data()
        guide_data.load_guide_data()
    assert mocked_open.call_count == 1

def test_load_zone_master_data_reloads_when_file_changes(monkeypatch, tmp_path):
    path = tmp_path / "zone_data.json"
    path.write_text('{"zone_data_by_version": {}, "town_zones_by_version": {}}', encoding="utf-8")
    monkeypatch.setattr(zone_master_data, "get_zone_master_path", lambda: str(path))
    zone_master_data._ZONE_MASTER_CACHE = None
    first = zone_master_data.load_zone_master_data()
    path.write_text('{"zone_data_by_version": {"poe1": {"x": "X"}}, "town_zones_by_version": {}}', encoding="utf-8")
    os.utime(path, None)
    assert zone_master_data.load_zone_master_data() != first
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_data_load_caching.py -q`

Expected: FAIL because cache state variables do not exist and both calls open the file.

- [ ] **Step 3: Write minimal implementation**

```python
_GUIDE_DATA_CACHE: dict[tuple[str, int], dict] = {}

def load_guide_data(poe_version: str = POE1) -> dict:
    path = get_guide_path(poe_version)
    try:
        stamp = os.stat(path).st_mtime_ns
    except OSError:
        return DEFAULT_GUIDE if poe_version == POE1 else {}
    key = (path, stamp)
    if key not in _GUIDE_DATA_CACHE:
        with open(path, "r", encoding="utf-8") as f:
            _GUIDE_DATA_CACHE[key] = json.load(f)
    return _GUIDE_DATA_CACHE[key]
```

ゾーンマスタにも同じく `(path, st_mtime_ns)` を保持し、`save_guide_data` / `save_zone_master_data` の直後は古い同一パスのキャッシュを削除する。

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `python -m pytest tests/test_data_load_caching.py tests/test_guide_detail_level_toggle.py tests/test_log_path_detector.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/utils/guide_data.py src/utils/zone_master_data.py tests/test_data_load_caching.py
git commit -m "perf: cache unchanged guide and zone data"
```

### Task 3: 同一設定のディスク書込みを省略

**Files:**
- Modify: `src/utils/config_manager.py:save_config`
- Modify: `tests/test_config_manager.py`

**Interfaces:**
- Produces: `ConfigManager.save_config(config)` は正規化後のJSONが保存済みファイルと一致する場合、`_write_json` を呼ばない。

- [ ] **Step 1: Write the failing test**

```python
def test_save_config_skips_unchanged_content(tmp_path, monkeypatch):
    monkeypatch.setattr(ConfigManager, "_get_config_path", lambda: str(tmp_path / "config.json"))
    ConfigManager.save_config({"poe_version": "poe1"})
    with patch.object(ConfigManager, "_write_json", wraps=ConfigManager._write_json) as write:
        ConfigManager.save_config({"poe_version": "poe1"})
    write.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config_manager.py::test_save_config_skips_unchanged_content -q`

Expected: FAIL because `_write_json` is called twice.

- [ ] **Step 3: Write minimal implementation**

```python
path = Path(cls._get_config_path())
if path.exists():
    try:
        if cls._load_from_path(path) == config:
            return
    except Exception:
        pass
cls._write_json(path, config)
```

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `python -m pytest tests/test_config_manager.py tests/test_log_path_autofill.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/utils/config_manager.py tests/test_config_manager.py
git commit -m "perf: skip unchanged config writes"
```

### Task 4: 起動・エリア遷移に計測点を接続

**Files:**
- Modify: `src/ui/main_window.py:MainWindow.__init__`
- Modify: `src/ui/main_window.py:MainWindow.on_zone_entered`
- Test: `tests/test_performance_metrics.py`

**Interfaces:**
- Consumes: `measure(operation: str)` from `src.utils.performance_metrics`.
- Produces: `POENAVI_PROFILE=1` 時だけ `startup data load` と `zone update` の処理時間を標準出力へ記録する。

- [ ] **Step 1: Write the failing test**

```python
@patch("src.ui.main_window.measure")
def test_zone_entry_is_measured(measure):
    window = MainWindow.__new__(MainWindow)
    with patch.object(MainWindow, "_handle_zone_entered") as handle:
        MainWindow.on_zone_entered(window, "The Coast")
    measure.assert_called_once_with("zone update")
    handle.assert_called_once_with("The Coast", True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_performance_metrics.py::test_zone_entry_is_measured -q`

Expected: FAIL because `MainWindow._handle_zone_entered` does not exist.

- [ ] **Step 3: Add instrumentation**

```python
with measure("startup data load"):
    zone_master_data = load_zone_master_data()
    self.guide_data = load_guide_data(self.poe_version)

def on_zone_entered(self, zone_name: str, actual_entry: bool = True):
    with measure("zone update"):
        return self._handle_zone_entered(zone_name, actual_entry)
```

`_handle_zone_entered` へ既存の本体を移し、シグナル接続・公開メソッドのシグネチャは維持する。

- [ ] **Step 4: Run regression tests**

Run: `QT_QPA_PLATFORM=minimal python -X faulthandler -m pytest -p no:unraisableexception tests/test_config_manager.py tests/test_log_path_detector.py tests/test_guide_detail_level_toggle.py tests/test_mini_navi_standalone.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ui/main_window.py tests/test_performance_metrics.py
git commit -m "perf: measure startup and zone updates"
```
