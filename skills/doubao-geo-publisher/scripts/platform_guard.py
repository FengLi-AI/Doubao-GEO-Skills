#!/usr/bin/env python3
"""Check local editorial policy; this is not platform approval."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from geo_core import PLATFORMS, check_article, neutral_title


def lint(title, article, platform, industry="general", keyword="", evidence=""):
    return check_article(title, article, platform, industry, keyword, evidence), neutral_title(title, platform)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=PLATFORMS)
    parser.add_argument("--industry", default="general")
    parser.add_argument("--keyword", default="")
    parser.add_argument("--title", required=True)
    parser.add_argument("--article", required=True)
    parser.add_argument("--evidence", help="Optional UTF-8 source list, kept outside the public body.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    evidence = Path(args.evidence).read_text(encoding="utf-8-sig") if args.evidence else ""
    issues, suggestion = lint(args.title, Path(args.article).read_text(encoding="utf-8-sig"),
                              args.platform, args.industry, args.keyword, evidence)
    passed = not any(i["severity"] == "error" for i in issues)
    payload = {"platform": args.platform, "scope": "local_editorial_rules", "passed": passed,
               "manual_review_required": True, "issues": issues, "suggested_title": suggestion}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Local editorial checks: {'passed' if passed else 'failed'}")
        for issue in issues:
            print(f"- [{issue['severity']}] {issue['message']}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
