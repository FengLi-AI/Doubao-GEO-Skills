#!/usr/bin/env python3
"""Diagnose client readiness for a Doubao GEO engagement."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple
from geo_core import client_intake, evidence_summary, has_value, normalize_profile


REQUIRED_GROUPS = {
    "strategy": ["objectives", "conversion_goal", "target_customers"],
    "business": ["brand_name", "industry", "business_type", "service_area"],
    "production": ["offerings", "channels"],
    "proof": ["eeat", "verified_sources"],
    "compliance": ["compliance"],
}


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return normalize_profile(json.load(handle))


def eeat_strength(profile: Dict) -> int:
    eeat = profile.get("eeat", {})
    score = 0
    for key in ("expertise", "experience", "authority", "trust"):
        if has_value(eeat.get(key, [])):
            score += 1
    return score


def field_score(profile: Dict) -> Tuple[int, int, List[str]]:
    total = 0
    present = 0
    missing = []
    for group, fields in REQUIRED_GROUPS.items():
        for field in fields:
            total += 1
            value = (profile.get("core_services") or profile.get("core_products") or profile.get("business_desc")) \
                if field == "offerings" else profile.get(field)
            if has_value(value):
                present += 1
            else:
                missing.append(f"{group}.{field}")
    return present, total, missing


def infer_service_mode(profile: Dict) -> str:
    business_type = profile.get("business_type", "")
    if business_type == "local_b2c":
        return "本地服务型"
    if business_type == "national_brand":
        return "全国品牌型"
    if business_type == "b2b_factory":
        return "B2B 线索型"
    if business_type == "hybrid":
        return "混合型"
    return "待判断"


def infer_scenario(profile: Dict) -> str:
    stage = profile.get("client_stage", "")
    visibility = profile.get("monitoring_baseline", {}).get("current_visibility", "")
    goals = " ".join(profile.get("objectives", []))
    campuses = profile.get("campuses", [])
    if stage == "cold_start":
        return "新客户冷启动"
    if len(campuses) >= 2 and ("曝光" in goals or "咨询" in goals):
        return "多校区课程推广型"
    if "品牌" in goals and "业务词" not in goals:
        return "品牌防守型"
    if "不稳定" in visibility or "没" in visibility:
        return "已有内容但效果不稳定"
    if profile.get("business_type") == "b2b_factory":
        return "B2B 线索型"
    return "待向用户确认"


def readiness_level(score: int) -> str:
    if score >= 85:
        return "complete_fields"
    if score >= 65:
        return "needs_completion"
    return "foundation_missing"


def immediate_questions(profile: Dict, missing: List[str], eeat_score: int) -> List[str]:
    intake = client_intake(profile)
    if intake["questions"]:
        return [item["question"] for item in intake["questions"]]
    questions = []
    if not has_value(profile.get("conversion_goal")):
        questions.append("希望读者看完内容后采取什么行动？")
    if not has_value(profile.get("eeat")):
        questions.append("有哪些可公开的资质、经历、案例或评价？请提供对应证据，没有的可以说明暂无。")
    if not has_value(profile.get("verified_sources")):
        questions.append("哪些来源可以支撑本次文章？请提供链接或材料，并说明核验状态及公开范围。")
    if not has_value(profile.get("channels")):
        questions.append("准备在哪些平台使用内容？是否已有可用账号或内容资产？")
    if not has_value(profile.get("compliance")):
        questions.append("材料中有哪些不能公开的信息或需要注意的行业限制？")
    return questions


def strengths(profile: Dict, eeat_score: int) -> List[str]:
    output = []
    if has_value(profile.get("brand_name")) and has_value(profile.get("industry")):
        output.append("已提供品牌和行业信息；其余必要字段齐备后可生成关键词。")
    if eeat_score >= 3:
        output.append("已填写多类证据描述；其真实性和公开范围仍须核验。")
    if has_value(profile.get("monitoring_baseline")):
        output.append("已有基线监测信息，便于做收录和引用对比。")
    if has_value(profile.get("channels")):
        output.append("渠道信息明确，可以同步规划头条和搜狐版本。")
    return output


def gaps(profile: Dict, missing: List[str], eeat_score: int) -> List[str]:
    output = []
    if missing:
        output.append("基础资料仍有缺口，接待阶段要先补齐核心字段。")
    if eeat_score < 3:
        output.append("可验证证据偏少，容易导致文章内容空泛。")
    if not has_value(profile.get("content_assets")):
        output.append("缺少现成内容资产，后续案例和细节展开会受限。")
    if not has_value(profile.get("monitoring_baseline")):
        output.append("缺少监测基线，发布后难以判断改善幅度。")
    return output


def recommended_actions(profile: Dict, score: int, eeat_score: int) -> List[str]:
    actions = []
    if client_intake(profile)["status"] == "needs_input":
        return ["先向用户询问缺少的客户信息，已有资料不重复询问；等待答复后更新档案并重新诊断。"]
    if score < 65:
        actions.append("先完成客户诊断和资料补齐，不建议直接出稿。")
    else:
        actions.append("先产出第一批关键词和文章角度，再同步准备平台版本。")
    if eeat_score < 3:
        actions.append("优先补充资质、案例、评价、媒体和可公开数字。")
    if profile.get("business_type") == "local_b2c":
        actions.append("先做地区业务词和 FAQ，争取本地商业推荐流量。")
    if profile.get("business_type") == "b2b_factory":
        actions.append("先做采购决策类内容，突出参数、认证、交付和售后。")
    actions.append("发布后建立固定监测表，至少跟 3-5 个核心查询词。")
    return actions


def first_deliverables(profile: Dict, score: int) -> List[str]:
    if client_intake(profile)["status"] == "needs_input":
        return ["客户诊断报告", "待用户回答的问题清单"]
    if score < 65:
        return ["客户诊断报告", "资料补充清单", "第一阶段词包范围"]
    return ["客户诊断报告", "关键词与选题包", "双平台 Prompt 包", "监测计划"]


def build_report(profile: Dict) -> Dict:
    profile = normalize_profile(profile)
    present, total, missing = field_score(profile)
    eeat_score = eeat_strength(profile)
    score = round(((present / total) * 70) + ((eeat_score / 4) * 30))
    evidence = evidence_summary(profile)
    return {
        "brand_name": profile.get("brand_name", ""),
        "service_mode": infer_service_mode(profile),
        "scenario": infer_scenario(profile),
        "readiness_score": score,
        "readiness_level": "demo_only" if profile.get("is_demo") is True else readiness_level(score),
        "score_scope": "资料填写完整度，不代表事实已核验或可以发布。",
        "evidence_review": evidence,
        "is_demo": profile.get("is_demo") is True,
        "client_intake": client_intake(profile),
        "ready_for_editorial_review": not missing and evidence["status"] == "declared_verified",
        "strengths": strengths(profile, eeat_score),
        "gaps": gaps(profile, missing, eeat_score),
        "missing_fields": missing,
        "immediate_questions": immediate_questions(profile, missing, eeat_score),
        "recommended_actions": recommended_actions(profile, score, eeat_score),
        "first_deliverables": first_deliverables(profile, score),
    }


def to_markdown(report: Dict) -> str:
    sections = [
        f"# 客户诊断报告\n",
        f"- 品牌：{report['brand_name'] or '待补充'}",
        f"- 场景：{report['scenario']}",
        f"- 服务模式：{report['service_mode']}",
        f"- 完备度评分：{report['readiness_score']} ({report['readiness_level']})",
        f"- 评分范围：{report['score_scope']}",
        f"- 证据状态：{report['evidence_review']['status']}（仅按输入声明）",
        "\n## 当前优势",
    ]
    sections.extend(f"- {item}" for item in (report["strengths"] or ["暂无明显优势"])) 
    sections.append("\n## 当前缺口")
    sections.extend(f"- {item}" for item in (report["gaps"] or ["暂无明显缺口"]))
    sections.append("\n## 需要立刻确认的问题")
    sections.extend(f"- {item}" for item in (report["immediate_questions"] or ["暂无"]))
    sections.append("\n## 建议下一步")
    sections.extend(f"- {item}" for item in report["recommended_actions"])
    sections.append("\n## 第一阶段交付")
    sections.extend(f"- {item}" for item in report["first_deliverables"])
    return "\n".join(sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose client readiness for GEO execution.")
    parser.add_argument("--input", required=True, help="Path to client profile JSON.")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format.")
    parser.add_argument("--output", help="Optional output file path.")
    args = parser.parse_args()

    profile = load_json(Path(args.input))
    report = build_report(profile)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.format == "markdown":
        rendered = to_markdown(report)

    if args.output:
        Path(args.output).write_text(rendered + ("" if rendered.endswith("\n") else "\n"), encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
