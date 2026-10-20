# 数据与记录格式

## 客户档案

正式项目从空白档案开始，先向用户询问并填写缺少的信息。见[客户资料收集](client-intake.md)。独立测试数据只放在 `examples/local-service/`，正式工作流不会自动读取。

| 字段 | 类型 | 说明 |
|---|---|---|
| client_id / brand_name | string | 客户标识、品牌全称 |
| is_demo | boolean | 正式档案为 false；仅独立离线演示数据为 true |
| client_stage | string | 用户说明的阶段；未说明时留空 |
| objectives / target_customers | string[] | 目标与读者 |
| conversion_goal | string | 内容需要承接的动作 |
| industry | string | 行业 |
| business_type | string | local_b2c / national_brand / b2b_factory / hybrid |
| service_area / core_services / core_products | string[] | 区域、服务、产品 |
| customer_language | string[] | 完整的真实问法，生成器不会再机械追加地区与动作词 |
| eeat | object | expertise / experience / authority / trust，各为字符串列表 |
| verified_sources | object[] | 见下文；名称保留兼容旧输入，数组内容仍按每条状态判断 |
| compliance.industry_sensitivity | string | general / medical / education / finance / legal 等；后两者尚无专门规则集 |

常用中文字段“品牌全称、业务类型、服务城市、核心服务、目标客户”等可被归一化；`本地B2C`、`全国品牌`、`B2B工厂制造`、`混合型` 映射到英文枚举。未填写时向用户询问，不默认混合业务；不认识的非空类型会报错。`business_type`、`client_stage`、行业敏感度未提供时均留空。关键词必需品牌、行业、业务类型、区域及具体服务/产品（也可提供 business_desc）；计划和 Prompt 还需目标读者与内容目标。

## 证据

每条来源包含：

```json
{
  "source": "可定位的来源名称",
  "date": "",
  "fact": "来源支持的具体事实",
  "url": "",
  "evidence_path": "",
  "status": "unverified"
}
```

`status` 可用 `unverified`、`verified`、`synthetic`。已核验条目需要非占位的来源名称、事实和至少一个 URL/材料路径。

- `synthetic`：演示数据，不能用作真实项目证据。
- `unverified`：尚未完成核验。
- `declared_verified`：诊断输出状态，表示至少一条输入标记 verified 且定位字段完整；程序没有打开来源或核实事实。

完整度、证据状态、文章规则检查和发布决定相互独立。“待补充可核查证据”等占位描述不计为有效填写。增加无意义字符串也不能替代人工事实核验。

## 文章和清单

每个 Markdown 文件一篇平台稿，首行为 `# 标题`。内部发布设置使用独立来源文件，或单独的 `## 发布设置（不复制到正文）` 节，结束于下一个同级/更高标题、分隔线或文件末尾。

```json
[
  {
    "file": "toutiao.md",
    "platform": "toutiao",
    "keyword": "本次查询词",
    "evidence_file": "article.sources.txt"
  }
]
```

平台枚举：`toutiao`、`sohu`、`zhihu`、`36kr`。清单内文件名唯一；来源文件位于文章目录内。草稿仍需逐平台编辑。

## 研究日志

文件顶部保存 `project`、`client_id`、`brand_name`、`stage`、`data_kind`、采集时间等字段。

- 每条效果记录以 `## Query: 完整查询词` 开始。
- `target_brand_seen` 手工填写 `yes / partial / no / unknown`；unknown 不会因正文出现品牌文字而自动转为 yes。
- `brand_recommended` 和 `own_content_cited` 单独记录，不能用“出现品牌”代替。
- 回答放在 answer 代码块；引用 URL、截图、搜索模式单独记录。
- 每条竞品来源以 `## Source: 标题` 开始，原文或摘录放 article 代码块。
- 空白模板块不计为有效记录。同批同词重复时先拆分轮次。
- `data_kind: synthetic` 标记虚构样例；真实采集可以用 `observed`，仍需人工核验。

Excel 的字段用于人工记录；脚本直接读取 JSON、CSV 和约定格式的 Markdown，不直接读写 Excel。
