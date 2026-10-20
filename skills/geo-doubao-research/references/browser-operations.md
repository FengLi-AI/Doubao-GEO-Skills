# 浏览器操作

人工浏览器可直接使用。可选 Shell 入口依赖已安装的 Playwright CLI；通过 PLAYWRIGHT_BIN 指定命令路径或将 playwright 放入 PATH。

`prepare_doubao_session.sh --profile-dir /path/to/dedicated-profile` 使用 codegen 打开有头会话。资料目录需独立于日常浏览器目录，包含登录态时不提交公开仓库。

参数参考 [Playwright Codegen](https://playwright.dev/docs/codegen)，链接核对于 2026-10-20。脚本不会自动搜索、录入账号、处理验证码或提交文章。

人工搜索后记录查询词、时间、模式、回答、引用 URL、截图。遇到安全提示或无法读取时记录限制并停止。
