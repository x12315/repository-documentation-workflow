# 测试与 fresh-context 审查协议

`tests/verify-fixtures` 和 `scripts/verify` 是确定性检查。它们验证路由 fixture、reviewer 数据包白名单、负向成稿、oracle 以及发布资产边界；它们不调用模型，也不把 fixture 形状检查记作 reviewer PASS。

## 准备隔离数据包

以 `newcomer-architecture` output case 为例：

```bash
tests/prepare-review-packets \
  tests/output-cases/newcomer-architecture \
  /tmp/newcomer-architecture-review
```

命令生成互不共享的 `cold-reader/` 与 `coverage-reviewer/` 目录；packet 中的每个相对路径都能在各自目录内直接解析。命令同时创建初始值为 `model_reviews_run: false` 的 `review-record.yaml`。`oracle.yaml` 留在 fixture 中，只供审查运行完成后的维护者比对，绝不能放入任一 reviewer context。

## 运行与记录 forward review

每一轮分别启动两个 fresh context。每个 context 只收到对应角色目录中的文件和 [`independent-review-loop.md`](../skills/repository-documentation-workflow/references/independent-review-loop.md) 规定的返回 schema。不要提供作者对话、另一 reviewer 的结果或 `oracle.yaml`。

把原始返回值分别保存为 `results/round-N-cold-reader.md` 和 `results/round-N-coverage-reviewer.md`。随后在 `review-record.yaml` 的 `rounds` 中为每个结果记录：

```json
{
  "round": 1,
  "role": "cold-reader",
  "reviewer_id": "独立 context 的稳定标识",
  "model": "实际模型与版本",
  "verdict": "PASS 或 FAIL",
  "result_path": "results/round-1-cold-reader.md"
}
```

只有两个角色都实际返回结果后，才把 `model_reviews_run` 改为 `true`。任一角色 FAIL 时先修订成稿，再为下一轮创建新的两个 context；同一个 `reviewer_id` 不得跨轮复用。oracle 只验证已知负向成稿是否触发角色范围内的 finding，不代替 reviewer 判断。
