from __future__ import annotations

import unittest

from src.core.utils import canonicalize_company_name


class UtilsTests(unittest.TestCase):
    def test_canonicalize_company_name_normalizes_known_typos(self) -> None:
        self.assertEqual(canonicalize_company_name("Catepillar"), "Caterpillar")
        self.assertEqual(canonicalize_company_name("Idaho National Labrotory"), "Idaho National Laboratory")
        self.assertEqual(canonicalize_company_name("Karios Power"), "Kairos Power")


if __name__ == "__main__":
    unittest.main()
