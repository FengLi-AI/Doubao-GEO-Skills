# 本地验证

`run_closed_loop_demo.py` 只验证诊断、计划、Prompt、文章规则和监测计划这些本地产物。

- 缺少客户必要信息：input_status=needs_input，只输出诊断、询问清单与 incomplete 汇总，不继续生成计划。输出目录必须为空或不存在。
- 不提供文章：skipped，本地汇总 incomplete。
- 空文章目录：empty，本地汇总 incomplete。
- 未知平台、缺失清单文件或文章规则错误：failed。
- 实际检查至少一篇文章且无 error：文章检查 completed；其他本地生成成功时汇总 passed。

passed 不代表事实已核验、平台已审核、内容已发布或搜索效果已改善。线上发布与搜索效果始终单列为 not_performed 和 not_evaluated。
