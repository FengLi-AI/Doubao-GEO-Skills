#!/usr/bin/env python3
"""Copy all five sibling skills. Never overwrite an existing skill."""
from __future__ import annotations
import argparse
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("doubao-geo-publisher", "geo-keyword-miner", "geo-article-writer",
          "geo-platform-adapter", "geo-doubao-research")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, help="The assistant's skills directory.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    destination = Path(args.destination).expanduser().resolve()
    conflicts = [name for name in SKILLS if (destination / name).exists()]
    for name in SKILLS:
        print(f"{name} -> {destination / name}")
    if conflicts:
        parser.error("Existing skills will not be overwritten: " + ", ".join(conflicts))
    if args.dry_run:
        return 0
    destination.mkdir(parents=True, exist_ok=True)
    created = []
    with tempfile.TemporaryDirectory(prefix=".geo-install-", dir=destination) as staging:
        try:
            for name in SKILLS:
                shutil.copytree(ROOT / "skills" / name, Path(staging) / name,
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
            for name in SKILLS:
                target = destination / name
                if target.exists():
                    raise FileExistsError(str(target))
                (Path(staging) / name).rename(target)
                created.append(target)
        except Exception:
            for target in created:
                shutil.rmtree(target)
            raise
    print("Installed five skills. Reload your assistant's skill catalog.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
