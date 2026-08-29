# Repository Documentation Workflow

`repository-documentation-workflow` 是一个面向仓库文档的 Codex Skill。它在创建或实质性重写 README、ADR、架构与设计说明、tutorial、how-to、reference、playbook 和 runbook 时，先核实项目事实，再组织读者的理解路径。

它不用于轻微校对、代码注释、PR/commit/issue 文案或 Agent 指令文件。若任务同时包含代码与文档，流程只作用于文档部分，不扩大原任务的权限或文件范围。

## 当前发布状态

| 项目 | 状态 |
| --- | --- |
| 版本表面 | `.codex-plugin/plugin.json` 与 `CHANGELOG.md` 记录为 `0.1.0`。 |
| Agent Skills CLI | 已用隔离的临时消费仓库完成真实 copy-install smoke，并核对安装副本的 schema 与文件内容。 |
| OpenAI plugin | 根目录 manifest 已准备；尚未发布公开 marketplace，不能提供公开安装 URL 或命令。 |
| Git 发布 | 当前没有 remote、tag 或正式 release。 |

因此，首次使用请选择下方可验证的 Agent Skills CLI 路径。plugin 的人工安装与发布前检查见 [`docs/releasing.md`](docs/releasing.md)。

## 安装

### Agent Skills CLI（当前可验证）

将源码 checkout 与消费仓库放在同一父目录。例如：

```text
workspace/
├── consumer-repository/
└── repository-documentation-workflow/
```

在 `consumer-repository/` 中运行：

```bash
npx --yes skills@1.5.23 add ../repository-documentation-workflow \
  --skill repository-documentation-workflow \
  --agent codex \
  --copy \
  --yes
```

安装副本位于消费仓库的 `.agents/skills/repository-documentation-workflow/`。它是消费端产物；要更新，请在源码 checkout 修改后重新执行同一条安装命令。

### OpenAI plugin

仓库根目录已有 plugin manifest，且它与 Agent Skills CLI 共用 `skills/repository-documentation-workflow/` 这一份 Skill 源码。公开 marketplace 尚未发布，所以现在没有可验证的远程安装命令。发布前的官方 validator、人工安装和 metadata 检查边界见 [`docs/releasing.md`](docs/releasing.md)。

## 使用

满足适用范围的仓库文档任务可自动触发，也可显式调用：

```text
$repository-documentation-workflow
```

流程围绕四个对象工作：

1. **读者契约**：明确主要读者、开始条件、阅读结果和阅读方式。
2. **事实账本**：把可写入的主张逐项对应到代码、配置、测试或记录。
3. **认知路径**：按读者理解依赖安排正文与查阅层。
4. **独立审查**：由 cold-reader 检查可读性，由 coverage reviewer 检查事实覆盖和状态准确性。

前一项确定文档应解决的问题；后两项防止成稿既难以阅读，又遗漏或升级项目事实。

## 工作流

推荐路径是：先定义文档契约，再建立事实账本；以账本组织主线和查阅层，最后由两个 fresh-context reviewer 分别审查。`SKILL.md` 还规定了适用范围、运行时 references 与最多三轮的审查收敛条件。

这是一套文档流程，不是模型质量保证。确定性检查只能验证可重复的结构与边界；真实 reviewer 是否通过，必须由实际独立 context 的记录证明。

## 验证边界

完整确定性入口是：

```bash
scripts/verify
```

它验证 Skill schema、plugin manifest、Git tracked 交付边界、上游快照、Markdown 本地链接、fixture 隔离与 forward-run 记录，并运行 regression tests。它不调用模型，也不会把 fixture 形状检查写成 reviewer PASS。

本仓库还保存了一次 `0.1.0` 的真实 forward review 证据，位于 `tests/forward-runs/0.1.0/newcomer-architecture/`；该证据仅覆盖其中记录的任务、模型和结果。测试资产与真实审查协议见 [`tests/README.md`](tests/README.md)。Agent Skills CLI 的真实安装 smoke 由 `scripts/smoke_agent_skills_install.py` 执行，并在 CI 中单独运行。

## 参与贡献与发布

- [贡献指南](CONTRIBUTING.md)：环境、验证、上游快照与 PR 约定。
- [发布指南](docs/releasing.md)：版本一致性、双通道验证及 remote/tag/release 的人工边界。
- [安全策略](SECURITY.md)：安全范围与当前报告通道状态。
- [行为准则](CODE_OF_CONDUCT.md)：社区参与契约与举报路径。

## 仓库结构

```text
.codex-plugin/plugin.json                    OpenAI plugin manifest
skills/repository-documentation-workflow/    唯一的 Skill 源码与固定上游快照
scripts/                                     确定性校验、同步与安装 smoke
tests/                                       fixture、regression tests 与 forward-review evidence
docs/                                        发布与长期维护说明
```

## 暂缓能力

“文档体系完整性与单篇文档克制性”的工作流扩展暂不属于 `0.1.0`。当前流程仍要求 scope 内事实有可达归宿，但没有把这一更广的体系级优化作为已实现能力。

## 许可证

本仓库自有内容采用 Apache-2.0。固定第三方内容的来源、commit、hash 与许可证见 [`THIRD_PARTY_NOTICES.md`](skills/repository-documentation-workflow/THIRD_PARTY_NOTICES.md) 和 [`UPSTREAM.lock.yaml`](skills/repository-documentation-workflow/UPSTREAM.lock.yaml)。
