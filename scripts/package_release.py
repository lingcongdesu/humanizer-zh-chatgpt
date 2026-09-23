#!/usr/bin/env python3
"""Build dist/skill.zip with a top-level humanizer-zh directory."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-dir", type=Path, default=Path("generated/humanizer-zh"))
    parser.add_argument("--output", type=Path, default=Path("dist/skill.zip"))
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        args.output.unlink()
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(args.skill_dir.rglob("*")):
            if path.is_file():
                archive.write(path, Path(args.skill_dir.name) / path.relative_to(args.skill_dir))
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
