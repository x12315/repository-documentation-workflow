# 发布指南

本文件是版本与远程发布的权威入口。公开 remote 为 <https://github.com/x12315/repository-documentation-workflow>；当前仍没有 tag 或正式 release。创建 remote 和上传 feature 分支不等于完成版本发布。

## 发布前保持一致

发布版本必须同时出现在：

- `.codex-plugin/plugin.json` 的 `version`；
- `CHANGELOG.md` 的对应版本节；
- `tests/forward-runs/<version>/` 中实际记录的 forward run。

版本变化后先审查上述三处的语义和 evidence，而不只做字符串替换。

## 验证清单

1. 用 Python 3.11 与 3.14 运行确定性验证；先检查 `uv` 是否可用，可用时执行：

   ```bash
   uv run --python 3.11 scripts/verify
   uv run --python 3.14 scripts/verify
   ```

2. 在官方 Skill validator 与其依赖真实可用时运行官方校验。`scripts/verify` 会在找到 `quick_validate.py` 且 PyYAML 可导入时叠加它；否则只报告 strict stdlib 层已通过。
3. 运行 Agent Skills CLI 的真实 smoke：

   ```bash
   python3 scripts/smoke_agent_skills_install.py
   ```

   该检查要求满足版本下限的 Node、`npx`、网络，并把消费端安装限定在临时目录。
4. 使用官方 OpenAI plugin 安装/validator 界面或 CLI 完成人工验证。根 manifest 已准备，但没有公开 marketplace；不得把 manifest 存在视为已安装或已发布。
5. 查看 `tests/forward-runs/<version>/` 的原始 author/reviewer 结果，确认它们只主张实际覆盖的任务、模型和 verdict。

## GitHub 仓库配置

远程仓库已配置真实 description、topics、`main` 默认分支、必需 CI 检查和管理员不可绕过的分支保护，并已启用 GitHub private vulnerability reporting。正式发布前仍应核对这些远程设置与当前 CI context、`SECURITY.md` 和实际维护流程一致；不要用未知 URL、账号或邮箱替代这些事实。

## 需要用户确认的动作

只有用户明确确认后，才可以创建 tag、merge 到目标分支、发布 GitHub release、发布 OpenAI plugin 或公开 marketplace。执行前检查工作区 clean、比较待发布 diff、保存验证结果，并确保 release notes 只陈述已验证能力。
