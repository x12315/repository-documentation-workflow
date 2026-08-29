# Repository Documentation Workflow

这是一个面向仓库文档的 Codex Skill。它把文档写作拆成四个可验证对象：读者契约、事实账本、认知路径和独立审查，目标是让不了解项目的人尽快建立正确的项目模型，同时不遗漏有证据支持的设计细节。

## 适用范围

Skill 自动用于创建或实质性重写 README、ADR、架构与设计说明、tutorial、how-to、reference、playbook 和 runbook。轻微校对、代码注释、PR/commit/issue 文案以及 Agent 指令文件不进入该流程。

它会先回答以下问题，再写正文：

- 谁是主要读者，开始阅读时已经知道什么？
- 读完后应该能回答哪些问题、做出哪些判断或完成哪些动作？
- 文档应从头阅读、按需查阅，还是先建立全局模型再查细节？
- 哪些项目事实必须进入文档，它们各自由什么证据支持？

成稿随后交给两个 fresh-context reviewer：cold-reader 只检查阅读体验和主线，coverage reviewer 依据事实账本和来源检查准确性与覆盖率。

## 安装

本地开发时，将源码仓库与消费仓库放在同一父目录，在消费仓库中运行：

```bash
npx skills add ../repository-documentation-workflow \
  --skill repository-documentation-workflow \
  --agent codex
```

发布到 GitHub 后可以从远端安装：

```bash
npx skills add x12315/repository-documentation-workflow \
  --skill repository-documentation-workflow \
  --agent codex
```

更新项目内已安装的副本：

```bash
npx skills update --project repository-documentation-workflow
```

安装目录是消费仓库的 `.agents/skills/repository-documentation-workflow/`。该目录是安装产物，不是源码；修改后应回到本仓库重新安装。

## 使用

普通仓库文档任务可以自动触发，也可以显式调用：

```text
$repository-documentation-workflow
```

Skill 只规定文档设计、写作和审查过程，不扩大当前任务的文件范围、权限或外部操作授权。

## 开发与验证

确定性完整验证入口：

```bash
scripts/verify
```

该入口始终运行与本发布 frontmatter 契约等价且更严格的 stdlib schema validator、Git tracked 交付边界、上游 schema/inventory/hash 校验、发布目录内链接边界、fixture 隔离检查和 regression tests。不支持的 YAML 形式会 fail closed。在 Git checkout 之外运行时会明确跳过 tracked 层。环境同时具有官方 `quick_validate.py` 和 PyYAML 时再叠加官方校验，并明确输出实际运行的验证层级；可用 `SKILL_QUICK_VALIDATE` 指定官方 validator 路径。

单独校验固定上游快照：

```bash
scripts/verify-upstreams
```

锁文件中的 commit 或 hash 经人工审核后，可同步上游文件：

```bash
scripts/sync-upstreams
```

`sync-upstreams` 只接受 `UPSTREAM.lock.yaml` 中的 GitHub commit 和 SHA-256。它先完成整个 lock schema 与 vendored inventory preflight，再下载并校验所有文件；批次替换或替换后校验失败时会恢复全部目标的原始字节。

仓库中扩展名为 `.yaml` 的 lock 和 fixture 为保持 stdlib-only，只接受 JSON-compatible YAML，也就是可由 `json.loads` 直接解析的 YAML 子集。解析错误会明确报告这一限制。

## 仓库结构

```text
skills/repository-documentation-workflow/  Skill 及固定上游快照
scripts/                                  同步与确定性验证
tests/                                    路由边界和输出审查案例
```

确定性脚本只检查测试资产、角色白名单和 packet 物理隔离，不运行模型，也不声称 fresh-context review 已通过。需要行为验证时，按 [`tests/README.md`](tests/README.md) 准备两个 reviewer 数据包、在独立 context 中运行并记录实际结果。

`references/upstream/` 中的第三方 prompt/Skill 文件只作为固定 provenance 快照保留，不由运行时工作流加载为指令。本 Skill 采用的原则位于自有 reference，更新上游快照不会自动改变运行行为。

## 待办

- [ ] 平衡文档体系完整性与单篇文档克制性。后续设计应让 scope 内的重要事实在整个文档
  体系中具有唯一、可达的权威归宿，同时只把读者当前必须知道的内容放进单篇正文；允许用
  reference、短链或具有独立身份的新文档承接细节。Coverage review 应检查体系级可达性，
  cold-reader review 应同时检查 first-pass 主线是否被查阅细节、重复说明或过早出现的概念
  淹没，并用同时覆盖“事实成为孤儿”和“正文过载”的行为案例验证改动。

## 许可证

本仓库自有内容采用 Apache-2.0。固定的第三方内容、来源、commit、hash 和许可证见 [`THIRD_PARTY_NOTICES.md`](skills/repository-documentation-workflow/THIRD_PARTY_NOTICES.md) 与 [`UPSTREAM.lock.yaml`](skills/repository-documentation-workflow/UPSTREAM.lock.yaml)。
