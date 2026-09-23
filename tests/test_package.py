from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_zip_has_skill_top_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            skill = tmp / "humanizer-zh"
            (skill / "agents").mkdir(parents=True)
            (skill / "SKILL.md").write_text("x", encoding="utf-8")
            (skill / "agents" / "openai.yaml").write_text("x", encoding="utf-8")
            out = tmp / "skill.zip"
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "package_release.py"), "--skill-dir", str(skill), "--output", str(out)],
                check=True,
            )
            with zipfile.ZipFile(out) as zf:
                self.assertEqual(sorted(zf.namelist()), ["humanizer-zh/SKILL.md", "humanizer-zh/agents/openai.yaml"])


if __name__ == "__main__":
    unittest.main()
