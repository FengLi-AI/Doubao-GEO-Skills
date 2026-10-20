---
name: geo-keyword-miner
description: 把客户档案或公司家底表转成带商业意图、优先级和文章类型建议的 GEO 关键词候选表时使用。
---

# GEO 关键词挖掘

根据业务和用户问法生成候选词，交给人工筛选。不把规则拼接结果描述为真实搜索量或已验证需求。

## 先询问缺失信息

先读已有资料；品牌、行业、业务类型、实际服务区域、核心产品或服务缺失时，直接向用户询问缺项并等待答复。不要默认全国、混合业务或“核心业务”。目标客户和真实问法按需补问；已有信息不重复询问。

正式任务只使用本次用户提供的资料。仅在用户明确要求演示或运行测试时使用独立示例；示例不能作为客户默认值。

## 工作流程

1. 读取品牌、业务类型、服务区域、核心服务/产品和完整用户问法。
2. 支持 local_b2c、national_brand、b2b_factory、hybrid；常见中文枚举会归一化。
3. 生成候选表，检查是否准确覆盖业务、是否通顺、有无重复意图。
4. 将筛选后的词交给 `$geo-article-writer` 或 `$geo-doubao-research`。

```bash
python3 skills/geo-keyword-miner/scripts/generate_keyword_table.py --profile /path/to/profile.json --output /path/to/keywords.csv --limit 24
```

命令从仓库根目录运行；安装后使用实际脚本路径。五个 Skill 同级安装以找到共享字段规则。

CSV 字段：客户ID、品牌名、核心关键词、意图层级、优先级、公式类型、推荐文章类型、平台建议。

细节见 [关键词规则](references/keyword-rules.md)。通用科普文章可以服务商业查询的解释需求，但不要为凑词扩展无业务关系的泛话题。
