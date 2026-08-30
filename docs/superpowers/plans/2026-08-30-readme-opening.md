# README Opening Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重写 README 的认知入口，让使用 AI 编写项目文档的开发者先看到项目结果和工作方式，再进入安装、适用范围、发布状态与验证细节。

**Architecture:** 只修改 `README.md` 的文案与章节顺序，不改变 Skill、脚本、测试、版本或分发契约。先以仓库事实建立临时事实账本，再按已批准的 hybrid 主线重写；成稿必须经过 fresh-context cold-reader 与 coverage reviewer，最后运行仓库验证并更新现有 PR。

**Tech Stack:** Markdown、Git、Python 3.11/3.14、`uv`、现有 `scripts/verify`、Codex fresh-context reviewers、GitHub Actions。

## Global Constraints

- Primary reader 是正在使用 AI 编写或维护项目文档的开发者。
- 首屏先说明“准确、好懂、能用”的目标，再说明流程如何达到该目标。
- 首屏不得使用 `cold-reader`、`coverage reviewer` 或“双 reviewer”等未定义实现术语。
- “准确、好懂、能用”是流程目标，不得写成模型质量保证。
- 不改变 Skill 运行时、能力边界、安装命令、版本或发布状态。
- Agent Skills CLI、OpenAI plugin、GitHub remote、tag、Release 与暂缓能力的状态必须保持仓库事实。
- Superpowers spec、plan 和临时事实账本是 AI 过程产物，不作为 README 的事实来源或面向人的项目说明。

---

### Task 1: 建立 README 事实账本

**Files:**
- Read: `docs/superpowers/specs/2026-08-30-readme-opening-design.md`
- Read: `README.md`
- Read: `skills/repository-documentation-workflow/SKILL.md`
- Read: `.codex-plugin/plugin.json`
- Read: `scripts/verify`
- Read: `scripts/smoke_agent_skills_install.py`
- Read: `.github/workflows/verify.yml`
- Read: `tests/forward-runs/0.1.0/newcomer-architecture/record.yaml`
- Read: `docs/releasing.md`
- Read: `SECURITY.md`
- Create temporarily: `$readme_review_dir/fact-ledger.md`

**Interfaces:**
- Consumes: 已批准的 document contract、当前 README 和仓库实现事实。
- Produces: coverage reviewer 使用的事实编号、主张、来源、状态与 README 落点。

- [ ] **Step 1: 创建仓库外临时审查目录**

Run:

```bash
mktemp -d /tmp/repository-documentation-workflow-readme.XXXXXX
```

Expected: 输出一个新的 `/tmp/repository-documentation-workflow-readme.*` 目录；后续把该绝对路径保存在任务专用变量 `readme_review_dir` 中，不写入仓库。

- [ ] **Step 2: 核对事实来源**

逐项读取上方列出的十个仓库文件，只把下列事实写入账本；每项使用 `id | reader question | claim | source | status | destination` 六列：

| id | claim | source | status | destination |
| --- | --- | --- | --- | --- |
| F1 | 项目为 AI 文档写作提供从读者契约、事实核验、认知组织到独立审查的流程 | `skills/repository-documentation-workflow/SKILL.md` | 已实现 | 首屏、它如何工作 |
| F2 | 流程适用于创建或实质性重写 README、ADR、架构/设计说明、tutorial、how-to、reference、playbook、runbook | `skills/repository-documentation-workflow/SKILL.md` | 已实现 | 适用范围 |
| F3 | 流程不用于轻微校对、代码注释、PR/commit/issue 文案或 Agent 指令 | `skills/repository-documentation-workflow/SKILL.md` | 已实现 | 适用范围 |
| F4 | GitHub 与本地 checkout 的 Agent Skills CLI copy-install 路径已验证 | `scripts/smoke_agent_skills_install.py`、`.github/workflows/verify.yml`、本轮临时远程 smoke 原始输出 | 已验证 | 快速安装、当前发布状态 |
| F5 | OpenAI plugin manifest 已准备，但公开 marketplace 尚未发布 | `.codex-plugin/plugin.json`、`docs/releasing.md` | 已配置/未发布 | 快速安装、当前发布状态 |
| F6 | 版本表面为 `0.1.0`，GitHub remote 已创建，尚无 tag 或 GitHub Release | `.codex-plugin/plugin.json`、`docs/releasing.md` | 已配置/未发布 | 当前发布状态 |
| F7 | `scripts/verify` 覆盖 schema、plugin 分发、tracked、上游、链接、fixture、forward-run 与 regression checks，但不运行模型 | `scripts/verify`、`README.md` | 已验证 | 验证证据与能力边界 |
| F8 | 仓库保存一次限定任务、模型和结论的 `0.1.0` 真实 forward review | `tests/forward-runs/0.1.0/newcomer-architecture/record.yaml` | 已记录 | 验证证据与能力边界 |
| F9 | private vulnerability reporting 已启用，发布与安全细节由专项文档承载 | `SECURITY.md`、`docs/releasing.md` | 已配置 | 参与贡献与发布 |
| F10 | “文档体系完整性与单篇文档克制性”扩展不属于 `0.1.0` | `README.md`、已批准 spec | 暂缓 | 暂缓能力 |

Expected: 每个事实都有准确来源、状态和唯一主要落点；账本不包含无法从仓库核实的新能力。

- [ ] **Step 3: 重新验证 GitHub 远程安装主张**

Run:

```bash
mktemp -d /tmp/repository-documentation-workflow-remote-smoke.XXXXXX
```

在命令输出的临时目录中运行：

```bash
npx --yes skills@1.5.23 add x12315/repository-documentation-workflow \
  --skill repository-documentation-workflow \
  --agent codex \
  --copy \
  --yes
rg --files .agents/skills/repository-documentation-workflow
```

Expected: CLI 从 `https://github.com/x12315/repository-documentation-workflow.git` clone，报告安装 1 个 Skill；文件清单恰好包含当前 Skill 的 14 个文件。原始命令输出留在临时执行记录中，不写入仓库。

- [ ] **Step 4: 检查旧结论与相关引用**

Run:

```bash
rg -n '面向仓库文档的 Codex Skill|不用于轻微校对|当前发布状态|双 reviewer|cold-reader|coverage reviewer|准确、好懂、能用' README.md CONTRIBUTING.md SECURITY.md docs CHANGELOG.md
```

Expected: 找到 README 当前入口、正式发布/安全事实和历史 Superpowers 过程记录；只修改 active human-facing `README.md`，不改写历史 spec/plan。

---

### Task 2: 按批准骨架重写 README

**Files:**
- Modify: `README.md`
- Reference: `docs/superpowers/specs/2026-08-30-readme-opening-design.md`
- Reference temporarily: `$readme_review_dir/fact-ledger.md`

**Interfaces:**
- Consumes: Task 1 的 F1–F10 事实账本和已批准首屏文案。
- Produces: 可送交两个 fresh-context reviewer 的完整 README 初稿。

- [ ] **Step 1: 用批准文案替换当前开头**

将标题后的两个现有段落替换为：

```markdown
> 让 AI 写出的项目文档，不只是语句通顺，而是真的准确、好懂、能用。

Repository Documentation Workflow 为 AI 文档写作提供一套可执行的流程：先明确文档写给谁看，再核实项目事实、按读者的理解顺序组织内容，最后分别检查“读者能不能看懂”和“事实有没有写错或遗漏”。

它改进的是 AI 写文档的全过程，而不只是最后的措辞润色。
```

- [ ] **Step 2: 在首屏后增加最小工作模型**

紧接首屏加入：

```markdown
## 它如何工作

1. 明确文档写给谁看、读完要得到什么。
2. 从代码、配置和测试中核实可以写入的事实。
3. 按读者理解新概念的顺序组织内容。
4. 分别检查可读性与事实覆盖；任一检查未通过，就根据可定位的问题继续修改。
```

- [ ] **Step 3: 重排安装、适用范围和发布状态**

按下列精确映射重排，命令与状态表内容保持不变：

| 当前内容 | 新位置 |
| --- | --- |
| `## 安装` | 重命名为 `## 快速安装`，放在“它如何工作”之后 |
| GitHub copy-install | `### 从 GitHub 安装（已验证）` |
| 本地 checkout copy-install | `### 从本地 checkout 安装` |
| OpenAI plugin | `### OpenAI plugin`，保留 marketplace 未发布边界 |
| 当前第二段的适用限制 | 新建 `## 适用范围`，放在快速安装之后 |
| `## 当前发布状态` | 完整表格移动到适用范围之后 |

`## 适用范围` 使用以下正文：

```markdown
这个流程适合创建或实质性重写 README、ADR、架构与设计说明、tutorial、how-to、reference、playbook 和 runbook。

它不用于轻微校对、代码注释、PR/commit/issue 文案或 Agent 指令文件。任务同时包含代码与文档时，流程只作用于文档部分，不扩大原任务的权限或文件范围。
```

删除原状态表后的“因此，首次使用……”过渡句；快速安装已经承担该导航职责。

- [ ] **Step 4: 合并使用与工作流说明**

把当前 `## 使用` 和 `## 工作流` 合并为 `## 完整工作流`。保留显式调用入口，并将四个对象写为：

````markdown
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
````

- [ ] **Step 5: 完成后半部分章节整理**

将 `## 验证边界` 重命名为 `## 验证证据与能力边界`，正文事实保持不变。其后依次保留：

1. `## 参与贡献与发布`
2. `## 仓库结构`
3. `## 暂缓能力`
4. `## 许可证`

Expected heading order:

```text
# Repository Documentation Workflow
## 它如何工作
## 快速安装
### 从 GitHub 安装（已验证）
### 从本地 checkout 安装
### OpenAI plugin
## 适用范围
## 当前发布状态
## 完整工作流
## 验证证据与能力边界
## 参与贡献与发布
## 仓库结构
## 暂缓能力
## 许可证
```

- [ ] **Step 6: 做作者层表达与事实预检**

Run:

```bash
rg -n '^#{1,3} |双 reviewer|面向仓库文档的 Codex Skill|因此，首次使用' README.md
```

Expected: 标题顺序与上方列表一致；首屏没有未定义 reviewer 术语；旧开头和旧过渡句均不存在。

Run:

```bash
git diff --check
git diff -- README.md
```

Expected: 无空白错误；diff 只重写入口、认知桥梁和章节顺序，没有改变安装命令、版本、发布状态或能力边界。

---

### Task 3: 运行 fresh-context 双 reviewer 闭环

**Files:**
- Read: `skills/repository-documentation-workflow/references/adopted-writing-principles.md`
- Read: `skills/repository-documentation-workflow/references/technical-humanizer-overlay.md`
- Read: `skills/repository-documentation-workflow/references/independent-review-loop.md`
- Read: `README.md`
- Read temporarily: `$readme_review_dir/fact-ledger.md`
- Create temporarily: `$readme_review_dir/cold-reader-packet.md`
- Create temporarily: `$readme_review_dir/coverage-reviewer-packet.md`
- Create temporarily: `$readme_review_dir/round-1-cold-reader.md`
- Create temporarily: `$readme_review_dir/round-1-coverage-reviewer.md`
- Create temporarily if another round is required: corresponding `round-2-*` and `round-3-*` files

**Interfaces:**
- Consumes: Task 2 完整 README 初稿、document contract 和 F1–F10 事实账本。
- Produces: 同一轮互相隔离的 cold-reader 与 coverage reviewer PASS，或可定位的修订项。

- [ ] **Step 1: 完整读取表达与 reviewer 协议**

读取本 Task 列出的三个 runtime reference；不读取 `references/upstream/` 中的 workflow 或 frontmatter。

- [ ] **Step 2: 创建 cold-reader 数据包并派发 fresh-context reviewer**

数据包只包含：

```text
primary reader: 正在使用 AI 编写或维护项目文档的开发者
entry state: 已经有代码仓库和 AI 编程工具，但不满意 AI 生成文档的准确性、结构或可用性
exit outcomes:
  - 能说明项目通过流程约束提高 AI 文档质量，而不是只负责润色
  - 能说明流程怎样让文档更准确、更容易理解并支持读者行动
  - 能判断适用范围并找到安装入口
  - 能区分已验证能力、未发布能力和验证边界
reading mode: hybrid
reading order: 按 README 从上到下，之后允许按标题查阅
draft: README.md 全文
```

Reviewer 必须返回 `PASS` 或 `FAIL`；`FAIL` 的每一项必须引用 README 可定位片段，说明哪个 exit outcome 无法达成以及最小修复方向。不得向 reviewer 提供作者 mainline、设计 spec 或事实账本。

- [ ] **Step 3: 创建 coverage 数据包并派发另一 fresh-context reviewer**

数据包只包含：scope、Task 1 的 F1–F10 事实账本、十个来源文件清单和 README 全文。Reviewer 必须逐项输出 `covered | contradicted | overstated | missing`，最后返回 `PASS` 或 `FAIL`；不得读取 cold-reader 结果。

- [ ] **Step 4: 根据同轮结果收敛**

若两个 reviewer 均为 `PASS`，进入 Task 4。任一为 `FAIL` 时，只按可定位证据修改 README，并为下一轮创建两个新的 fresh-context reviewer；最多三轮。第三轮仍有阻塞问题时停止，不得声称完成。

Expected: 同一轮 cold-reader 与 coverage reviewer 都明确返回 `PASS`，原始结果保存在临时目录而不提交仓库。

---

### Task 4: 验证、提交并更新 PR

**Files:**
- Modify: `README.md`
- Existing PR: `#1` (`feature/initial-workflow` → `main`)

**Interfaces:**
- Consumes: 两个 reviewer 同轮 PASS 的 README 成稿。
- Produces: 已验证、已提交、已 push，且远程 CI 全绿的 README 重写。

- [ ] **Step 1: 检查 Python 工具并运行双版本验证**

Run:

```bash
uv --version
uv run --python 3.11 scripts/verify
uv run --python 3.14 scripts/verify
```

Expected: `uv` 可用；两个 Python 版本均输出 `all deterministic repository-documentation-workflow checks passed`。

- [ ] **Step 2: 完成 diff 与状态审查**

Run:

```bash
git diff --check
git diff -- README.md
git status --short --branch
```

Expected: 只有 `README.md` 未提交；无空白错误、个人绝对路径、凭据、临时 reviewer 产物或能力状态漂移。

- [ ] **Step 3: 提交 README**

Run:

```bash
git add README.md
git diff --cached --check
git commit -m "docs: 重写 README 认知入口"
```

Expected: 产生一个只包含 `README.md` 的 Conventional Commit。

- [ ] **Step 4: push 并等待 PR 检查**

Run:

```bash
git push origin feature/initial-workflow
gh pr checks 1 --repo x12315/repository-documentation-workflow --watch --interval 10
```

Expected: Python 3.11、Python 3.14 与 Agent Skills smoke 均为 `pass`。

- [ ] **Step 5: 完成最终审计**

Run:

```bash
git status --short --branch
gh pr view 1 --repo x12315/repository-documentation-workflow --json url,state,mergeable,mergeStateStatus,headRefOid,statusCheckRollup
```

Expected: 本地 feature 与 origin 同步、工作区 clean；PR 为 open、`MERGEABLE`、`CLEAN`，head OID 等于本地 HEAD，所有 required checks 为 `SUCCESS`。不 merge、不创建 tag 或 Release。
