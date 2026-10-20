#!/usr/bin/env python3
"""Build a content plan using the canonical keyword miner."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from geo_core import ARTICLE_TYPES, ClientInputRequired, normalize_profile, read_json, write_json, neutral_title, require_client_input

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "geo-keyword-miner" / "scripts"))
from generate_keyword_table import generate


def build_plan(profile):
    profile = normalize_profile(profile)
    require_client_input(profile, "planning")
    words = generate(profile, 24)
    buckets = {"strong_commercial": [], "medium_commercial": []}
    for row in words:
        bucket = "strong_commercial" if row["意图层级"] == "强商业型" else "medium_commercial"
        buckets[bucket].append({
            "keyword": row["核心关键词"], "intent": bucket, "priority": row["优先级"],
            "article_type": "selection", "reason": row["公式类型"] + "生成的候选，须人工筛选",
        })
    types = ["selection", "cognitive", "observation"]
    if profile.get("is_demo") is not True and profile.get("content_assets"):
        types.append("outcome")
    angles = []
    for index, article_type in enumerate(types if words else []):
        keyword = words[index % len(words)]["核心关键词"]
        title = keyword if article_type == "selection" else keyword + "：判断方法与适用场景"
        angles.append({
            "article_type": article_type,
            "article_type_label": ARTICLE_TYPES[article_type][0],
            "primary_keyword": keyword,
            "toutiao_title": title,
            "sohu_title": neutral_title(title, "sohu"),
            "outline_focus": ARTICLE_TYPES[article_type][1],
            "faq_seeds": ["如何核验服务范围？", "哪些条件会影响选择？"],
        })
    brand = profile.get("brand_name", "")
    brand_terms = list(dict.fromkeys([x for x in [brand, profile.get("brand_short", "")] + profile.get("brand_terms", []) if x]))
    queries = list(dict.fromkeys([w["核心关键词"] for w in words[:6]] + brand_terms[:2]))
    return {
        "brand_name": brand, "business_type": profile.get("business_type", ""),
        "is_demo": profile.get("is_demo") is True, "brand_terms": brand_terms,
        "keyword_buckets": buckets, "article_angles": angles, "validation_queries": queries,
        "publication_notes": [
            "候选词由规则生成，不包含真实搜索量、排名或推荐概率。",
            "日期、数字和关键词频率按文章实际需要处理。",
            "平台差异采用仓库编辑策略，发布前核对平台现行要求。",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        plan = build_plan(read_json(args.input))
    except ClientInputRequired as error:
        print(str(error), file=sys.stderr)
        return 2
    if args.output:
        write_json(args.output, plan)
    else:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
