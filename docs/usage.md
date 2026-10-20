# 使用说明

所有命令从仓库根目录执行。纯 Python 部分不调用模型、不联网。正式使用先询问缺少的客户信息；离线演示是可选的独立验证入口。

## 1. 创建客户档案

先读取已有对话和材料，再按[客户资料收集流程](client-intake.md)向用户询问缺项。AI 助手或操作人员将用户答复填入 `skills/doubao-geo-publisher/assets/client_profile.template.json` 的工作副本，例如 `work/client.json`。品牌、业务类型、区域和客户阶段均不预设；不确定的字段留空并继续询问。

也可在 AI 助手中把 Excel 或原始资料整理成 JSON，转换后人工核对品牌、服务范围与证据。

```bash
python3 skills/doubao-geo-publisher/scripts/diagnose_client.py --input work/client.json --format markdown
```

完整度评分只衡量填写程度。`declared_verified` 表示输入声明了核验状态，并非脚本核实了事实。演示档案的 `is_demo: true` 必须保留；真实项目使用空模板并按实际情况填写。

## 2. 生成并筛选关键词

```bash
python3 skills/geo-keyword-miner/scripts/generate_keyword_table.py --profile work/client.json --output work/keywords.csv --limit 24
python3 skills/doubao-geo-publisher/scripts/generate_geo_plan.py --input work/client.json --output work/geo-plan.json
```

必要信息不全时返回退出码 2，并在终端列出需要向用户询问的问题，不写新产物。关键词需要品牌、行业、业务类型、产品/服务、区域；内容计划还需要目标读者和目标。补充后重新运行。

两条命令共用关键词生成逻辑：第一条提供表格，第二条附加文章角度和检验词。候选不含真实搜索需求数据，人工删除不通顺、不符合业务或重复意图的词。

## 3. 记录发布前状态

```bash
python3 skills/geo-doubao-research/scripts/select_doubao_queries.py --keywords work/keywords.csv --profile work/client.json --output work/queries.md
```

从 `templates/effect-log.template.md` 复制一份日志。逐词搜索，记录原始回答、时间、来源 URL、截图和人工判断。尽量保持查询词、搜索模式和采集条件一致；不同轮次分开文件。

```bash
python3 skills/geo-doubao-research/scripts/build_doubao_research_report.py --mode effect --stage pre --input work/pre-log.md --output work/pre-report.md
```

## 4. 生成 Prompt 并写主稿

```bash
python3 skills/doubao-geo-publisher/scripts/build_prompt_packet.py --profile work/client.json --keyword "目标查询词" --article-type selection --platform toutiao --output work/prompt.txt
```

把 Prompt 与证据交给 AI 助手，并让它读取 `geo-article-writer/SKILL.md`。关键事实缺来源时，向用户询问并等待必要答复，再写相关内容。主稿保存成 `work/article.md`，首行使用 `# 标题`，来源另存 `work/evidence.md`。

五类文章：`cognitive` 认知科普、`selection` 选择判断、`observation` 行业观察、`outcome` 案例成果、`profile` 人物机构。

## 5. 平台预处理与编辑

```bash
python3 skills/geo-platform-adapter/scripts/adapt_platform_versions.py --input work/article.md --evidence work/evidence.md --output-dir work/platforms --keyword "目标查询词" --industry general
```

输出四份稿件、`article.sources.txt`、`article-manifest.json` 和 `platform-report.json`。发布设置会从稿件正文分离到来源文件。脚本不生成深度平台改写，继续编辑四份稿件后再验收。

发现规则错误时仍会写出文件与报告，并以退出码 1 提醒处理。每批文章使用独立输出目录，避免旧稿混入。

## 6. 验证本地交付材料

```bash
python3 skills/doubao-geo-publisher/scripts/run_closed_loop_demo.py --profile work/client.json --publish-dir work/platforms --output-dir work/validation --industry general
```

每次使用新的或空的输出目录，避免旧产物混入。缺客户基础信息时只输出诊断、询问清单和未完成汇总（`input_status: needs_input`），等待用户补充后再运行。

它会自动读取文章目录里的清单，也支持 `--article-manifest` 指定文件。清单每条含 `file`、`platform`、`keyword`、可选 `evidence_file`。标准四个平台文件名可直接识别；其他文件名须明确平台，不能被静默跳过。

退出码：

| 退出码 | 状态 | 含义 |
|---|---|---|
| 0 | passed | 本地计划生成成功，至少一篇文章完成规则检查且无 error |
| 1 | failed | 检查发现错误，或输入/运行失败 |
| 2 | incomplete | 缺客户必要信息、未提供文章或目录没有文章；不会算作通过 |

汇总中线上发布和搜索效果始终单列为未执行、未评估。人工事实核验和发布判断仍是独立步骤。

## 7. 发布后记录与比较

发布和账号操作按用户明确授权执行。按同批查询词采集新日志，再运行：

```bash
python3 skills/geo-doubao-research/scripts/build_doubao_research_report.py --mode effect --stage post --input work/post-log.md --output work/post-report.md
python3 skills/geo-doubao-research/scripts/build_doubao_research_report.py --mode compare --pre work/pre-log.md --post work/post-log.md --output work/comparison.md
```

前后品牌须一致；同批关键词不能重复。缺少一侧记录或任一侧为 unknown 时标记“不可比较”。“改善”只描述人工标记的品牌出现程度变化，不证明发文导致了变化。

## 8. 竞品信源复盘

复制 `templates/competitor-source-log.template.md`，填实际引用来源及阅读记录。

```bash
python3 skills/geo-doubao-research/scripts/build_doubao_research_report.py --mode competitor --input work/competitors.md --output work/competitor-report.md
```

脚本统计本次收集样本。进一步的网页阅读和结构分析交给 AI 或人工，并把结论落实到 Brief、证据和查询词；不把少量样本统计写成平台整体偏好。

## 常见问题

- 找不到共享模块：五个 Skill 必须同级存放，不能只复制单个脚本。
- 路径错误：确认位于仓库根目录；其他目录调用请使用脚本绝对路径。
- JSON 解析失败：检查逗号、引号和列表结构；支持 UTF-8 与 UTF-8 BOM。
- 核验来源放在独立文件：给适配器或检查器传 `--evidence`，不要求正文硬塞参考来源段落。
- 旧“头条标题：/搜狐号标题：”合并稿：先拆成每个平台一个 Markdown 文件，补清单后再检查。
- 浏览器无法打开或需要登录：按浏览器说明排查；本地 Python 流程可独立运行。
