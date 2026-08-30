# 安全策略

## 范围

请报告可能影响安装、上游同步、路径边界或供应链完整性的安全问题，包括依赖或来源替换、路径逃逸、符号链接处理、安装副本漂移和验证绕过。

## 报告方式

不要在公开 issue 中披露漏洞细节、复现凭据、访问 token、私有路径或其他敏感输入。

仓库已经启用 GitHub private vulnerability reporting。请使用仓库 Security 页面中的 **Report a vulnerability** 私密提交详情；不要用公开 issue、discussion 或 PR 替代该渠道，也不要在其中公布凭据或其他敏感输入。

## 处理边界

安全报告与普通 bug 分开处理。公开 issue 只适合不含敏感细节的后续状态或修复说明；修复发布、tag 和公告均按 [`docs/releasing.md`](docs/releasing.md) 的用户确认边界执行。
