#!/usr/bin/env python3
"""Deterministically convert upstream Humanizer-zh into a ChatGPT-compatible Skill."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

SPLIT_HEADING = "## 模式的使用方式"
SOURCE_REPO = "https://github.com/op7418/Humanizer-zh"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md is missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("SKILL.md frontmatter is not terminated")
    raw = text[4:end]
    body = text[end + 5 :]

    data: dict[str, str] = {}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line or line[:1].isspace() or ":" not in line:
            i += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key not in {"name", "description"}:
            i += 1
            continue
        if value in {"|", ">"}:
            block: list[str] = []
            i += 1
            while i < len(lines) and (not lines[i] or lines[i][:1].isspace()):
                block.append(lines[i].strip())
                i += 1
            data[key] = ("\n" if value == "|" else " ").join(block).strip()
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        data[key] = value
        i += 1

    if not data.get("name") or not data.get("description"):
        raise ValueError("frontmatter must contain name and description")
    return data, body


def yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_core(body: str) -> tuple[str, str]:
    marker = f"\n{SPLIT_HEADING}\n"
    if marker not in body:
        raise ValueError(f"expected split heading not found: {SPLIT_HEADING}")
    core, patterns = body.split(marker, 1)
    core = core.rstrip() + "\n"
    patterns = SPLIT_HEADING + "\n" + patterns.lstrip()
    return core, patterns


def patterns_document(patterns: str) -> str:
    return (
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
        + patterns.rstrip()
        + "\n"
    )


def convert(source_dir: Path, output_dir: Path, upstream_sha: str) -> None:
    skill_path = source_dir / "SKILL.md"
    license_path = source_dir / "LICENSE"
    if not skill_path.exists():
        raise FileNotFoundError(skill_path)

    source_text = skill_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(source_text)
    if meta["name"] != "humanizer-zh":
        raise ValueError(f"unexpected upstream skill name: {meta['name']}")

    core, patterns = build_core(body)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "agents").mkdir(parents=True)
    (output_dir / "references").mkdir(parents=True)

    generated_skill = (
        "---\n"
        f"name: {meta['name']}\n"
        f"description: {yaml_scalar(meta['description'])}\n"
        "---\n"
        + core.rstrip()
        + "\n\n"
        "## 详细编辑模式\n\n"
        "在实际润色或审阅中文文本前，读取 "
        "[references/patterns.md](references/patterns.md)。"
        "其中保留上游的 31 个检查点、交付前核对和完整示例。"
        "只讨论安装、维护或 Skill 本身时无需加载。\n"
    )
    (output_dir / "SKILL.md").write_text(generated_skill, encoding="utf-8")
    (output_dir / "references" / "patterns.md").write_text(
        patterns_document(patterns), encoding="utf-8"
    )
    (output_dir / "agents" / "openai.yaml").write_text(
        "interface:\n"
        '  display_name: "Humanizer 中文润色"\n'
        '  short_description: "在保留事实、确定程度和作者声音的前提下，让中文表达更自然。"\n'
        '  default_prompt: "使用 $humanizer-zh 润色我提供的中文文本；优先保留事实、限定、归因和原有文体，只修改确实存在的表达问题。"\n',
        encoding="utf-8",
    )
    provenance = {
        "upstream_repository": SOURCE_REPO,
        "upstream_commit": upstream_sha,
        "conversion": "deterministic",
        "source_file": "SKILL.md",
        "split_heading": SPLIT_HEADING,
    }
    (output_dir / "UPSTREAM.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if license_path.exists():
        shutil.copy2(license_path, output_dir / "LICENSE")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--upstream-sha", required=True)
    args = parser.parse_args()
    convert(args.source_dir, args.output_dir, args.upstream_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
