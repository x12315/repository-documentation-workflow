# RelayHub 架构

本文面向刚加入 RelayHub、目前只知道系统负责接收和分发任务的后端工程师。先沿一项任务从接收走到结果读取，再按组件查阅职责、持久化边界、失败恢复和当前验证状态。

## 阅读路径

首次阅读时，依次阅读“系统全景”“一次任务如何穿过系统”“持久化与可见性边界”和“失败与恢复”。建立完整路径后，可直接在“组件职责”中按组件查阅，并在“当前验证状态”中确认一个结论处于已测试还是尚未验证的状态。

## 系统全景

```text
调用方
  |
  v
ingress -- 原始请求 --> task_log --> router -- 按 task_type 选择 --> queue
                                                                    |
                                                                    v
                                                                 worker
                                                                    |
                                                         先写结果，再确认消息
                                                                    |
                                                                    v
receipt-api <-------------- 只读 --------------------------- result_store
```

这条路径有两个明确的存储边界。入口处，原始请求先写入 `task_log`，`router` 再从中读取待处理记录。执行完成处，worker 先把结果写入 `result_store`，然后才确认 queue message；`receipt-api` 也只从 `result_store` 读取结果。

queue 采用至少一次投递，因此同一任务可能再次到达 worker。worker 以 `task_id` 为幂等键，使重复投递不会改写已经存在的结果。这一投递语义是理解确认顺序和故障恢复的前提。

## 一次任务如何穿过系统

1. `ingress` 验证调用方身份和请求 schema。验证通过后，它把原始请求写入 `task_log`。
2. `router` 从 `task_log` 读取待处理记录，根据记录的 `task_type` 选择 queue。它只负责路由，不执行任务。
3. `worker` 从它负责的单一 queue 消费任务并执行。
4. 执行成功后，worker 先把结果写入 `result_store`，再确认 queue message。
5. `receipt-api` 从 `result_store` 读取结果。它不查询 worker 的内存状态。

正常路径确定了每个组件接力的位置，也确定了结果可查阅所依赖的状态：读取侧依赖 `result_store`，而不是某个仍在运行的 worker。下面的组件表把这条路径拆成可独立查阅的职责边界。

## 组件职责

| 组件或存储 | 职责 | 明确边界 |
| --- | --- | --- |
| `ingress` | 验证调用方身份与请求 schema；验证成功后将原始请求写入 `task_log` | 写 `task_log` 失败时返回错误，且不发布 queue message |
| `task_log` | 保存 `ingress` 写入的原始请求；向 `router` 提供待处理记录 | 来源没有定义记录生命周期、保留策略或一致性保证 |
| `router` | 从 `task_log` 读取待处理记录，按 `task_type` 选择 queue | 不执行任务；完整映射不属于架构主线 |
| queue | 向 worker 提供至少一次投递 | 可能重复投递；来源没有给出其他确认或重试细节 |
| `worker` | 消费单一 queue 并执行任务；成功后先写 `result_store`，再确认消息 | 以 `task_id` 为幂等键；来源没有定义执行失败或结果写入失败的处理 |
| `result_store` | 接收 worker 的执行结果，并作为 `receipt-api` 的读取来源 | 来源没有定义数据模型、保留策略或一致性保证 |
| `receipt-api` | 只从 `result_store` 读取结果 | 不查询 worker 内存状态 |

## 持久化与可见性边界

`task_log` 是入口与路由之间的记录边界。只有成功通过身份和 schema 验证的请求才进入这一步；如果 `ingress` 写入失败，它返回错误且不发布 queue message。来源没有进一步说明写入成功后的事务范围或记录生命周期。

`result_store` 是执行侧与读取侧之间的结果边界。worker 成功执行后，写入顺序固定为：

```text
写 result_store -> 确认 queue message
```

`receipt-api` 的读取来源也限定为 `result_store`。它不使用 worker 内存判断结果，因此 worker 的进程内状态不构成结果查询接口的一部分。

这两个边界说明了组件之间通过哪些状态接力，但来源没有给出存储的 schema、保留策略、一致性、复制或跨可用区保证。不能从“写入 store”进一步推断这些性质。

## 失败与恢复

### 入口写入失败

如果 `ingress` 无法把原始请求写入 `task_log`，它返回错误，并且不发布 queue message。这个边界避免了在入口记录尚未写入时继续进入 queue。

### 结果已写入、消息未确认

queue 的至少一次投递允许消息再次出现。一个明确的故障窗口是：

```text
worker 写入结果 -> worker 崩溃 -> 尚未确认消息 -> queue 重复投递
```

重复投递到达后，worker 仍使用同一个 `task_id` 作为幂等键。幂等写使 `result_store` 中已有的结果保持不变。这里的恢复保证只覆盖来源明确描述的窗口；它没有定义 worker 执行失败、写结果失败或 `router` 崩溃时的行为。

## 当前验证状态

当前自动化测试覆盖：

- schema rejection；
- route selection；
- 正常执行；
- 重复投递。

以下验证尚未执行：

- 压力测试；
- 跨可用区恢复；
- 生产故障演练。

因此，现有自动化覆盖能说明列出的行为已有测试，不能替代压力、跨可用区或生产演练结论。“尚未执行”也不等于行为一定不受支持，只表示当前没有这些验证结果。

## 配置 reference 边界

`router` 根据 `task_type` 选择 queue，但完整映射属于配置 reference，不在架构主线中复制。需要确认某个 `task_type` 的具体目标 queue 时，应查阅配置 reference；当前来源没有提供该 reference 的路径或映射内容。
