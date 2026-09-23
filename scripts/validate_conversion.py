#!/usr/bin/env python3
"""Validate ChatGPT packaging and lossless deterministic conversion."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from convert_skill import ADAPTER_DESCRIPTION, OPENAI_METADATA, SPLIT_HEADING, build_core, parse_frontmatter

PREFIX = (
    "# Humanizer-zh 详细编辑模式\n\n"
    "此文件由上游 `SKILL.md` 确定性拆分生成。实际执行中文润色或审阅任务时读取；"
    "不要把这些模式当作作者身份检测标准。\n\n"
    "## 目录\n\n"
    "- [模式的使用方式](#模式的使用方式)\n"
    "- [A. 铺垫代替陈述](#a-铺垫代替陈述)\n"
    "- [B. 公式化节奏](#b-公式化节奏)\n"
    "- [C. 拔高与借权威](#c-拔高与借权威)\n"
    "- [D. 公式化排版](#d-公式化排版)\n"
    "- [E. 聊天与草稿残留](#e-聊天与草稿残留)\n"
    "- [F. 中文表达的补充检查](#f-中文表达的补充检查)\n"
    "- [交付前核对](#交付前核对)\n"
    "- [完整示例](#完整示例)\n\n"
)
NAV = (
    "\n\n## 详细编辑模式\n\n"
    "在实际润色或审阅中文文本前，读取 "
    "[references/patterns.md](references/patterns.md)。"
    "其中保留上游的 31 个检查点、交付前核对和完整示例。"
    "只讨论安装、维护或 Skill 本身时无需加载。\n"
)


def output_frontmatter_keys(text: str) -> set[str]:
    if not text.startswith("---\n"):
        return set()
    end = text.find("\n---\n", 4)
    raw = text[4:end]
    keys = set()
    for line in raw.splitlines():
        if line and not line[:1].isspace() and ":" in line:
            keys.add(line.split(":", 1)[0].strip())
    return keys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    source = (args.source_dir / "SKILL.md").read_text(encoding="utf-8")
    generated = (args.output_dir / "SKILL.md").read_text(encoding="utf-8")
    patterns_doc = (args.output_dir / "references" / "patterns.md").read_text(encoding="utf-8")
    source_meta, source_body = parse_frontmatter(source)
    generated_meta, generated_body = parse_frontmatter(generated)
    source_core, source_patterns = build_core(source_body)

    checks: dict[str, bool] = {}
    checks["frontmatter_only_name_description"] = output_frontmatter_keys(generated) == {"name", "description"}
    checks["name_preserved"] = generated_meta["name"] == source_meta["name"] == "humanizer-zh"
    checks["description_adapter_owned"] = generated_meta["description"] == ADAPTER_DESCRIPTION
    checks["description_chinese_only"] = (
        "Chinese-language" in generated_meta["description"]
        and "only" in generated_meta["description"]
        and "纯英文" in generated_meta["description"]
    )
    checks["core_preserved"] = generated_body == source_core.rstrip() + NAV
    checks["patterns_preserved"] = patterns_doc == PREFIX + source_patterns.rstrip() + "\n"
    checks["openai_metadata_chinese_only"] = (
        (args.output_dir / "agents" / "openai.yaml").read_text(encoding="utf-8") == OPENAI_METADATA
    )
    checks["license_present"] = (args.output_dir / "LICENSE").is_file()
    checks["no_placeholder_files"] = not any(
        p.name.startswith("example_") or p.name == "api_reference.md"
        for p in args.output_dir.rglob("*")
        if p.is_file()
    )
    provenance = json.loads((args.output_dir / "UPSTREAM.json").read_text(encoding="utf-8"))
    checks["provenance_has_commit"] = bool(re.fullmatch(r"[0-9a-f]{40}", provenance.get("upstream_commit", "")))

    failed = [name for name, ok in checks.items() if not ok]
    print(json.dumps({"checks": checks, "passed": not failed}, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
