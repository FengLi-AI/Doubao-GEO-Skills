# Doubao-GEO-Skills

面向中文 GEO 内容运营的五个 AI Skills，覆盖客户诊断、关键词规划、文章写作、多平台适配和豆包搜索复盘，配套客户询问清单、空白档案、Python 脚本与 Excel 模板。

当前版本：`0.1.0`。本项目提供本地工具和人工参与的研究流程，不承诺品牌收录、推荐排名或获客效果，与豆包及所提及的平台无官方关联。

## 五个 Skill

| Skill | 用途 | 可执行能力 |
|---|---|---|
| [doubao-geo-publisher](skills/doubao-geo-publisher/SKILL.md) | 总流程、客户诊断与计划 | 诊断、选题、Prompt、规则检查、监测计划、本地验证 |
| [geo-keyword-miner](skills/geo-keyword-miner/SKILL.md) | 商业关键词候选 | 按业务类型生成 CSV；不提供搜索量或排名数据 |
| [geo-article-writer](skills/geo-article-writer/SKILL.md) | 证据驱动的文章写作 | 由支持 Skill 的 AI 助手执行 Brief 和写作规范 |
| [geo-platform-adapter](skills/geo-platform-adapter/SKILL.md) | 头条、搜狐、知乎、36氪适配 | 机械预处理、独立来源文件、文章清单与规则报告 |
| [geo-doubao-research](skills/geo-doubao-research/SKILL.md) | 豆包诊断与复盘 | 检验词抽取、人工采集日志解析、前后比较与信源汇总 |

典型流程：询问缺失信息 → 用户提供客户资料 → 关键词筛选 → 发布前记录 → AI 写稿 → 平台编辑 → 人工发布 → 发布后记录 → 同词比较与复盘。

## 快速开始：先询问客户信息

下载并解压仓库，进入 `Doubao-GEO-Skills` 目录执行命令。使用 Python 3.10 或更高版本；脚本只依赖标准库。Windows 可将 `python3` 替换为 `py -3`。

五个 Skill 共用少量规则代码，请整套安装，保持五个目录在同一父目录下。可以直接让助手读取仓库中的对应 `SKILL.md`，也可以复制到助手的 Skills 目录。

例如 Codex：

```bash
# 先预览目标；已有同名 Skill 时脚本会拒绝覆盖。
python3 scripts/install_skills.py --destination ~/.codex/skills --dry-run
python3 scripts/install_skills.py --destination ~/.codex/skills
```

设置过 `CODEX_HOME` 时，把目标改成该目录下的 `skills`。其他助手的安装路径按其文档配置。安装后让客户端重新加载 Skills。

安装后直接提出任务，无需提前编造或套用一份客户资料：

> 使用 $doubao-geo-publisher 帮我做 GEO 内容规划。先读取我已有的材料，向我询问缺少的客户信息，必要信息齐备后再生成关键词和计划。不要发布。

> 使用 $geo-article-writer 写一篇选择判断型文章。先询问缺少的客户背景、读者问题和来源，不要替我编造客户资料。

> 使用 $geo-doubao-research，对比这两份同品牌、同查询词的人工记录，缺少基线的词标为不可比较。

正式使用从[空白档案](skills/doubao-geo-publisher/assets/client_profile.template.json)开始。助手只询问本轮缺少的信息；必要信息未齐备时先输出问题并等待答复，不会把区域默认成全国或自动使用示例。完整说明见[客户资料收集](docs/client-intake.md)。

## 可选：独立离线演示

下载并解压仓库，进入 `Doubao-GEO-Skills` 目录。使用 Python 3.10 或更高版本；本地脚本只依赖标准库，不需要 API Key 或 `pip install`。

```bash
python3 scripts/run_offline_demo.py --output-dir work/demo
```

Windows 可以把 `python3` 替换为 `py -3`。命令必须在仓库根目录运行。输出目录须为空或不存在；再次演示请换一个目录，例如 `work/demo-02`。

示例中的品牌、城市、服务资料和搜索回答全部虚构。演示不会联网、调用模型、登录账号或发布文章。

输出包括：

- `keywords.csv`、`queries.md`：候选关键词与检验词。
- `platforms/`：四份待编辑稿、来源清单、`article-manifest.json`。
- `showcase/`：客户诊断、内容计划、Prompt、文章检查和本地汇总。
- `pre-report.md`、`post-report.md`、`comparison.md`、`competitor-report.md`。

正常演示应检查到 4 篇文章，`showcase/showcase-summary.json` 的 `overall_status` 为 `passed`，同时明确 `is_demo: true`、`publication_status: not_performed`、`search_effect_status: not_evaluated`。这里的通过只表示本地步骤完成。

## 能力边界

- Python 脚本生成规划材料、机械适配稿和结构化报告；正文生成需要 AI 助手或人工。
- 平台版本仍需编辑，尤其是知乎论证和 36氪产业材料；产生四个文件不等于四篇已审定文章。
- 豆包实际搜索、来源网页阅读、结果截图与日志填写由人工或用户授权的浏览器工具完成。
- 浏览器 Shell 脚本是可选入口，不包含自动查询轮询、验证码处理或发布。见[浏览器说明](docs/browser.md)。
- 飞书、Coze、广告投放和定时任务没有内置集成。
- 平台规则是本项目的保守编辑策略，不能代替平台现行要求或行业审核。

## 文档与模板

- [如何向用户询问客户信息](docs/client-intake.md)
- [从客户资料到报告的使用说明](docs/usage.md)
- [字段、证据状态和记录格式](docs/data-schema.md)
- [架构、共享依赖与状态说明](docs/architecture.md)
- [本地验证记录与范围](docs/validation.md)
- [平台策略与核验边界](docs/platform-policies.md)
- [迁移说明与变更记录](CHANGELOG.md)
- [独立离线测试案例](examples/local-service/README.md)
- [Excel 流程模板](templates/GEO自动化流程表格模板.xlsx)：9 张表，人工填写，不自动同步脚本。

## 开发与验证

```bash
python3 -m unittest discover -s tests -v
```

测试覆盖无文章误通过、平台输出与验收衔接、缺失/未知基线、占位证据、规则一致性等边界。CI 配置运行单元测试和离线演示，不访问豆包或发布平台。

## 许可证

本仓库的代码、Skill 文档和原创示例按 [MIT License](LICENSE) 提供。第三方平台、商标和用户后来加入的材料不因此获得额外授权。
