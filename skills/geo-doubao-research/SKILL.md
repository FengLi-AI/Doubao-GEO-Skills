---
name: geo-doubao-research
description: 从关键词与人工采集的豆包回答、引用来源记录生成发布前后报告、同词比较和竞品信源汇总时使用。
---

# 豆包 GEO 研究

研究模块负责查询批次和记录整理；真实搜索、网页阅读和截图依靠人工或用户授权的浏览器工具。脚本不会自行持续抓取豆包。

## 先询问缺失信息

先从当前材料确认目标品牌、实际查询词及研究阶段。缺失时向用户询问；比较任务缺记录时先索取记录，用户没有则保留“不可比较”。不要编造搜索回答、来源或发布前基线，也不要求与本次研究无关的完整客户档案。

正式任务只使用本次用户提供的资料。仅在用户明确要求演示或运行测试时使用独立示例；示例不能作为客户默认值。

## 工作流程

1. 从当前客户关键词表生成检验批次，避免使用固定演示词替代真实查询。
2. 记录品牌、查询词、时间、模式、回答、引用 URL 和截图。登录和账号安全步骤由用户处理。
3. 人工区分品牌被提及、品牌被推荐和自有内容被引用。
4. 发布前后尽量复用同词和条件。缺记录或 unknown 均标记不可比较；不同轮次拆开。
5. 对实际引用来源进行结构与证据分析，将结论回流到关键词和文章 Brief。

```bash
python3 skills/geo-doubao-research/scripts/select_doubao_queries.py --keywords /path/to/keywords.csv --profile /path/to/profile.json --output /path/to/queries.md
python3 skills/geo-doubao-research/scripts/build_doubao_research_report.py --mode effect --stage pre --input /path/to/log.md --output /path/to/report.md
python3 skills/geo-doubao-research/scripts/build_doubao_research_report.py --mode compare --pre /path/to/pre.md --post /path/to/post.md --output /path/to/comparison.md
python3 skills/geo-doubao-research/scripts/build_doubao_research_report.py --mode competitor --input /path/to/sources.md --output /path/to/source-report.md
```

从仓库根目录运行；安装后用实际脚本路径并保持五个 Skill 同级。

## 判断边界

只比较实际记录，不能把未采集当未出现。改善指记录中的出现状态变化，不代表推荐排名、获客效果或发文因果贡献。

## 按需材料

- [客户研究流程](references/customer-flow.md)、[浏览器操作](references/browser-operations.md)。
- [来源分类](references/source-taxonomy.md)、[内部复盘](references/internal-review-flow.md)。
- [效果日志](assets/effect-log.template.md)、[竞品日志](assets/competitor-source-log.template.md)、[反馈模板](assets/comparison-feedback.template.md)。
