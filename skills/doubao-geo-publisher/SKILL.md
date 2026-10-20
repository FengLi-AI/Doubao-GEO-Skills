---
name: doubao-geo-publisher
description: 围绕豆包搜索组织客户诊断、关键词、文章计划、平台检查和监测复盘时使用。适用于完整 GEO 内容运营任务。
---

# 豆包 GEO 工作流

组织客户资料、关键词、写作、平台编辑与研究记录，区分规划产物和真实发布/搜索结果。总入口不代表无人值守自动执行。

## 先询问缺失信息

先读取本次对话与用户已提供的材料。没有客户档案时，先向用户询问品牌、行业、业务类型、核心产品或服务、服务区域，再了解目标读者与本轮目标；仅补问缺失或矛盾项。使用 [询问清单](assets/intake_questionnaire.template.md) 分轮沟通，把答复填入 [空白档案](assets/client_profile.template.json)。必要信息未齐备时输出问题并等待答复，不代填客户资料，不生成依赖它的计划。

正式任务只使用本次用户提供的资料。仅在用户明确要求演示或运行测试时使用独立示例；示例不能作为客户默认值。

## 输入与路径

读取客户档案、目标和已提供证据。五个 Skill 需要同级安装，共享规则在本目录 `scripts/geo_core.py`。下方命令以仓库根目录为工作目录；安装后按当前 Skill 的实际路径定位脚本。

## 工作流程

1. 用 `scripts/diagnose_client.py` 检查字段完整度和证据声明。占位值不算有效信息；虚构样例不能作为真实客户证据。
2. 用 `scripts/generate_geo_plan.py` 生成计划；它复用 `$geo-keyword-miner` 的关键词实现。人工筛选候选。
3. 用 `$geo-doubao-research` 抽取查询词，按用户授权采集发布前记录。
4. 用 `scripts/build_prompt_packet.py` 组装提示词，再由 `$geo-article-writer` 生成 Brief 和主稿。
5. 用 `$geo-platform-adapter` 做预处理，继续逐平台编辑并校验。
6. 发布和账号操作需要用户授权。采集同词发布后记录，再比较和复盘。

## 本地命令

```bash
python3 skills/doubao-geo-publisher/scripts/diagnose_client.py --input /path/to/profile.json --format markdown
python3 skills/doubao-geo-publisher/scripts/generate_geo_plan.py --input /path/to/profile.json --output /path/to/plan.json
python3 skills/doubao-geo-publisher/scripts/build_prompt_packet.py --profile /path/to/profile.json --keyword "目标查询词" --article-type selection --platform toutiao --output /path/to/prompt.txt
python3 skills/doubao-geo-publisher/scripts/run_closed_loop_demo.py --profile /path/to/profile.json --publish-dir /path/to/platforms --output-dir /path/to/validation
```

最后一个命令只验证本地产物：退出码 0 为通过规则检查，1 为失败，2 为缺客户信息或缺文章等未完成状态。不得把通过写成真实收录或获客结果。

## 按需参考

- 档案与证据：[字段说明](references/client-profile-schema.md)、[接待流程](references/client-service-playbook.md)。
- 写作：[文章类型](references/article-patterns.md)、[五类文章规范](../geo-article-writer/references/article-generation-rules.md)。
- 编辑：[平台策略](references/platform-rules.md)。
- 研究：[监测](references/monitoring-playbook.md)、[浏览器](references/browser-automation.md)。
- 验收：[状态语义](references/closed-loop-validation.md)、[交付标准](references/delivery-standards.md)。
