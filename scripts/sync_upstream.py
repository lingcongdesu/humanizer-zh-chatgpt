#!/usr/bin/env python3
"""Fetch the upstream repository, convert it, sync tests, and record the commit."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from convert_skill import convert


def run(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True)
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-url", default="https://github.com/op7418/Humanizer-zh.git")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--output-dir", type=Path, default=Path("generated/humanizer-zh"))
    parser.add_argument("--tests-dir", type=Path, default=Path("upstream-tests"))
    parser.add_argument("--snapshot-dir", type=Path, default=Path("upstream-snapshot"))
    parser.add_argument("--lock-file", type=Path, default=Path("UPSTREAM.lock"))
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="humanizer-upstream-") as tmp:
        checkout = Path(tmp) / "repo"
        run("git", "clone", "--depth", "1", "--branch", args.branch, args.repo_url, str(checkout))
        sha = run("git", "rev-parse", "HEAD", cwd=checkout)
        if args.lock_file.exists():
            locked = json.loads(args.lock_file.read_text(encoding="utf-8"))
            if locked.get("commit") == sha:
                print(f"Already synced: {sha}")
                return 0
        if args.snapshot_dir.exists():
            shutil.rmtree(args.snapshot_dir)
        args.snapshot_dir.mkdir(parents=True)
        for name in ("SKILL.md", "LICENSE", "README.md", "CHANGELOG.md"):
            source = checkout / name
            if source.exists():
                shutil.copy2(source, args.snapshot_dir / name)

        convert(args.snapshot_dir, args.output_dir, sha)

        if args.tests_dir.exists():
            shutil.rmtree(args.tests_dir)
        if (checkout / "tests").exists():
            shutil.copytree(checkout / "tests", args.tests_dir)

        args.lock_file.write_text(
            json.dumps(
                {
                    "repository": "https://github.com/op7418/Humanizer-zh",
                    "branch": args.branch,
                    "commit": sha,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
