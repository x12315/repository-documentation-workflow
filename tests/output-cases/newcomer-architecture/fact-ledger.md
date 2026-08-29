# Fact ledger

| id | reader question | claim | source | status | destination |
| --- | --- | --- | --- | --- | --- |
| F1 | 请求从哪里进入？ | ingress 先验证身份和 schema，再持久化原始请求 | `source-packet.md#S1` | implemented, automated tests partial | 主路径：入口 |
| F2 | 谁决定任务去向？ | router 按 task_type 选择 queue，但不执行任务 | `source-packet.md#S2` | implemented, automated test | 主路径：路由 |
| F3 | 执行结果何时可见？ | worker 先写 result_store，再确认消息；receipt-api 只读结果存储 | `source-packet.md#S3`、`source-packet.md#S4` | implemented, automated test partial | 主路径：执行与查询 |
| F4 | 重复投递如何处理？ | queue 至少一次投递，worker 以 task_id 做幂等写 | `source-packet.md#S5`、`source-packet.md#S7` | implemented, automated test | 失败恢复 |
| F5 | 入口持久化失败会怎样？ | task_log 写入失败时返回错误且不发布消息 | `source-packet.md#S6` | implemented, automated test not stated | 失败恢复 |
| F6 | 当前验证到了哪一层？ | 自动化测试覆盖四类行为，压力与跨区/生产演练未执行 | `source-packet.md#S8`、`source-packet.md#S9` | tested with named gaps | 验证状态 |
| F7 | 完整路由表在哪里？ | 映射由配置 reference 承载，架构文档只解释规则 | `source-packet.md#S10` | documented boundary | 短链，不复制表格 |
