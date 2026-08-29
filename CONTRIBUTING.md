# 贡献指南

本指南是开发、验证与上游快照更新的权威入口；安装与使用见 [README](README.md)，发布步骤见 [`docs/releasing.md`](docs/releasing.md)。

## 适用修改

可以贡献 Skill 运行时文档、确定性验证脚本、fixture、forward-review evidence、plugin manifest、治理文档和 CI。修改 `skills/repository-documentation-workflow/references/upstream/` 或 `skills/repository-documentation-workflow/licenses/` 前，必须按 `skills/repository-documentation-workflow/UPSTREAM.lock.yaml` 审核来源、commit、许可证和 SHA-256；不要把固定上游快照当作运行时指令。

## 本地环境与验证

需要 Python 3.11+、Git、shell，以及执行 Agent Skills smoke 时所需的 Node 与网络。先检查 `uv` 是否可用；可用时默认通过它选择解释器，例如：

```bash
uv run --python 3.11 scripts/verify
```

没有 `uv` 时，使用满足版本要求的 `python3` 运行脚本。提交前必须运行：

```bash
scripts/verify
```

该命令包含确定性 schema、链接、tracked、上游、fixture 与 regression 检查。它不运行模型：fixture 只验证协议和隔离边界，不能替代真实的 fresh-context review。变更工作流行为时，按照 [`tests/README.md`](tests/README.md) 准备隔离 reviewer 数据包、保存原始结果并如实记录结论。

## 上游快照

`skills/repository-documentation-workflow/UPSTREAM.lock.yaml` 是固定上游的审核清单。更新前先核对目标 GitHub commit、许可证、文件清单和 SHA-256；随后运行：

```bash
scripts/sync-upstreams
scripts/verify-upstreams
```

`sync-upstreams` 只接受 lock 中已审核的 GitHub commit 与 hash，并在批次失败时恢复目标字节。不要手工漂移 vendored 文件或增添未纳入 lock 的文件。

## 分支、提交与 PR

仓库采用轻量分支模型：在 `feature/<short-kebab-name>` 上完成可审查的功能单元，再经用户确认合并。提交使用 conventional commit，例如 `docs: 补齐开源治理与发布入口`。

提交 PR 前：

- 查看 `git diff`，确认只包含当前任务；
- 运行相关测试和 `scripts/verify`；
- 检查文档、fixture、脚本和报告中没有个人绝对路径、凭据或临时消费端产物；
- 说明确定性验证、真实 forward review 与未覆盖边界各自的实际结果。
