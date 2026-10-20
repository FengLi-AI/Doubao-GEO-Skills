#!/usr/bin/env python3
"""Create mechanical platform drafts, an evidence sidecar and a manifest."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "doubao-geo-publisher" / "scripts"))
from geo_core import PLATFORMS, PHONE_RE, title_body, neutral_title, check_article, write_json


def adapt_body(body, platform):
    # Do not replace words inside factual claims or prepend canned paragraphs.
    if platform in ("sohu", "36kr"):
        return PHONE_RE.sub("官方联系渠道", body)
    return body


def adapt(source, output_dir, keyword="", industry="general", platforms=PLATFORMS, evidence=""):
    platforms = list(platforms)
    if not platforms or any(p not in PLATFORMS for p in platforms) or len(set(platforms)) != len(platforms):
        raise ValueError("Choose distinct supported platform ids: " + ",".join(PLATFORMS))
    title, body, settings = title_body(source)
    if not title or not body:
        raise ValueError("Article needs a title and a nonempty body.")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    sources = "\n\n".join(s for s in (settings, evidence) if s.strip())
    if sources:
        (output_dir / "article.sources.txt").write_text(sources + "\n", encoding="utf-8")
    report = {"scope": "mechanical_drafts", "manual_review_required": True, "variants": [], "issues": []}
    manifest = []
    for platform in platforms:
        variant_title = neutral_title(title, platform)
        variant_body = adapt_body(body, platform)
        filename = f"{platform}.md"
        (output_dir / filename).write_text(f"# {variant_title}\n\n{variant_body}\n", encoding="utf-8")
        issues = check_article(variant_title, variant_body, platform, industry, keyword, sources)
        report["variants"].append({"platform": platform, "file": filename, "title": variant_title})
        report["issues"].extend(dict(i, platform=platform) for i in issues)
        manifest.append({"file": filename, "platform": platform, "keyword": keyword,
                         "evidence_file": "article.sources.txt" if sources else ""})
    report["passed"] = not any(i["severity"] == "error" for i in report["issues"])
    write_json(output_dir / "article-manifest.json", manifest)
    write_json(output_dir / "platform-report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--industry", default="general")
    parser.add_argument("--keyword", default="")
    parser.add_argument("--platforms", default=",".join(PLATFORMS))
    parser.add_argument("--evidence")
    args = parser.parse_args()
    evidence = Path(args.evidence).read_text(encoding="utf-8-sig") if args.evidence else ""
    report = adapt(Path(args.input).read_text(encoding="utf-8-sig"), args.output_dir, args.keyword,
                   args.industry, [p.strip() for p in args.platforms.split(",")], evidence)
    print(f"Generated {len(report['variants'])} drafts; manual editing is required.")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
