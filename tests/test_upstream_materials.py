from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UpstreamMaterialsTests(unittest.TestCase):
    def test_upstream_fixture_set_is_present(self):
        cases = json.loads((ROOT / "upstream-tests" / "fixtures" / "cases.json").read_text(encoding="utf-8"))
        self.assertEqual(len(cases), 18)
        self.assertTrue((ROOT / "upstream-tests" / "fixtures" / "structure.md").is_file())
        self.assertTrue((ROOT / "upstream-tests" / "check_structure.py").is_file())


if __name__ == "__main__":
    unittest.main()
