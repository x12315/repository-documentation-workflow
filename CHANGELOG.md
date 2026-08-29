# Changelog

## [0.1.0] - 2026-08-29

### Added

- 增加 `.codex-plugin/plugin.json`，声明本仓库的 plugin 元数据、技能入口与用户可见接口说明。
- 增加 `scripts/verify_distribution.py` 与 `tests/test_distribution.py`，对 manifest 和 marketplace 分发契约做确定性校验。

### Changed

- `scripts/verify` 现在包含 plugin 分发校验。
- `scripts/verify_tracked.py` 将 `.codex-plugin` 纳入必须被 Git 跟踪的交付边界。
- `.gitignore` 忽略消费端安装产物 `.agents/skills/` 与 `skills-lock.json`。

### Verified

- `python3 tests/test_distribution.py`
- `scripts/verify`
