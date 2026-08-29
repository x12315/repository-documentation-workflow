# RelayHub source packet

- <a id="S1"></a>**S1**：`ingress` 验证调用方身份和请求 schema，成功后把原始请求写入 `task_log`。
- <a id="S2"></a>**S2**：`router` 从 `task_log` 读取待处理记录，根据 `task_type` 选择 queue；它不执行任务。
- <a id="S3"></a>**S3**：`worker` 消费单一 queue。执行成功后先写 `result_store`，再确认 queue message。
- <a id="S4"></a>**S4**：`receipt-api` 只读取 `result_store`，不查询 worker 内存状态。
- <a id="S5"></a>**S5**：queue 至少一次投递；worker 使用 `task_id` 作为幂等键。
- <a id="S6"></a>**S6**：ingress 到 `task_log` 的写入失败时返回错误，不发布 queue message。
- <a id="S7"></a>**S7**：worker 写入结果后、确认消息前崩溃会触发重复投递；幂等写使已有结果保持不变。
- <a id="S8"></a>**S8**：当前自动化测试覆盖 schema rejection、route selection、正常执行和重复投递。
- <a id="S9"></a>**S9**：压力测试、跨可用区恢复和生产故障演练尚未执行。
- <a id="S10"></a>**S10**：`task_type` 与 queue 的完整映射属于配置 reference，不应复制到架构主线。
