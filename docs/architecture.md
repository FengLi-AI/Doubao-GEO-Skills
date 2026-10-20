# 架构与维护

## 目录

```text
Doubao-GEO-Skills/
├── skills/                 五个同级 Skill，整套安装
├── templates/              客户、Brief、研究日志与 Excel 模板
├── examples/local-service/ 全部虚构的离线案例
├── scripts/                安装与离线演示入口
├── tests/                  有行为断言的回归测试
└── docs/                   使用、字段、平台和浏览器说明
```

## 共享规则

`skills/doubao-geo-publisher/scripts/geo_core.py` 维护客户字段归一化、缺项询问与生成前检查、占位值识别、五类文章映射、发布设置分离、平台稿基础检查。

关键词生成的唯一实现位于 `geo-keyword-miner/scripts/generate_keyword_table.py`，总流程导入它追加内容规划。平台适配器与验收脚本共用 `geo_core.check_article`。

因此安装时五个目录必须同级。不需要把仓库根目录加入 PYTHONPATH，也不安装第三方 Python 库。`geo_core.py` 是内部模块，不是第六个 Skill。

## 状态语义

- 输入状态：needs_input / ready；缺必要信息时仅输出询问清单、诊断及 incomplete 汇总，不继续生成。
- 资料完整度：字段是否填写，不能判断事实真假。
- 证据状态：synthetic / unverified / declared_verified。
- 文章检查：skipped / empty / completed / failed，skipped 和 empty 的 passed 为 null。
- 本地汇总：passed / failed / incomplete；只有实际检查了文章且没有 error 才可能 passed。
- 线上发布：本地演示固定 not_performed。
- 搜索效果：本地演示固定 not_evaluated。

警告是人工复核事项；error 让规则检查失败。输入解析错误与无法识别的文章不能被静默忽略。

## 兼容性

保留五个 Skill 名称和主要命令行参数。旧文章类型 `guide`、`procurement` 映射为 selection，`analysis`、`annual` 映射为 observation。新生成计划统一采用五类标识。

旧的合并双标题稿需拆分。客户必要信息缺失或没有文章时退出码为 2；验证输出目录必须为空或不存在；平台适配发现 error 时退出码改为 1。调用脚本的外部流程应据此更新。
