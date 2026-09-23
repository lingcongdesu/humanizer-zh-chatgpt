from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from convert_skill import ADAPTER_DESCRIPTION, OPENAI_METADATA, build_core, convert, parse_frontmatter  # noqa: E402


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
            self.assertEqual(
                {line.split(":", 1)[0] for line in frontmatter.splitlines() if ":" in line},
                {"name", "description"},
            )
            generated_meta, generated_body = parse_frontmatter((output / "SKILL.md").read_text(encoding="utf-8"))
            self.assertEqual(generated_meta["description"], ADAPTER_DESCRIPTION)
            self.assertIn("Chinese-language", generated_meta["description"])
            self.assertIn("only", generated_meta["description"])
            self.assertIn("纯英文", generated_meta["description"])
            self.assertEqual((output / "agents" / "openai.yaml").read_text(encoding="utf-8"), OPENAI_METADATA)
            source_body = parse_frontmatter(SAMPLE)[1]
            source_core, source_patterns = build_core(source_body)
            self.assertTrue(generated_body.startswith(source_core))
            self.assertIn(source_patterns, (output / "references" / "patterns.md").read_text(encoding="utf-8"))
            provenance = json.loads((output / "UPSTREAM.json").read_text(encoding="utf-8"))
            self.assertEqual(provenance["upstream_commit"], sha)
            self.assertIn("## A. 铺垫代替陈述", (output / "references" / "patterns.md").read_text(encoding="utf-8"))

    def test_upstream_description_cannot_change_routing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            output = root / "humanizer-zh"
            source_file = source / "SKILL.md"
            source_file.write_text(SAMPLE, encoding="utf-8")
            convert(source, output, "a" * 40)
            original = (output / "SKILL.md").read_bytes()
            original_agent = (output / "agents" / "openai.yaml").read_bytes()

            source_file.write_text(SAMPLE.replace("示例描述", "Use for prose in every language, including English."), encoding="utf-8")
            convert(source, output, "a" * 40)
            self.assertEqual((output / "SKILL.md").read_bytes(), original)
            self.assertEqual((output / "agents" / "openai.yaml").read_bytes(), original_agent)


if __name__ == "__main__":
    unittest.main()
