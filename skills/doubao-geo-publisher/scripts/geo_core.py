"""Shared data and editorial rules for the five bundled skills (stdlib only)."""
from __future__ import annotations

import json
import re
from pathlib import Path


ARTICLE_TYPES = {
    "cognitive": ("认知科普型", ["真实问题与定义", "常见误解", "判断框架", "有证据的样本", "结论"]),
    "selection": ("选择判断型", ["选择困难", "判断维度", "证据与适配场景", "结果边界", "建议"]),
    "observation": ("行业观察型", ["变化背景", "有来源的趋势", "能力与选择逻辑", "具体样本", "结论"]),
    "outcome": ("案例成果型", ["如何看成果", "案例过程", "可核验材料", "适用条件与结果边界"]),
    "profile": ("人物机构型", ["搜索意图", "身份与关系", "可核验经历", "案例与课程或服务体系"]),
}
ARTICLE_ALIASES = {
    "guide": "selection", "procurement": "selection", "analysis": "observation", "annual": "observation",
    "选购指南": "selection", "采购决策": "selection", "行业深度分析": "observation", "年度盘点": "observation",
    **{value[0]: key for key, value in ARTICLE_TYPES.items()},
}
BUSINESS_ALIASES = {
    "local_b2c": "local_b2c", "本地b2c": "local_b2c", "本地": "local_b2c",
    "national_brand": "national_brand", "全国品牌": "national_brand", "全国": "national_brand",
    "b2b_factory": "b2b_factory", "b2b工厂制造": "b2b_factory", "b2b": "b2b_factory",
    "hybrid": "hybrid", "混合型": "hybrid", "混合": "hybrid",
}
PLATFORMS = ("toutiao", "sohu", "zhihu", "36kr")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?86[-\s]?)?(?:1[3-9]\d{9}|\d{3,4}[-\s]?\d{7,8})(?!\d)")
SOHU_TITLE_TERMS = ("排行榜", "TOP", "排名", "排行", "榜", "推荐", "靠谱", "权威", "首选", "头部")
INTERNAL_TERMS = ("客户资料显示", "补充材料显示", "客户资料", "资料口径", "实体链", "目标达成词", "我们要绑定", "关键词布局", "豆包优化")
GENERAL_TERMS = ("最好", "最佳", "绝对", "永久", "100%", "独家", "首创", "全国领先", "行业第一")
INDUSTRY_TERMS = {
    "medical": ("治愈率100%", "永不复发", "免费治疗", "优惠手术", "买一赠一"),
    "education": ("保就业", "包就业", "保证就业", "保证涨薪", "保过", "包过", "不过退费", "100%就业"),
}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def has_value(value):
    if value is None or value is False:
        return False
    if isinstance(value, str):
        text = value.strip()
        return bool(text) and not re.match(
            r"^(待补充|待填写|待确认|待核验|待提供|示例|某某|请填写|请替换|TBD\b|TODO\b|unknown$|N/?A$|<|\{)", text, re.I
        )
    if isinstance(value, (list, tuple)):
        return any(has_value(v) for v in value)
    if isinstance(value, dict):
        return any(has_value(v) for k, v in value.items() if k not in ("status", "verified", "is_demo"))
    return True


def as_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        value = re.split(r"[\n,，;；、]+", value)
    if not isinstance(value, list):
        raise ValueError("Expected a list or a comma-separated string.")
    return list(dict.fromkeys(str(v).strip() for v in value if str(v).strip()))


def normalize_business(value):
    key = str(value).strip().lower()
    if key not in BUSINESS_ALIASES:
        raise ValueError(f"Unsupported business_type: {value!r}")
    return BUSINESS_ALIASES[key]


def normalize_profile(profile):
    if not isinstance(profile, dict):
        raise ValueError("Client profile must be a JSON object.")
    result = dict(profile)
    aliases = {
        "client_id": ("客户ID",), "brand_name": ("品牌全称", "品牌名"), "brand_short": ("品牌简称",),
        "industry": ("行业",), "business_type": ("业务类型", "biz_type"), "service_area": ("服务区域", "服务城市", "primary_city", "city"),
        "core_services": ("核心服务",), "core_products": ("核心产品",), "target_customers": ("目标客户",),
        "competitors": ("竞品列表",), "business_desc": ("核心业务描述", "core_business"),
    }
    for key, alternatives in aliases.items():
        if not has_value(result.get(key)):
            for alias in alternatives:
                if has_value(result.get(alias)):
                    result[key] = result[alias]
                    break
    if has_value(result.get("business_type")):
        result["business_type"] = normalize_business(result["business_type"])
    else:
        result["business_type"] = ""
    for key in ("service_area", "core_services", "core_products", "target_customers", "competitors",
                "customer_language", "objectives", "channels", "brand_terms", "content_assets", "pain_points"):
        result[key] = [value for value in as_list(result.get(key)) if has_value(value)]
    return result


CLIENT_QUESTIONS = {
    "brand_name": "本次服务的品牌或机构叫什么？请提供准确名称。",
    "industry": "品牌属于哪个行业？",
    "business_type": "主要业务是本地服务、全国品牌、B2B 工厂制造，还是混合业务？",
    "offerings": "本次要推广哪些具体产品或服务？也可以先用自己的话描述业务。",
    "service_area": "实际服务哪些地区？如果覆盖全国，请明确说明。",
    "target_customers": "希望触达哪些客户或读者？他们最关心什么问题？",
    "objectives": "这次 GEO 内容希望解决什么问题，例如业务咨询、品牌介绍或采购线索？",
}


def client_intake(profile, scope="planning"):
    """Return only unanswered questions; never load or invent client data."""
    if scope not in ("keywords", "planning", "writing"):
        raise ValueError(f"Unsupported intake scope: {scope}")
    profile = normalize_profile(profile)
    fields = list(CLIENT_QUESTIONS)[:5]
    if scope != "keywords":
        fields += ["target_customers", "objectives"]
    missing = []
    for field in fields:
        value = (profile.get("core_services") or profile.get("core_products") or profile.get("business_desc")) \
            if field == "offerings" else profile.get(field)
        if not has_value(value):
            missing.append(field)
    return {
        "status": "needs_input" if missing else "ready",
        "scope": scope,
        "missing_fields": missing,
        "questions": [{"field": field, "question": CLIENT_QUESTIONS[field]} for field in missing],
    }


class ClientInputRequired(ValueError):
    def __init__(self, intake):
        self.intake = intake
        super().__init__("请先向用户询问以下客户信息，再继续生成：\n" +
                         "\n".join("- " + item["question"] for item in intake["questions"]))


def require_client_input(profile, scope="planning"):
    intake = client_intake(profile, scope)
    if intake["status"] == "needs_input":
        raise ClientInputRequired(intake)


def canonical_article_type(value):
    key = ARTICLE_ALIASES.get(value, value)
    if key not in ARTICLE_TYPES:
        raise ValueError(f"Unsupported article type: {value!r}")
    return key


def evidence_summary(profile):
    sources = profile.get("verified_sources") or []
    valid = [
        item for item in sources if isinstance(item, dict)
        and item.get("status") == "verified"
        and has_value(item.get("source")) and has_value(item.get("fact"))
        and has_value(item.get("url") or item.get("evidence_path"))
    ]
    demo = profile.get("is_demo") is True
    return {
        "status": "synthetic" if demo else ("declared_verified" if valid else "unverified"),
        "declared_verified_count": 0 if demo else len(valid),
        "note": "只检查输入中的状态和定位字段，不验证事实真伪或链接内容。",
    }


def split_article(text):
    """Remove a dedicated publishing-settings section at any position.

    The section ends at a horizontal rule, an equal/higher heading, or EOF.
    Its content is returned separately for an evidence sidecar.
    """
    body, settings = [], []
    settings_level = None
    fenced = False
    for line in text.splitlines():
        heading = re.match(r"^(#{1,6})\s+(.+)$", line.strip()) if not fenced else None
        if heading and re.fullmatch(r"发布设置[（(]不复制到正文[）)]", heading.group(2).strip()):
            settings_level = len(heading.group(1))
            continue
        if settings_level is not None:
            if re.fullmatch(r"\s*---+\s*", line):
                settings_level = None
                continue
            if heading and len(heading.group(1)) <= settings_level:
                settings_level = None
            else:
                settings.append(line)
                continue
        body.append(line)
        if line.lstrip().startswith("```"):
            fenced = not fenced
    return "\n".join(body).strip(), "\n".join(settings).strip()


def title_body(text):
    public, settings = split_article(text)
    lines = public.splitlines()
    for index, line in enumerate(lines):
        if line.strip():
            title = re.sub(r"^#+\s*", "", line.strip())
            title = re.sub(r"^(?:今日头条|头条|搜狐号?|知乎|36氪|主稿|文章)?标题[：:]\s*", "", title)
            return title, "\n".join(lines[index + 1:]).strip(), settings
    return "", "", settings


def neutral_title(title, platform):
    # This is the repository's conservative editorial policy, not a platform ban list.
    if platform == "sohu":
        for term in SOHU_TITLE_TERMS:
            title = re.sub(re.escape(term), "", title, flags=re.I)
    return re.sub(r"[ \t]+", " ", title).strip()


def check_article(title, body, platform, industry="general", keyword="", evidence=""):
    if platform not in PLATFORMS:
        raise ValueError(f"Unknown platform: {platform}")
    public, settings = split_article(body)
    merged = title + "\n" + public
    issues = []

    def add(code, severity, message):
        issues.append({"code": code, "severity": severity, "message": message})

    if not title.strip() or not public.strip():
        add("empty_article", "error", "标题或正文为空。")
    if len(title) > 30:
        add("long_title", "warning", "标题较长，请人工判断是否需要压缩。")
    if any(term in merged for term in INTERNAL_TERMS) or re.search(r"\b(?:EEAT|GEO|SEO)\b", merged, re.I):
        add("internal_terms", "error", "发布正文含内部流程措辞，请复核。")
    hits = [term for term in GENERAL_TERMS if term in merged]
    if hits:
        add("absolute_claim", "warning", "需结合上下文核查的表述：" + "、".join(hits))
    if any(term in merged for term in INDUSTRY_TERMS.get(industry, ())):
        add("industry_claim", "error", "发现本仓库规则标记的行业结果承诺，请人工复核。")
    if industry not in ("general", "medical", "education"):
        add("industry_review", "warning", "当前行业没有专用规则集，须人工复核行业要求。")
    if platform == "sohu":
        if any(re.search(re.escape(t), title, re.I) for t in SOHU_TITLE_TERMS):
            add("sohu_title_policy", "error", "标题不符合本仓库的搜狐中性表达策略。")
        if PHONE_RE.search(merged):
            add("sohu_phone_policy", "error", "本仓库的搜狐版本默认不保留电话。")
        if industry == "medical" and "医院排名" in merged:
            add("medical_ranking", "error", "医疗排名表达需人工处理。")
    if keyword and keyword not in public:
        add("keyword_missing", "warning", "正文未逐字出现目标词；请人工核对语义覆盖，不要求机械堆词。")
    evidence_text = "\n".join((evidence, settings))
    if not evidence_text.strip() and not any(t in public for t in ("参考来源", "参考资料", "https://", "http://")):
        add("evidence_missing", "warning", "请提供来源清单；可以使用独立证据文件，无须堆在正文末尾。")
    return issues
