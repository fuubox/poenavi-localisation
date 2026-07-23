import unittest

try:
    from src.ui.main_window import MiniNaviOverlay
except ModuleNotFoundError as exc:  # pragma: no cover - local dev without GUI deps
    MiniNaviOverlay = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

from src.utils.guide_data import get_mini_navi_content


class MiniNaviSpacePreservationTest(unittest.TestCase):
    def test_get_mini_navi_content_preserves_leading_and_inner_spaces(self):
        guide = {
            "mini_navi": {
                "text": "▸親行\n  └ 子行  余白あり",
                "direction": "none",
            }
        }

        result = get_mini_navi_content(guide)

        self.assertEqual(result["text"], "▸親行\n  └ 子行  余白あり")

    def test_get_mini_navi_content_preserves_leading_nbsp(self):
        guide = {
            "mini_navi": {
                "text": "▸親行\n\u00a0\u00a0└ 子行",
                "direction": "none",
            }
        }

        result = get_mini_navi_content(guide)

        self.assertEqual(result["text"], "▸親行\n\u00a0\u00a0└ 子行")

    def test_get_mini_navi_content_returns_all_lines_without_a_limit(self):
        guide = {
            "mini_navi": {
                "text": "一行目\n二行目\n三行目\n四行目\n五行目",
                "direction": "none",
            }
        }

        result = get_mini_navi_content(guide, max_lines=None)

        self.assertEqual(result["text"].splitlines(), ["一行目", "二行目", "三行目", "四行目", "五行目"])

    @unittest.skipIf(MiniNaviOverlay is None, f"GUI dependencies unavailable: {IMPORT_ERROR}")
    def test_render_line_preserves_spaces_without_breaking_span_tags(self):
        overlay = MiniNaviOverlay.__new__(MiniNaviOverlay)

        rendered = overlay._render_line("\u00a0\u00a0<span style='color:#dddd44'>西の森</span>  へ")

        self.assertIn("&nbsp;&nbsp;<span style='color:#dddd44'>西の森</span>&nbsp;&nbsp;へ", rendered)
        self.assertNotIn("<span&nbsp;style", rendered)


if __name__ == "__main__":
    unittest.main()
