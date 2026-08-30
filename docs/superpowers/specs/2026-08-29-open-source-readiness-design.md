# 仓库开源整备设计

## 目标

把当前独立出来的 `repository-documentation-workflow` 整备成可公开审查、可验证、可通过两条渠道安装的开源仓库，同时保留现有 Skill 源码和确定性验证基础。

本轮交付完成后，维护者应能：

- 从同一份 Skill 源码构建 OpenAI plugin 和 Agent Skills CLI 两条安装链路；
- 在 GitHub CI 中验证仓库结构、Skill、plugin 包装、上游快照和测试资产；
- 按明确的贡献、安全和发布约定维护项目；
- 查看一次真实 forward test 的输入、产物、reviewer 结果和能力边界；
- 在创建远程仓库后直接进入首个公开版本的发布准备。

## 已确认的选择

- 分发定位：OpenAI plugin 与 Agent Skills CLI 都是正式支持的安装方式。
- 文档语言：用户可读的项目文档保持中文，不维护英文文档副本。
- 通用化边界：Skill 的触发描述和路由测试覆盖英文请求，运行时工作流仍可生成用户要求语言的文档。
- 分支模型：采用轻量档，功能工作在 `feature/*` 完成，合并到默认分支前由用户确认。
- 初始版本：plugin manifest 从 `0.1.0` 起步；本轮不创建公开 tag。
- 能力边界：暂缓“文档体系完整性与单篇文档克制性”的工作流扩展，不把它混入开源整备。
- 远程边界：本轮不创建远程仓库，不填写未知的仓库 URL、维护者邮箱或发布账号。

## 单一源码与双通道分发

`skills/repository-documentation-workflow/` 继续作为唯一运行时源码。OpenAI plugin 和 Agent Skills CLI 都引用该目录，不生成或提交第二份 Skill 副本。

```text
仓库根
├── .codex-plugin/plugin.json             OpenAI plugin manifest
├── skills/
│   └── repository-documentation-workflow/ 唯一 Skill 源码
├── scripts/                               确定性维护与验证入口
└── tests/                                 路由、输出案例和 forward test 记录
```

`.codex-plugin/plugin.json` 声明稳定名称、`0.1.0` 版本、描述、Apache-2.0 许可证、`./skills/` 入口、非占位的贡献者身份和必要的 interface 字段。主页、仓库 URL 和视觉资产只有在真实值存在时才加入。

`plugin-creator` 的 repo marketplace 只接受 `./plugins/<name>` 结构，不能把仓库根声明为本地 plugin source。为保留根 plugin 和唯一 Skill 源码，仓库不提交不受支持的 marketplace 条目；安装 smoke test 在临时目录创建标准 `plugins/<name>` 布局和 marketplace，正式远程 marketplace 等仓库 URL 存在后再加入。

Agent Skills CLI 继续从仓库的 `skills/repository-documentation-workflow/` 安装。README 把两条渠道写成并列选择，并说明各自适用的宿主范围、安装命令和更新方式。

`.agents/skills/`、个人 Codex 配置、CLI cache 和临时消费仓库都是测试产物，不进入 Git。

## 开源仓库契约

新增以下长期维护入口：

| 文件 | 责任 |
| --- | --- |
| `CONTRIBUTING.md` | 说明环境、修改边界、验证命令、上游快照更新和提交要求 |
| `SECURITY.md` | 说明安全问题范围和 GitHub private vulnerability reporting 入口 |
| `CODE_OF_CONDUCT.md` | 提供中文社区行为准则并保留所采用上游版本与归属 |
| `CHANGELOG.md` | 按版本记录用户可见变化，从 `0.1.0` 开始 |
| `docs/releasing.md` | 说明版本更新、双通道验证、tag 和公开发布检查单 |
| `.github/ISSUE_TEMPLATE/` | 区分缺陷、功能建议和行为验证报告 |
| `.github/pull_request_template.md` | 要求说明范围、验证层级、第三方来源与未覆盖边界 |
| `.github/workflows/verify.yml` | 在受支持 Python 版本上运行仓库验证与安装 smoke test |

项目保持 stdlib-only，不为了形成 Python package 而增加无运行价值的依赖或构建层。贡献者环境声明支持 Python 3.11 及以上；本地优先用 `uv` 选择解释器，发布后的 Skill 运行不依赖 `uv`。

GitHub description、topics、默认分支保护、远程地址和首个 tag 属于远程仓库创建阶段。本轮只在 `docs/releasing.md` 中给出可执行检查单，不写占位值。

## 项目文档更新

README 不做脱离事实的整体重写，只补充本轮产生的新公开契约：

- OpenAI plugin 与 Agent Skills CLI 的选择、安装和更新方式；
- Python、shell、网络和宿主能力等开发前提；
- CI 与本地验证的覆盖层级；
- `CONTRIBUTING.md`、`SECURITY.md`、`docs/releasing.md` 和第三方归属入口；
- 当前版本、已验证能力和暂缓能力的明确状态。

新增文档应由仓库代码、配置、测试和实际命令结果支撑。README 不复制贡献、发布或安全文档的完整内容，只提供短入口，避免形成多处事实源。

## 行为 forward test 与自我改进

直接重写本仓库 README 不能充分验证这个 Skill，并且 Skill 的入口 gate 明确排除了 `SKILL.md` 等 Agent 指令文件。因此，自我改进采用“真实任务运行 + 正确的元级编辑工具”，而不是让 Skill 违反自己的边界直接改写自身。

### 运行任务

以 `tests/output-cases/newcomer-architecture/` 的请求和 source packet 为输入，在隔离临时目录运行当前 Skill。执行者只收到：

- `skills/repository-documentation-workflow/`；
- `request.md`；
- `source-packet.md`。

执行者不收到已有 `draft.md`、oracle、作者预期、已知缺陷或本次设计结论。它从原始任务生成文档契约、事实账本和架构成稿。

### 独立审查

成稿由两个 fresh-context reviewer 审查：

- cold-reader 只收到读者条件、阅读结果和成稿；
- coverage reviewer 只收到 scope、事实账本、来源和成稿。

任一角色失败时，把 finding 定位到具体成稿位置、事实或 Skill 规则。修改 Skill 时使用 `skill-creator` 和 `writing-for-agents`，只修复实际暴露的问题，不让待测 Skill 自己改写 Agent 指令。修改后换新的执行者和 reviewer 重跑，最多三轮。

### 证据记录

`tests/forward-runs/0.1.0/newcomer-architecture/` 保存：

- 实际输入副本；
- 生成的文档契约、事实账本和成稿；
- 每轮两个 reviewer 的原始输出；
- 模型标识、fresh-context 标识、轮次与 verdict；
- 本轮据此产生的 Skill 修改摘要。

记录只证明 `0.1.0`、该任务和所记录模型的实际结果，不声称所有文档任务都已通过。测试资产不得包含个人路径、会话秘密、作者对话或未授权仓库内容。

## 验证策略

### 确定性验证

`scripts/verify` 继续作为唯一完整入口，并增加以下检查：

- plugin manifest schema、路径边界和 Skill inventory；
- 临时 marketplace schema、source 路径和 plugin 名称一致性；
- manifest、CHANGELOG 和 forward run 的版本一致性；
- 开源文档与模板的本地链接；
- forward run 记录具备两个角色、不同 reviewer 标识、原始结果路径和实际 verdict；
- `.agents/skills/`、cache 或临时安装产物未被跟踪。

这些检查只验证结构和可追溯性，不模拟模型 verdict，也不把静态 fixture 当成模型通过。

### 路由与输出案例

现有中文正负路由案例继续保留，并补充：

- 英文创建或实质性重写仓库文档的正向请求；
- 英文轻微校对、commit 文案和 Agent 指令文件的负向请求；
- 同时包含代码与文档的任务，验证工作流只作用于文档部分。

现有故意失败的 `newcomer-architecture` draft 继续作为 reviewer 边界 fixture，不被 forward test 成稿覆盖。新增一份正确成稿案例，验证 packet 准备和记录协议能表达通过结果；确定性脚本仍不判断文章质量。

### 双通道安装

安装 smoke test 使用临时目录和隔离配置：

1. Agent Skills CLI 从本地仓库安装指定 Skill 到临时消费仓库，检查实际安装文件与 schema。
2. OpenAI plugin 在临时标准 marketplace 布局中验证 manifest 可发现、plugin 路径可解析、所含 Skill 与源码 inventory 一致。
3. 若当前宿主不能自动完成 ChatGPT 桌面安装，只把结构和 CLI 可覆盖部分记为自动通过，并在发布检查单保留人工安装步骤。

网络、外部 CLI 或宿主能力不可用时，对应层明确记录为“未执行”；不得用 manifest 文件存在替代真实安装结果。

### CI

GitHub Actions 在 Linux 上覆盖 Python 3.11 和 3.14。基础 job 只依赖仓库和 Python stdlib；需要外部 CLI 或网络的安装 job 单独运行，使失败原因可区分。

官方 validator 只在工具与依赖真实可用时叠加运行。缺失时输出实际跳过原因，仓库自带 validator 的通过不能改写为“官方 validator 通过”。

## 发布与交付边界

`0.1.0` 的本地整备完成条件是：

- 两条分发入口引用同一份 Skill；
- `scripts/verify` 在支持的本地 Python 环境通过；
- GitHub Actions 配置能在目标矩阵运行；
- 双通道安装 smoke test 的自动覆盖和人工边界均有记录；
- forward test 达到两名 reviewer 同轮通过，或如实记录三轮后的阻塞项；
- README 与开源治理文档只包含已验证事实和可执行入口；
- 工作区 clean，变更按功能语义提交到 `feature/initial-workflow`。

创建远程、启用安全报告、设置分支保护、创建 tag、发布 plugin 或合并默认分支都不属于本轮自动操作，需要在远程仓库存在后按发布检查单执行。合并仍须用户明确确认。

## 非目标

- 不实现已暂缓的文档体系级事实归宿能力；
- 不扩大 Skill 到 Agent 指令、源码注释或一般写作任务；
- 不维护英文项目文档；
- 不引入 MCP server、hooks、遥测或运行时网络依赖；
- 不把测试用安装副本、模型 cache 或临时事实账本提交到仓库；
- 不把一次 forward test 的通过推广成未经验证的通用质量声明。
