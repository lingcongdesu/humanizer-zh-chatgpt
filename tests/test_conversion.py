from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from convert_skill import convert, parse_frontmatter  # noqa: E402


SAMPLE = """---
name: humanizer-zh
description: 示例描述
allowed-tools:
  - Read
metadata:
  trigger: 示例
---
# Humanizer-zh

核心内容。

## 模式的使用方式

模式说明。

## A. 铺垫代替陈述

### 1. 示例

保留语义。
"""


class ConversionTests(unittest.TestCase):
    def test_parse_ignores_non_openai_frontmatter(self):
        meta, body = parse_frontmatter(SAMPLE)
        self.assertEqual(meta, {"name": "humanizer-zh", "description": "示例描述"})
        self.assertIn("核心内容", body)

    def test_conversion_is_deterministic_and_preserves_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            output = root / "output"
            source.mkdir()
            (source / "SKILL.md").write_text(SAMPLE, encoding="utf-8")
            (source / "LICENSE").write_text("MIT\n", encoding="utf-8")
            sha = "a" * 40
            convert(source, output, sha)
            first = {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}
            convert(source, output, sha)
            second = {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}
            self.assertEqual(first, second)
            frontmatter = (output / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1]
            self.assertNotIn("allowed-tools", frontmatter)
            self.assertNotIn("metadata", frontmatter)
            provenance = json.loads((output / "UPSTREAM.json").read_text(encoding="utf-8"))
            self.assertEqual(provenance["upstream_commit"], sha)
            self.assertIn("## A. 铺垫代替陈述", (output / "references" / "patterns.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
