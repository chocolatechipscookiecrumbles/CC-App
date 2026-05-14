import unittest

from programlauncher.common.pdf_names import fallback_institution_from_filename
from programlauncher.common.sports import normalize_sport_name


class CommonLogicTests(unittest.TestCase):
    def test_filename_fallback_removes_fy_suffix(self):
        self.assertEqual(
            fallback_institution_from_filename("College of Charleston, FY24.pdf"),
            "College of Charleston",
        )

    def test_filename_fallback_keeps_plain_name(self):
        self.assertEqual(
            fallback_institution_from_filename("Example University.pdf"),
            "Example University",
        )

    def test_sport_normalization_track_variant(self):
        self.assertEqual(normalize_sport_name("Track and Field, X-Country"), "XC/TF")

    def test_sport_normalization_swimming_variant(self):
        self.assertEqual(normalize_sport_name("Swimming and"), "Swimming and Diving")

    def test_sport_normalization_acrobatics_variant(self):
        self.assertEqual(normalize_sport_name("Acrobatics & Tumbling"), "Acrobatics and Tumbling")


if __name__ == "__main__":
    unittest.main()

