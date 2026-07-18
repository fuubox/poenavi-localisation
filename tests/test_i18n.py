import unittest

from src.utils.i18n import EN, JA, get_supported_locales, normalize_locale, set_locale, tr


class I18nTest(unittest.TestCase):
    def tearDown(self):
        set_locale(JA)

    def test_supported_locale_normalization_and_catalog_lookup(self):
        self.assertEqual(normalize_locale("en-US"), EN)
        self.assertEqual(normalize_locale("ja-JP"), JA)
        self.assertEqual(get_supported_locales(), (JA, EN))

        set_locale(EN)
        self.assertEqual(tr("app.title"), "PoENavi")
        self.assertIn("The Coast", tr("guide.missing", zone="The Coast"))

    def test_missing_named_placeholder_is_reported(self):
        set_locale(EN)
        with self.assertRaises(KeyError):
            tr("guide.missing")


if __name__ == "__main__":
    unittest.main()
