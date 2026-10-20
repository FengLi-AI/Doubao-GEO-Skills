# 可选浏览器流程

浏览器操作不影响纯 Python 离线流程。你也可以直接用自己的浏览器手工搜索和填写日志。

## 准备

需要 Node.js、npm 和 Playwright 的浏览器运行环境。按 [Playwright 官方安装说明](https://playwright.dev/docs/intro) 安装；本仓库不内置、自动下载或锁定浏览器依赖。

在单独的浏览器工具目录安装 Playwright 后，确保 `playwright` 命令在 PATH 上，或设置 `PLAYWRIGHT_BIN` 为该目录 `node_modules/.bin/playwright` 的绝对路径。下面两个脚本只使用已经安装的命令。

```bash
bash skills/geo-doubao-research/scripts/prepare_doubao_session.sh --profile-dir .local/doubao-profile
bash skills/doubao-geo-publisher/scripts/probe_doubao_surface.sh --output-dir work/browser-probe
```

会话脚本使用 Playwright `codegen --user-data-dir` 打开可见浏览器，人工处理登录并搜索。它不会自动轮询关键词或提取回答。截图脚本只检查页面入口，不会复用前者的登录状态。

参数与行为参考 [Playwright Codegen 文档](https://playwright.dev/docs/codegen)。文档链接核对日期：2026-10-20；豆包页面兼容性仍需在使用时验证。

## 状态与记录

- 使用专门的浏览器资料目录，不使用日常浏览器的默认用户目录。
- `.local/`、浏览器状态、截图和真实客户日志已纳入 `.gitignore` 默认排除范围；不要把它们当作公开示例。
- 登录、验证码或账号安全步骤由用户处理；发生拦截时停下并记录情况。
- 每次搜索记录完整查询词、日期、模式、回答、引用链接与截图。
- 此次发布包只做了 Shell 语法和参数检查，没有验证真实登录或线上搜索。
