# 独立审查闭环

本文定义两种互补 review。cold-reader 证明文档能被目标读者读懂；coverage reviewer 证明文档没有因追求流畅而丢失范围内的设计事实。作者自检不能替代任何一项。

## 隔离原则

每名 reviewer 使用 fresh context，例如 subagent 的 `fork_turns=none`。reviewer 不接收作者的推理过程、历史争论、预期答案、已知问题或另一名 reviewer 的报告。它只能使用本角色的数据包作判断。

同一 reviewer 不参与下一轮。修订后创建新的 cold-reader 和 coverage reviewer，避免旧结论成为阅读提示。

## Cold-reader 数据包

只提供：

- primary reader 与 entry state；
- exit outcomes；
- reading mode 与预期阅读顺序；
- 待审文档，以及文档正文明确链接的其他人类文档。

不提供作者预设的 document identity、mainline、outline 或认知骨架，也不提供代码、配置、事实账本、作者说明或仓库历史。reviewer 以 entry state 扮演真实读者，按预期顺序阅读，不主动搜索正文没有给出的入口；identity 与 mainline 必须从成稿重建。

要求 reviewer 返回：

```text
verdict: PASS | FAIL
reconstructed identity: 这是什么文档，为谁解决什么问题
reconstructed mainline: 不看契约复述理解脉络
exit outcomes: 每项 answered | partial | missing，并引用文档位置
friction log: 未定义术语、回读、跳层、入口不明和查找失败的位置
blocking findings: 导致 FAIL 的最小问题集
```

只有以下条件同时成立才 PASS：文档身份与 mainline 可以从正文重建；所有 exit outcomes 都是 `answered`；没有需要作者背景才能跨越的概念跳层；reading mode 对应的导航行为可用。

## Coverage reviewer 数据包

只提供：

- scope；
- 事实账本；
- 账本使用的来源清单及读取范围；
- 待审文档与被它替代或引用的相关文档；
- 项目定义的能力状态或证据层级。

不提供作者说明、cold-reader 报告或预期遗漏。reviewer 先独立检查来源范围是否存在账本未捕获的重要设计事实，再检查账本到成稿的映射。

要求 reviewer 返回：

```text
verdict: PASS | FAIL
source coverage: 来源中未进入账本的重要事实
ledger coverage: 每个事实 id 的 mapped | justified omission | missing
accuracy: 与来源矛盾、条件丢失或无证据新增的主张
status fidelity: 能力状态和证据强度是否被升级或弱化
blocking findings: 导致 FAIL 的最小问题集
```

只有以下条件同时成立才 PASS：来源范围内的重要事实已进入账本；每个应写入事实有可定位落点；省略理由与 scope 一致；正文没有冲突、无依据新增或能力状态漂移。

## 修订与停止条件

作者把 finding 映射到具体章节、事实 id 或来源后再修订。主观偏好、无法定位的“可以更清晰”和超出契约的扩写不驱动改稿。两名 reviewer 的意见冲突时，按 document contract 判断：认知问题调整呈现层，事实问题调整主张或账本；若必须牺牲一个 exit outcome 或 scope 内事实，交由用户裁决。

每轮都重新运行两种 review，最多三轮。第三轮仍未同时 PASS 时停止，向用户提供：未通过项、对应证据、已经尝试的结构修改，以及需要用户决定的取舍。环境无法产生 fresh context 时，标记 `independent review: not run`，不把作者自检记为 PASS。
