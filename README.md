# Repository Documentation Workflow

> 让 AI 写出的项目文档，不只是语句通顺，而是真的准确、好懂、能用。

Repository Documentation Workflow 为 AI 文档写作提供一套可执行的流程：先明确文档写给谁看，再核实项目事实、按读者的理解顺序组织内容，最后分别检查“读者能不能看懂”和“事实有没有写错或遗漏”。

它改进的是 AI 写文档的全过程，而不只是最后的措辞润色。

## 它如何工作

1. 明确文档写给谁看、读完要得到什么。
2. 从代码、配置和测试中核实可以写入的事实。
3. 按读者理解新概念的顺序组织内容。
4. 分别检查可读性与事实覆盖；任一检查未通过，就根据可定位的问题继续修改。

## 快速安装

### 从 GitHub 安装（已验证）

在目标仓库中运行：

```bash
npx --yes skills@1.5.23 add x12315/repository-documentation-workflow \
  --skill repository-documentation-workflow \
  --agent codex \
  --copy \
  --yes
```

该命令从公开 GitHub 仓库取得源码，并把 Skill copy 安装到当前仓库的 `.agents/skills/repository-documentation-workflow/`。

### 从本地 checkout 安装

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

## 适用范围

这个流程适合创建或实质性重写 README、ADR、架构与设计说明、tutorial、how-to、reference、playbook 和 runbook。

它不用于轻微校对、代码注释、PR/commit/issue 文案或 Agent 指令文件。任务同时包含代码与文档时，流程只作用于文档部分，不扩大原任务的权限或文件范围。

## 当前发布状态

| 项目 | 状态 |
| --- | --- |
| 版本表面 | `.codex-plugin/plugin.json` 与 `CHANGELOG.md` 记录为 `0.1.0`。 |
| Agent Skills CLI | 已分别从本地 checkout 和公开 GitHub 仓库完成隔离 copy-install smoke，并核对安装副本。 |
| OpenAI plugin | 根目录 manifest 已准备；尚未发布公开 marketplace，不能提供公开安装 URL 或命令。 |
| Git 发布 | [GitHub 仓库](https://github.com/x12315/repository-documentation-workflow)已创建；尚无 tag 或正式 release。 |

## 完整工作流

满足适用范围的仓库文档任务可自动触发，也可显式调用：

```text
$repository-documentation-workflow
```

完整流程围绕四个对象展开：

1. **读者契约**：明确主要读者、开始条件、阅读结果和阅读方式。
2. **事实账本**：把可以写入的主张逐项对应到代码、配置、测试或记录。
3. **认知路径**：按读者理解新概念所需的前置知识安排正文与查阅层。
4. **独立审查**：`cold-reader` 从陌生读者角度检查是否读得懂，`coverage reviewer` 逐项检查事实是否写全、写准。

流程先定义文档契约，再建立事实账本；以账本组织主线和查阅层，最后让两个互不共享作者上下文的角色分别审查。任一检查未通过，作者就根据可定位的问题修改并重新送审，最多三轮。

这是一套文档流程，不是模型质量保证。确定性检查只能验证可重复的结构与边界；真实 reviewer 是否通过，必须由实际独立 context 的记录证明。

## 验证证据与能力边界

完整确定性入口是：

```bash
scripts/verify
```

它验证 Skill schema、plugin manifest、Git tracked 交付边界、上游快照、Markdown 本地链接、fixture 隔离与 forward-run 记录，并运行 regression tests。它不调用模型，也不会把 fixture 形状检查写成 reviewer PASS。

本仓库还保存了一次 `0.1.0` 的真实 forward review 证据，位于 `tests/forward-runs/0.1.0/newcomer-architecture/`。记录中的 `cold-reader` 与 `coverage reviewer` 均为 PASS，并列出了 author 和两名 reviewer 的模型标识与报告路径；该证据只覆盖其中记录的任务、模型和结果。测试资产与真实审查协议见 [`tests/README.md`](tests/README.md)。Agent Skills CLI 的真实安装 smoke 由 `scripts/smoke_agent_skills_install.py` 执行，并在 CI 中单独运行。

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
