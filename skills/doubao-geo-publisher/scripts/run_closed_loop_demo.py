#!/usr/bin/env python3
"""Validate local artifacts; never claim online publication or search improvement."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from geo_core import PLATFORMS, read_json, write_json, title_body, check_article, normalize_profile
from diagnose_client import build_report, to_markdown
from generate_geo_plan import build_plan
from build_prompt_packet import build_prompt
from build_monitoring_plan import build_plan as monitoring_plan


def lint_articles(publish_dir, manifest_path, industry, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results, errors = [], []
    if publish_dir is None:
        status = "skipped"
    else:
        publish_dir = Path(publish_dir)
        if not publish_dir.is_dir():
            status = "failed"
            errors.append("文章目录不存在或不是目录。")
        else:
            manifest_path = Path(manifest_path) if manifest_path else publish_dir / "article-manifest.json"
            manifest = {}
            if manifest_path.exists():
                data = read_json(manifest_path)
                if not isinstance(data, list):
                    raise ValueError("Article manifest must be a list.")
                for item in data:
                    name = item["file"]
                    if Path(name).name != name or name in manifest:
                        raise ValueError("Manifest filenames must be unique basenames.")
                    manifest[name] = item
                for name in manifest:
                    if not (publish_dir / name).is_file():
                        errors.append(f"清单中的文章不存在：{name}")
            paths = [p for p in sorted(publish_dir.glob("*.md")) if p.name.lower() != "readme.md"]
            for path in paths:
                meta = manifest.get(path.name, {})
                platform = meta.get("platform") or (path.stem if path.stem in PLATFORMS else "")
                if platform not in PLATFORMS:
                    errors.append(f"无法识别平台：{path.name}；请提供 article-manifest.json。")
                    continue
                title, body, settings = title_body(path.read_text(encoding="utf-8-sig"))
                evidence = settings
                if meta.get("evidence_file"):
                    evidence_path = (publish_dir / meta["evidence_file"]).resolve()
                    if not evidence_path.is_relative_to(publish_dir.resolve()):
                        raise ValueError("Evidence paths must remain inside the article directory.")
                    if not evidence_path.is_file():
                        errors.append(f"来源文件不存在：{meta['evidence_file']}")
                    else:
                        evidence += "\n" + evidence_path.read_text(encoding="utf-8-sig")
                issues = check_article(title, body, platform, industry, meta.get("keyword", ""), evidence)
                results.append({"file": path.name, "platform": platform, "title": title,
                                "passed": not any(i["severity"] == "error" for i in issues), "issues": issues})
            status = "failed" if errors or any(not r["passed"] for r in results) else ("completed" if results else "empty")
    payload = {"status": status, "articles": results, "errors": errors,
               "passed": (status == "completed") if status not in ("skipped", "empty") else None,
               "scope": "local_editorial_rules", "manual_review_required": True}
    write_json(output_dir / "article-validation.json", payload)
    lines = ["# 本地文章规则检查", "", f"- 状态：{status}", f"- 实际检查文章数：{len(results)}",
             "- 规则检查不代表平台审核通过或事实已经核验。", ""]
    lines.extend("- " + error for error in errors)
    for result in results:
        lines.append(f"## {result['file']}：{'通过规则检查' if result['passed'] else '发现错误'}")
        lines.extend(f"- [{i['severity']}] {i['message']}" for i in result["issues"])
    (output_dir / "article-validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def run(profile_path, output_dir, publish_dir=None, manifest_path=None, industry="general"):
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("请使用新的或空的输出目录，避免旧产物混入本轮结果。")
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = normalize_profile(read_json(profile_path))
    diagnosis = build_report(profile)
    write_json(output_dir / "diagnosis.json", diagnosis)
    (output_dir / "diagnosis.md").write_text(to_markdown(diagnosis), encoding="utf-8")
    intake = diagnosis["client_intake"]
    if intake["status"] == "needs_input":
        write_json(output_dir / "intake-questions.json", intake)
        questions = "# 请先向用户询问\n\n已有信息不重复询问；等待答复后更新客户档案，再重新运行。\n\n"
        questions += "\n".join("- " + item["question"] for item in intake["questions"]) + "\n"
        (output_dir / "intake-questions.md").write_text(questions, encoding="utf-8")
        summary = {
            "scope": "local_artifacts", "overall_status": "incomplete",
            "input_status": "needs_input", "missing_fields": intake["missing_fields"],
            "is_demo": profile.get("is_demo") is True, "planning_generated": False,
            "keyword_count": 0, "prompt_count": 0, "article_validation": "skipped", "article_count": 0,
            "evidence_review": diagnosis["evidence_review"],
            "publication_status": "not_performed", "search_effect_status": "not_evaluated",
            "manual_review_required": True,
        }
        write_json(output_dir / "showcase-summary.json", summary)
        (output_dir / "showcase-summary.md").write_text(
            "# 本地工作流验证汇总\n\n- 状态：incomplete / needs_input\n"
            "- 客户信息尚未齐备，未生成关键词、内容计划或 Prompt。\n"
            "- 下一步：向用户询问 intake-questions.md 中的问题。\n"
            "- 线上发布：未执行\n- 搜索效果：未评估\n", encoding="utf-8")
        return summary
    plan = build_plan(profile)
    write_json(output_dir / "geo-plan.json", plan)
    prompt_dir = output_dir / "prompts"
    prompt_dir.mkdir(exist_ok=True)
    for index, angle in enumerate(plan["article_angles"], 1):
        prompt = build_prompt(profile, angle["primary_keyword"], angle["article_type"], "both")
        (prompt_dir / f"{index:02d}-{angle['article_type']}.txt").write_text(prompt + "\n", encoding="utf-8")
    monitoring = monitoring_plan(profile, plan)
    write_json(output_dir / "monitoring-plan.json", monitoring)
    articles = lint_articles(publish_dir, manifest_path, industry, output_dir)
    total_words = sum(len(b) for b in plan["keyword_buckets"].values())
    planning_ok = bool(total_words and plan["article_angles"] and monitoring["queries"])
    status = "failed" if not planning_ok or articles["status"] == "failed" else (
        "passed" if articles["status"] == "completed" else "incomplete")
    summary = {
        "scope": "local_artifacts", "overall_status": status,
        "input_status": "ready",
        "is_demo": profile.get("is_demo") is True,
        "planning_generated": planning_ok, "keyword_count": total_words,
        "prompt_count": len(plan["article_angles"]), "article_validation": articles["status"],
        "article_count": len(articles["articles"]),
        "evidence_review": diagnosis["evidence_review"],
        "publication_status": "not_performed", "search_effect_status": "not_evaluated",
        "manual_review_required": True,
    }
    write_json(output_dir / "showcase-summary.json", summary)
    lines = ["# 本地工作流验证汇总", "", f"- 本地状态：{status}",
             f"- 关键词：{total_words}", f"- 实际检查文章：{len(articles['articles'])}",
             f"- 文章检查状态：{articles['status']}", f"- 证据状态：{diagnosis['evidence_review']['status']}",
             "- 线上发布：未执行", "- 搜索效果：未评估",
             "- 下一步：核验资料、编辑文章；需要真实效果评估时另行采集同批查询词的前后记录。"]
    (output_dir / "showcase-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--publish-dir")
    parser.add_argument("--article-manifest")
    parser.add_argument("--industry", default="general")
    args = parser.parse_args()
    summary = run(args.profile, args.output_dir, args.publish_dir, args.article_manifest, args.industry)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return {"passed": 0, "failed": 1, "incomplete": 2}[summary["overall_status"]]


if __name__ == "__main__":
    raise SystemExit(main())
