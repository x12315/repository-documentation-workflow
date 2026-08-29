# RelayHub 架构说明事实账本

来源范围仅包括 `source-packet.md` 的 S1–S10。状态描述的是 source packet 给出的证据层级，不把未提供的实现细节补写为事实。

| ID | 读者问题 | 可写入正文的主张 | 来源 | 状态 | 正文落点 |
| --- | --- | --- | --- | --- | --- |
| F1 | 请求进入系统时先发生什么？ | `ingress` 验证调用方身份和请求 schema；验证成功后把原始请求写入 `task_log`。 | `source-packet.md#S1` | 已实现（source packet 陈述） | “一次任务如何穿过系统”第 1 步；“组件职责”中的 `ingress` |
| F2 | 谁决定任务进入哪个 queue，谁执行任务？ | `router` 从 `task_log` 读取待处理记录，并按 `task_type` 选择 queue；`router` 不执行任务。 | `source-packet.md#S2` | 已实现（source packet 陈述） | “一次任务如何穿过系统”第 2 步；“组件职责”中的 `router` |
| F3 | worker 如何消费任务，成功时结果与消息确认的顺序是什么？ | 每个 `worker` 消费单一 queue；执行成功后先写 `result_store`，再确认 queue message。 | `source-packet.md#S3` | 已实现（source packet 陈述） | “一次任务如何穿过系统”第 3–4 步；“组件职责”中的 `worker`；“持久化与可见性边界” |
| F4 | receipt-api 从哪里读取结果？ | `receipt-api` 只读取 `result_store`，不查询 worker 内存状态。 | `source-packet.md#S4` | 已实现（source packet 陈述） | “一次任务如何穿过系统”第 5 步；“组件职责”中的 `receipt-api`；“持久化与可见性边界” |
| F5 | 系统怎样面对 queue 的重复投递？ | queue 提供至少一次投递，因此消息可能重复；worker 使用 `task_id` 作为幂等键。 | `source-packet.md#S5` | 已实现（source packet 陈述） | “系统全景”；“失败与恢复”中的“重复投递” |
| F6 | 入口无法写入 task_log 时会发生什么？ | `ingress` 写 `task_log` 失败时返回错误，且不发布 queue message。 | `source-packet.md#S6` | 已实现（source packet 陈述） | “组件职责”中的 `ingress`；“失败与恢复”中的“入口写入失败” |
| F7 | worker 已写结果但尚未确认消息时崩溃会发生什么？ | 崩溃会触发重复投递；使用 `task_id` 的幂等写使已有结果保持不变。 | `source-packet.md#S7` | 已实现的恢复行为（source packet 陈述） | “失败与恢复”中的“结果已写入、消息未确认” |
| F8 | 哪些行为已有自动化测试覆盖？ | 当前自动化测试覆盖 schema rejection、route selection、正常执行和重复投递。 | `source-packet.md#S8` | 已由自动化测试覆盖（仅限列出的四类行为） | “当前验证状态”中的“已覆盖” |
| F9 | 哪些验证尚未执行？ | 压力测试、跨可用区恢复和生产故障演练尚未执行。 | `source-packet.md#S9` | 未执行 | “当前验证状态”中的“尚未执行” |
| F10 | 架构文档是否应该列出完整路由映射？ | `task_type` 与 queue 的完整映射属于配置 reference，不复制到架构主线。 | `source-packet.md#S10` | 文档范围约束 | “配置 reference 边界” |

## 证据缺口

以下内容在来源范围内没有定义，因此不能写成系统保证：

- `task_log` 和 `result_store` 的 schema、保留策略、一致性、复制和跨可用区语义；
- 身份验证失败的响应契约，以及除 schema rejection 外的验证测试覆盖；
- `router` 的发布、确认、重试和崩溃恢复细节；
- worker 执行失败或写 `result_store` 失败时的重试与消息确认行为；
- 配置 reference 的具体路径，以及 `task_type` 到 queue 的实际映射；
- 压力、跨可用区恢复和生产故障演练结果。
