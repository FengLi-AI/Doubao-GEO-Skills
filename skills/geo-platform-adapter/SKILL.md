---
name: geo-platform-adapter
description: 把中文主稿适配为头条、搜狐、知乎、36氪版本，处理发布设置、联系方式和本地编辑规则，并准备文章清单时使用。
---

# GEO 平台适配

先用脚本做确定性预处理，再由 AI 或人工完成语气、结构和证据表达的编辑。输出四个文件不代表已经完成四篇深度改写。

```bash
python3 skills/geo-platform-adapter/scripts/adapt_platform_versions.py --input /path/to/article.md --evidence /path/to/evidence.md --output-dir /path/to/platforms --keyword "目标查询词" --industry general
```

从仓库根目录运行；安装后使用实际路径，保留五个同级 Skill。

## 先询问缺失信息

先读用户提供的主稿与材料。主稿、目标平台、相关行业背景或待保留的客户表述不清楚时，仅向用户询问影响本次适配的缺项；无需重问完整客户档案。不得自行替换客户身份、地区、业绩或来源。

正式任务只使用本次用户提供的资料。仅在用户明确要求演示或运行测试时使用独立示例；示例不能作为客户默认值。

## 工作流程

1. 读取主稿、来源、行业和平台要求。
2. 运行脚本分离发布设置、处理标题与电话，生成稿件、`article.sources.txt`、`article-manifest.json` 和规则报告。
3. 逐平台编辑：头条关注问题和场景；搜狐采用中性表达；知乎补论证；36氪补产业/商业材料。缺材料时明确列缺口。
4. 不改变有来源的事实，不对正文做无差别词语替换。
5. 用总流程检查或 `platform_guard.py` 再检查，并人工核实事实和平台当前要求。

## 状态

脚本返回 0 表示机械检查未发现 error，返回 1 表示文件已生成但需要修复错误。发布授权、事实核验和平台审核都是独立步骤。

平台默认策略见 [平台规则](references/platform-rules.md)。这些策略不等于官方禁词列表；不强制年份、数字或固定关键词频率。
