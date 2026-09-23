from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = """---
name: humanizer-zh
description: 本地同步测试
allowed-tools:
  - Read
---
# Humanizer-zh

核心。

## 模式的使用方式

规则。
"""


class SyncTests(unittest.TestCase):
    def test_full_sync_against_local_git_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            upstream = tmp / "upstream"
            upstream.mkdir()
            subprocess.run(["git", "init", "-b", "main"], cwd=upstream, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=upstream, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=upstream, check=True)
            (upstream / "SKILL.md").write_text(SAMPLE, encoding="utf-8")
            (upstream / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (upstream / "tests").mkdir()
            (upstream / "tests" / "fixture.txt").write_text("fixture\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=upstream, check=True)
            subprocess.run(["git", "commit", "-m", "fixture"], cwd=upstream, check=True, capture_output=True)
            expected_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()

            work = tmp / "work"
            work.mkdir()
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "sync_upstream.py"),
                    "--repo-url",
                    str(upstream),
                    "--output-dir",
                    str(work / "generated" / "humanizer-zh"),
                    "--tests-dir",
                    str(work / "upstream-tests"),
                    "--snapshot-dir",
                    str(work / "upstream-snapshot"),
                    "--lock-file",
                    str(work / "UPSTREAM.lock"),
                ],
                check=True,
                cwd=ROOT,
            )
            lock = json.loads((work / "UPSTREAM.lock").read_text(encoding="utf-8"))
            self.assertEqual(lock["commit"], expected_sha)
            self.assertTrue((work / "upstream-tests" / "fixture.txt").is_file())
            self.assertTrue((work / "generated" / "humanizer-zh" / "agents" / "openai.yaml").is_file())

            # A scheduled check with the same upstream SHA must leave the tree untouched.
            (work / "upstream-snapshot" / "local-marker.txt").write_text("keep\n", encoding="utf-8")
            sync = [
                sys.executable,
                str(ROOT / "scripts" / "sync_upstream.py"),
                "--repo-url", str(upstream),
                "--output-dir", str(work / "generated" / "humanizer-zh"),
                "--tests-dir", str(work / "upstream-tests"),
                "--snapshot-dir", str(work / "upstream-snapshot"),
                "--lock-file", str(work / "UPSTREAM.lock"),
            ]
            subprocess.run(sync, check=True, cwd=ROOT, capture_output=True)
            self.assertTrue((work / "upstream-snapshot" / "local-marker.txt").is_file())

            # A new commit must update the lock and regenerate the skill.
            (upstream / "SKILL.md").write_text(SAMPLE.replace("规则。", "新规则。"), encoding="utf-8")
            subprocess.run(["git", "add", "SKILL.md"], cwd=upstream, check=True)
            subprocess.run(["git", "commit", "-m", "new rule"], cwd=upstream, check=True, capture_output=True)
            new_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
            subprocess.run(sync, check=True, cwd=ROOT, capture_output=True)
            self.assertEqual(json.loads((work / "UPSTREAM.lock").read_text(encoding="utf-8"))["commit"], new_sha)
            self.assertFalse((work / "upstream-snapshot" / "local-marker.txt").exists())
            self.assertIn("新规则。", (work / "generated" / "humanizer-zh" / "references" / "patterns.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
