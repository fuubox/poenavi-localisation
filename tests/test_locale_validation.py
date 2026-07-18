import unittest
from pathlib import Path

from scripts.validate_locales import validate_all


class LocaleValidationTest(unittest.TestCase):
    def test_release_locale_assets_pass_validation(self):
        self.assertEqual(validate_all(Path(__file__).resolve().parents[1]), [])


if __name__ == "__main__":
    unittest.main()
