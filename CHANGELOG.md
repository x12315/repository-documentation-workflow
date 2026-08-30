# Changelog

## [0.1.0] - 2026-08-29

### Added

- 增加 `.codex-plugin/plugin.json`，声明本仓库的 plugin 元数据、技能入口与用户可见接口说明。
- 增加 `scripts/verify_distribution.py` 与 `tests/test_distribution.py`，对 manifest 和 marketplace 分发契约做确定性校验。
- 增加中文 `CONTRIBUTING.md`、`SECURITY.md`、`CODE_OF_CONDUCT.md`、发布指南、GitHub issue/PR 模板和验证 CI。
- 增加根文档本地链接的确定性门禁与回归测试。

### Changed

- Superpowers scratch 和过程文档现在排除在 release tree 外，tracked-delivery verification 会强制执行这项忽略边界。
- `scripts/verify` 现在包含 plugin 分发校验。
- `scripts/verify_tracked.py` 将 `.github`、`.codex-plugin`、`docs`、脚本、Skill、测试和根治理文档纳入必须被 Git 跟踪的交付边界。
- `.gitignore` 忽略消费端安装产物 `.agents/skills/` 与 `skills-lock.json`。
- README 以中文区分 Agent Skills CLI 的当前可验证安装、已包装但未发布的 OpenAI plugin、真实 forward evidence 与治理入口。

### Verified

- `python3 tests/test_distribution.py`
- `scripts/verify`
- Agent Skills CLI `skills@1.5.23` 隔离 copy-install smoke；它核对安装副本的 schema 与文件内容。
- `tests/forward-runs/0.1.0/newcomer-architecture/` 保存了该任务与记录模型的一次实际双 reviewer 通过证据，不推广为所有任务的结论。
