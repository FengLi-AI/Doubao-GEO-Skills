#!/usr/bin/env python3
"""Build prompts, without calling a model or publishing content."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from geo_core import ARTICLE_TYPES, ARTICLE_ALIASES, ClientInputRequired, canonical_article_type, evidence_summary, normalize_profile, read_json, require_client_input


def build_prompt(profile, keyword, article_type, platform):
    profile = normalize_profile(profile)
    require_client_input(profile, "writing")
    article_type = canonical_article_type(article_type)
    if platform not in ("toutiao", "sohu", "both", "zhihu", "36kr"):
        raise ValueError("Unsupported platform.")
    evidence = evidence_summary(profile)
    source_lines = []
    for item in profile.get("verified_sources") or []:
        source_lines.append(
            f"- 状态={item.get('status', 'unverified')}；来源={item.get('source', '')}；"
            f"事实={item.get('fact', '')}；定位={item.get('url') or item.get('evidence_path', '')}"
        )
    structure = "\n".join("- " + value for value in ARTICLE_TYPES[article_type][1])
    facts = "\n".join(
        "- " + key + "：" + "；".join(str(v) for v in values)
        for key, values in (profile.get("eeat") or {}).items()
    )
    policy = {
        "toutiao": "先回答问题，段落清楚，联系方式仅在用户需要且已核验时使用。",
        "sohu": "采用中性标题，避免榜单与绝对化措辞；按本仓库策略去掉电话。",
        "zhihu": "解释判断依据与适用边界，不只添加固定开场白。",
        "36kr": "围绕产业、供需与商业逻辑组织材料；缺少这些材料时先列缺口。",
        "both": "分别组织头条与搜狐两版；搜狐采用中性标题并去掉电话。",
    }[platform]
    services = "；".join(profile.get("core_services", []) + profile.get("core_products", []))
    services = services or profile.get("business_desc", "")
    return f"""请作为中文编辑，先核对资料再生成文章。

[任务]
- 文章类型：{ARTICLE_TYPES[article_type][0]}
- 平台：{platform}
- 用户问题：{keyword}
- 品牌：{profile.get('brand_name', '')}
- 服务或业务描述：{services}
- 地区：{'；'.join(profile.get('service_area', []))}
- 目标读者：{'；'.join(profile.get('target_customers', []))}
- 目标：{'；'.join(profile.get('objectives', []))}

[材料状态]
- 虚构演示：{profile.get('is_demo') is True}
- 证据状态：{evidence['status']}；此状态来自输入声明，并非程序事实核验。
- 演示资料只能生成明确标注虚构的演示稿，不能当成真实客户成果。
- 未核验事实先列资料缺口，不补编数字、资质、评价或案例。
- 缺少写作依据时，先向用户询问来源和可公开范围；等待答复后再写依赖这些事实的内容。不能用示例客户代填。

[客户提供的证据描述]
{facts or '暂无，先补材料。'}

[来源记录]
{chr(10).join(source_lines) or '暂无可核验来源。'}

[参考结构]
{structure}

[编辑规则]
- {policy}
- 以上平台策略是本仓库编辑默认值，不是现行官方审核规则。
- 导语先回答读者问题；客户仅在相关且有证据时自然出现。
- 年份、数字、FAQ 按实际需要加入，人物身份类标题不机械加年份。
- 关键词以语义覆盖为先，不要求每隔固定字数重复。
- 发布正文不包含 GEO、EEAT、关键词布局、客户资料显示等内部工作措辞。
- 来源可放在正文适当位置或独立证据清单；不能把未核验描述改写成确定事实。
- 正文使用一个 Markdown 一级标题。
- 发布设置单列为“## 发布设置（不复制到正文）”；优先另交独立来源清单。

交付：Brief、标题与主稿、来源清单、仍待核验项。资料不足时先交缺口清单。"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--article-type", required=True, choices=sorted(set(ARTICLE_TYPES) | set(ARTICLE_ALIASES)))
    parser.add_argument("--platform", required=True, choices=["toutiao", "sohu", "both", "zhihu", "36kr"])
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        text = build_prompt(read_json(args.profile), args.keyword, args.article_type, args.platform)
    except ClientInputRequired as error:
        print(str(error), file=sys.stderr)
        return 2
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
