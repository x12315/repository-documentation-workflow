# RelayHub 架构

RelayHub 接收任务、把任务交给执行端，并允许调用方查询结果。

## 一次任务的路径

`ingress` 验证身份和 schema，把原始请求写入 `task_log`。随后 `worker` 从 queue 取得任务，写入 `result_store` 并确认消息。`receipt-api` 直接查询 worker 的内存状态并返回结果。

## 失败恢复

queue 可能重复投递。worker 用 `task_id` 幂等写入，因此写结果后、确认前崩溃不会改变已有结果。

## 验证状态

自动化测试覆盖 schema rejection、route selection、正常执行和重复投递。完整路由映射见配置 reference。
