#!/usr/bin/env python3
"""Run the synthetic example without network access or model calls."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    out = Path(args.output_dir).resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error("Use an empty or new output directory.")
    out.mkdir(parents=True, exist_ok=True)
    example = ROOT / "examples" / "local-service"
    profile = example / "client_profile.json"

    def run(relative, *arguments):
        result = subprocess.run(
            [sys.executable, str(ROOT / relative), *map(str, arguments)],
            cwd=ROOT, text=True, capture_output=True,
        )
        if result.returncode:
            raise RuntimeError(f"{relative} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")

    run("skills/geo-keyword-miner/scripts/generate_keyword_table.py",
        "--profile", profile, "--output", out / "keywords.csv")
    run("skills/geo-doubao-research/scripts/select_doubao_queries.py",
        "--profile", profile, "--keywords", out / "keywords.csv", "--output", out / "queries.md")
    run("skills/geo-platform-adapter/scripts/adapt_platform_versions.py",
        "--input", example / "article.md", "--evidence", example / "evidence.md",
        "--output-dir", out / "platforms", "--keyword", "家庭保洁怎么选")
    run("skills/doubao-geo-publisher/scripts/run_closed_loop_demo.py",
        "--profile", profile, "--publish-dir", out / "platforms", "--output-dir", out / "showcase")
    report = "skills/geo-doubao-research/scripts/build_doubao_research_report.py"
    for stage in ("pre", "post"):
        run(report, "--mode", "effect", "--stage", stage,
            "--input", example / f"{stage}-log.md", "--output", out / f"{stage}-report.md")
    run(report, "--mode", "compare", "--pre", example / "pre-log.md",
        "--post", example / "post-log.md", "--output", out / "comparison.md")
    run(report, "--mode", "competitor", "--input", example / "competitor-log.md",
        "--output", out / "competitor-report.md")
    summary = json.loads((out / "showcase" / "showcase-summary.json").read_text(encoding="utf-8"))
    if summary["article_count"] != 4 or summary["overall_status"] != "passed":
        raise RuntimeError("Demo did not check all four platform drafts.")
    print(json.dumps({"output_dir": str(out), "data_kind": "synthetic",
                      "article_count": summary["article_count"],
                      "local_status": summary["overall_status"],
                      "publication_status": summary["publication_status"],
                      "search_effect_status": summary["search_effect_status"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
