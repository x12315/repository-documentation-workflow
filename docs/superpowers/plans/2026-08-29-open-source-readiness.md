# 仓库开源整备实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把当前 Skill 仓库整备成共享一份源码、正式支持 OpenAI plugin 与 Agent Skills CLI、具备开源治理和可追溯行为验证的 `0.1.0` 版本。

**Architecture:** 仓库根作为 OpenAI plugin，`skills/repository-documentation-workflow/` 保持唯一运行时源码；Agent Skills CLI 直接安装同一目录。确定性脚本验证 manifest、版本、测试资产和 forward run 记录，外部 CLI smoke test 与模型 review 明确分层。

**Tech Stack:** POSIX shell、Python 3.11/3.14 stdlib、JSON-compatible YAML、GitHub Actions、Codex plugin manifest、`skills` CLI 1.5.23。

## Global Constraints

- 用户可读项目文档使用中文；Skill description 与路由 fixture 覆盖英文请求。
- plugin 版本固定为 `0.1.0`，本轮不创建 tag、不创建远程仓库、不发布、不合并。
- `skills/repository-documentation-workflow/` 是唯一 Skill 源码，不迁移、不复制到仓库其他目录。
- 暂缓“文档体系完整性与单篇文档克制性”能力，不修改核心工作流步骤。
- 运行时与基础验证保持 stdlib-only；`uv` 只用于贡献者解释器和临时验证依赖。
- 所有安装测试写入临时目录，不修改个人 Codex marketplace、config 或 plugin cache。
- Git 分支保持 `feature/initial-workflow`，每个任务验证后独立 commit。

---

### Task 1: Plugin 分发契约与确定性校验

**Files:**
- Create: `.codex-plugin/plugin.json`
- Create: `CHANGELOG.md`
- Create: `scripts/verify_distribution.py`
- Create: `tests/test_distribution.py`
- Modify: `scripts/verify`
- Modify: `scripts/verify_tracked.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `validate_plugin_manifest(repository_root: Path) -> str`，返回严格 semver。
- Produces: `validate_marketplace(marketplace_root: Path, expected_plugin_name: str) -> Path`，返回解析后的 plugin 根。
- Consumes: plugin manifest 中的 `skills: "./skills/"` 和 `CHANGELOG.md` 中的 `## [0.1.0]`。

- [ ] **Step 1: 写失败测试**

在 `tests/test_distribution.py` 建立两个独立测试：真实仓库在 manifest 缺失时失败；临时 marketplace 在 source 越界或 plugin 名称漂移时失败。测试通过 `sys.path.insert(0, str(ROOT / "scripts"))` 导入：

```python
from verify_distribution import validate_marketplace, validate_plugin_manifest


class DistributionTest(unittest.TestCase):
    def test_repository_manifest_is_valid_and_versioned(self) -> None:
        self.assertEqual("0.1.0", validate_plugin_manifest(ROOT))

    def test_marketplace_rejects_source_outside_plugins_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            (root / ".agents/plugins").mkdir(parents=True)
            (root / ".agents/plugins/marketplace.json").write_text(
                json.dumps({
                    "name": "local-test",
                    "plugins": [{
                        "name": "repository-documentation-workflow",
                        "source": {"source": "local", "path": "../escape"},
                        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                        "category": "Productivity",
                    }],
                }),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "source.path"):
                validate_marketplace(root, "repository-documentation-workflow")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 tests/test_distribution.py`

Expected: FAIL，错误指向缺少 `scripts/verify_distribution.py` 或 `.codex-plugin/plugin.json`。

- [ ] **Step 3: 写最小 manifest 和版本表面**

`.codex-plugin/plugin.json` 使用 `plugin-creator` scaffold 验证过的字段形状：

```json
{
  "name": "repository-documentation-workflow",
  "version": "0.1.0",
  "description": "按读者认知路径设计、核实并独立审查仓库文档。",
  "author": {"name": "repository-documentation-workflow contributors"},
  "license": "Apache-2.0",
  "keywords": ["documentation", "repository", "review", "codex"],
  "skills": "./skills/",
  "interface": {
    "displayName": "Repository Documentation Workflow",
    "shortDescription": "按读者认知路径编写并审查仓库文档",
    "longDescription": "通过读者契约、事实账本、认知路径和双 reviewer，编写可核验的仓库文档。",
    "developerName": "repository-documentation-workflow contributors",
    "category": "Productivity",
    "capabilities": ["Write"],
    "defaultPrompt": "根据代码、配置和测试，创建或实质性重写这个仓库的文档。"
  }
}
```

`CHANGELOG.md` 建立 `# Changelog`、`## [0.1.0] - 2026-08-29` 和 Added/Changed/Verified 三节，只记录本轮真实能力，不写远程发布状态。

- [ ] **Step 4: 实现分发 validator**

`scripts/verify_distribution.py` 使用 `json`、`re`、`Path`，完整实现：

```python
SEMVER_RE = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?")
REQUIRED_INTERFACE = {
    "displayName", "shortDescription", "longDescription", "developerName",
    "category", "capabilities", "defaultPrompt",
}


def load_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON object {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _inside(root: Path, relative: object, field: str) -> Path:
    if not isinstance(relative, str) or not relative.startswith("./"):
        raise ValueError(f"{field} must start with ./")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"{field} leaves its root") from error
    return resolved


def validate_plugin_manifest(repository_root: Path) -> str:
    manifest = load_object(repository_root / ".codex-plugin/plugin.json")
    required = {"name", "version", "description", "author", "license", "skills", "interface"}
    if missing := required - manifest.keys():
        raise ValueError(f"plugin manifest missing: {', '.join(sorted(missing))}")
    if manifest["name"] != repository_root.name:
        raise ValueError("plugin name must match repository directory")
    version = manifest["version"]
    if not isinstance(version, str) or SEMVER_RE.fullmatch(version) is None:
        raise ValueError("plugin version must use strict semver")
    if manifest["license"] != "Apache-2.0":
        raise ValueError("plugin license must match repository LICENSE")
    author = manifest["author"]
    if not isinstance(author, dict) or not isinstance(author.get("name"), str) or not author["name"].strip():
        raise ValueError("plugin author.name is required")
    interface = manifest["interface"]
    if not isinstance(interface, dict) or REQUIRED_INTERFACE - interface.keys():
        raise ValueError("plugin interface is incomplete")
    skill_root = _inside(repository_root, manifest["skills"], "skills")
    expected_skill = skill_root / manifest["name"] / "SKILL.md"
    if not expected_skill.is_file():
        raise ValueError(f"plugin skill entry is missing: {expected_skill}")
    changelog = (repository_root / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## [{version}]" not in changelog:
        raise ValueError("CHANGELOG does not contain plugin version")
    return version


def validate_marketplace(marketplace_root: Path, expected_plugin_name: str) -> Path:
    catalog = load_object(marketplace_root / ".agents/plugins/marketplace.json")
    entries = catalog.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1:
        raise ValueError("marketplace must contain exactly one smoke-test plugin")
    entry = entries[0]
    if entry.get("name") != expected_plugin_name:
        raise ValueError("marketplace plugin name mismatch")
    source = entry.get("source")
    expected_path = f"./plugins/{expected_plugin_name}"
    if not isinstance(source, dict) or source.get("source") != "local" or source.get("path") != expected_path:
        raise ValueError(f"source.path must be {expected_path}")
    if entry.get("policy") != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}:
        raise ValueError("marketplace policy mismatch")
    plugin_root = _inside(marketplace_root, expected_path, "source.path")
    if not (plugin_root / ".codex-plugin/plugin.json").is_file():
        raise ValueError("marketplace plugin manifest is missing")
    return plugin_root
```

CLI `main()` 接收 repository root，依次验证 manifest 并打印版本；异常统一返回 1。

- [ ] **Step 5: 接入完整验证和 tracked 边界**

在 `scripts/verify` 的 Skill schema 之后运行：

```sh
python3 "$repository_root/scripts/verify_distribution.py" "$repository_root"
```

`scripts/verify_tracked.py` 把 `.codex-plugin` 加入 `delivery_roots`。`.gitignore` 新增 `.agents/skills/` 与 `skills-lock.json`，避免当前源码仓库混入消费端安装产物。

- [ ] **Step 6: 运行测试与完整验证**

Run: `python3 tests/test_distribution.py`

Expected: `Ran 2 tests`，`OK`。

Run: `scripts/verify`

Expected: 新增 `verified plugin distribution 0.1.0`，原有检查继续通过。

- [ ] **Step 7: Commit**

```bash
git add .codex-plugin/plugin.json CHANGELOG.md .gitignore scripts/verify scripts/verify_distribution.py scripts/verify_tracked.py tests/test_distribution.py
git commit -m "feat: 建立 plugin 分发契约"
```

### Task 2: 英文路由与正向输出案例

**Files:**
- Modify: `skills/repository-documentation-workflow/SKILL.md`
- Modify: `tests/routing-positive.yaml`
- Modify: `tests/routing-negative.yaml`
- Modify: `tests/verify-fixtures`
- Modify: `tests/output-cases/newcomer-architecture/oracle.yaml`
- Create: `tests/output-cases/passing-newcomer-architecture/*`

**Interfaces:**
- Produces: 中英文均可匹配、仍排除 Agent 指令与轻微编辑的 frontmatter description。
- Produces: `oracle.expected_verdicts`，角色键固定为 `cold-reader`、`coverage-reviewer`。

- [ ] **Step 1: 先加入正向 fixture，制造失败**

从已通过的隔离 author 产物创建 `passing-newcomer-architecture`，包含与现有 case 相同的八个必需文件。其 `oracle.yaml` 使用：

```json
{
  "schema_version": 1,
  "fixture_intent": "正向成稿验证 reviewer packet 与 PASS 记录协议；确定性脚本不判断文章质量。",
  "expected_verdicts": {"cold-reader": "PASS", "coverage-reviewer": "PASS"},
  "expected_findings": {"cold-reader": [], "coverage-reviewer": []}
}
```

Run: `tests/verify-fixtures`

Expected: FAIL，指出正向 case 的 finding 列表为空或 oracle schema 尚不支持 PASS。

- [ ] **Step 2: 扩展 oracle 验证**

在 `tests/verify-fixtures` 中要求 `expected_verdicts` 恰好包含两个角色，值只能是 PASS/FAIL；PASS 必须没有 finding，FAIL 必须至少有一个 finding。为现有负向 case 增加：

```json
"expected_verdicts": {
  "cold-reader": "FAIL",
  "coverage-reviewer": "FAIL"
}
```

- [ ] **Step 3: 通用化 Skill description 与路由案例**

保持正文流程不变，只把 frontmatter description 改成一行中英双语指针；英文部分明确 `Use for creating or substantially rewriting human-facing repository documentation`，并保留 `Do not use for agent instructions, code comments, PR/commit/issue copy, or minor edits.`。

每个路由文件新增三项：英文实质性 README/architecture 请求、英文轻微编辑或 commit copy、代码与文档混合任务。混合任务的 expected 为 invoke，但 reason 明确“只对文档部分应用”。

- [ ] **Step 4: 运行 fixture、schema 和完整验证**

Run: `python3 scripts/verify_skill_schema.py skills/repository-documentation-workflow`

Expected: PASS，description 未超过 1024 字符。

Run: `tests/verify-fixtures`

Expected: 输出至少 `verified 18 routing cases and 2 output case(s)`。

Run: `scripts/verify`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add skills/repository-documentation-workflow/SKILL.md tests/routing-positive.yaml tests/routing-negative.yaml tests/verify-fixtures tests/output-cases
git commit -m "test: 扩展双语路由与正向案例"
```

### Task 3: Forward run 证据与记录 validator

**Files:**
- Create: `scripts/verify_forward_runs.py`
- Create: `tests/test_forward_runs.py`
- Create: `tests/forward-runs/0.1.0/newcomer-architecture/*`
- Modify: `scripts/verify`

**Interfaces:**
- Produces: `validate_forward_run(run_root: Path, expected_version: str) -> int`，返回 reviewer 记录数。
- Consumes: Task 1 的 `validate_plugin_manifest()` 返回版本。

- [ ] **Step 1: 写失败测试**

`tests/test_forward_runs.py` 创建临时 run，分别验证：同轮 reviewer id 重复被拒绝；result 文件 verdict 与 record 不一致被拒绝；有效的同轮双 PASS 返回 2。

有效记录形状固定为：

```json
{
  "schema_version": 1,
  "release_version": "0.1.0",
  "case": "newcomer-architecture",
  "model_reviews_run": true,
  "outcome": "passed",
  "author": {
    "context_id": "/root/forward_author_round1",
    "model": "gpt-5 (exact runtime revision not exposed)",
    "report_path": "author-report.md"
  },
  "rounds": [
    {
      "round": 1,
      "role": "cold-reader",
      "reviewer_id": "/root/forward_cold_reader_r1",
      "model": "gpt-5 (exact runtime revision not exposed)",
      "verdict": "PASS",
      "result_path": "results/round-1-cold-reader.md"
    },
    {
      "round": 1,
      "role": "coverage-reviewer",
      "reviewer_id": "/root/forward_coverage_r1",
      "model": "gpt-5 (exact runtime revision not exposed)",
      "verdict": "PASS",
      "result_path": "results/round-1-coverage-reviewer.md"
    }
  ]
}
```

Run: `python3 tests/test_forward_runs.py`

Expected: FAIL，模块尚不存在。

- [ ] **Step 2: 实现记录 validator**

`validate_forward_run()` 检查：版本一致、`model_reviews_run` 为 true、author report 存在、每轮恰好两个角色、reviewer id 在整个 run 中唯一、model 非空、result 路径不越界且存在、原始结果首个 verdict 与记录一致。`outcome: passed` 时最后一轮必须同轮双 PASS；`outcome: blocked` 时必须恰好三轮且最后一轮至少一项 FAIL。

CLI 从 plugin manifest 取得版本，只验证 `tests/forward-runs/0.1.0/`，并打印 run 与 reviewer 数量。

- [ ] **Step 3: 固化 round 1 原始证据**

把 `/tmp/repository-documentation-forward-0.1.0/` 中实际 author 输入、契约、事实账本、draft、author report 和两个原始 reviewer 结果复制到 run 目录；不复制临时绝对路径 packet。新增 `skill-change-summary.md`，明确：round 1 双 PASS，没有证据支持修改核心工作流；本轮只修改触发描述和测试覆盖。

- [ ] **Step 4: 接入完整验证并运行**

在 `scripts/verify` 中于 fixture 之后运行：

```sh
python3 "$repository_root/scripts/verify_forward_runs.py" "$repository_root"
python3 "$repository_root/tests/test_forward_runs.py"
```

Run: `python3 tests/test_forward_runs.py`

Expected: `Ran 3 tests`，`OK`。

Run: `scripts/verify`

Expected: 输出 `verified 1 forward run(s) and 2 reviewer result(s)` 后整体 PASS。

- [ ] **Step 5: Commit**

```bash
git add scripts/verify scripts/verify_forward_runs.py tests/test_forward_runs.py tests/forward-runs
git commit -m "test: 记录 0.1.0 forward review"
```

### Task 4: Agent Skills CLI 安装 smoke test

**Files:**
- Create: `scripts/smoke_agent_skills_install.py`
- Create: `tests/test_agent_skills_install.py`
- Modify: `scripts/verify_tracked.py`

**Interfaces:**
- Produces: `install_and_verify(repository_root: Path, runner: Callable[..., CompletedProcess]) -> int`，返回核对文件数。
- Consumes: `skills` CLI 1.5.23、Node >=22.20、`validate_skill_schema()`。

- [ ] **Step 1: 写 runner 注入测试**

测试 runner 断言命令包含：

```python
[
    "npx", "--yes", "skills@1.5.23", "add", str(repository_root.resolve()),
    "--skill", "repository-documentation-workflow",
    "--agent", "codex", "--copy", "--yes",
]
```

随后把源码 Skill copy 到临时 consumer 的 `.agents/skills/repository-documentation-workflow/`。测试要求函数验证 schema，并逐文件比较 source 与 installed inventory/hash。

Run: `python3 tests/test_agent_skills_install.py`

Expected: FAIL，模块尚不存在。

- [ ] **Step 2: 实现临时安装和字节核对**

`scripts/smoke_agent_skills_install.py` 使用 `tempfile.TemporaryDirectory()`，不调用 `rm`。默认 runner 为 `subprocess.run(check=True, cwd=consumer_root)`；命令固定 CLI 版本和 `--copy --yes`。安装后拒绝 symlink、额外文件和缺失文件，调用 `validate_skill_schema(installed_root)`，最后打印实际文件数。

CLI 运行前检查 `node --version` 与 `npx --version` 可执行；网络或 CLI 错误原样返回失败，不降级为结构 PASS。

- [ ] **Step 3: 运行单元测试与真实 smoke**

Run: `python3 tests/test_agent_skills_install.py`

Expected: PASS。

Run: `NPM_CONFIG_CACHE=/tmp/repository-documentation-npm-cache python3 scripts/smoke_agent_skills_install.py`

Expected: `installed and verified repository-documentation-workflow`，安装目录位于自动清理的临时 consumer。

- [ ] **Step 4: Commit**

```bash
git add scripts/smoke_agent_skills_install.py scripts/verify_tracked.py tests/test_agent_skills_install.py
git commit -m "test: 验证 Agent Skills CLI 安装"
```

### Task 5: 中文开源治理、README 与 CI

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `CODE_OF_CONDUCT.md`
- Create: `docs/releasing.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `.github/ISSUE_TEMPLATE/behavior_report.yml`
- Create: `.github/ISSUE_TEMPLATE/config.yml`
- Create: `.github/pull_request_template.md`
- Create: `.github/workflows/verify.yml`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `scripts/verify`
- Modify: `scripts/verify_tracked.py`

**Interfaces:**
- README 只保留身份、两条分发状态、使用入口、验证边界和短链接。
- `CONTRIBUTING.md` 是开发与上游更新的权威入口；`docs/releasing.md` 是版本与远程发布的权威入口。

- [ ] **Step 1: 先扩大 tracked/link 检查并确认缺口**

`scripts/verify_tracked.py` 增加 `.github`、`.codex-plugin`、`docs` 为 delivery roots，并把 `CHANGELOG.md`、`CODE_OF_CONDUCT.md`、`CONTRIBUTING.md`、`SECURITY.md` 加入根文件集合。

在 `scripts/verify` 中增加：

```sh
python3 "$repository_root/scripts/verify_release.py" "$repository_root"
```

Run: `scripts/verify`

Expected: FAIL，列出尚未创建的开源交付文件或 README 新链接目标。

- [ ] **Step 2: 编写互不重复的中文文档**

`CONTRIBUTING.md` 固定包含：适用修改类型、Python 3.11+ 与 `uv`、`scripts/verify`、forward review 边界、`UPSTREAM.lock.yaml` 更新、分支/commit、PR 前检查。

`SECURITY.md` 固定包含：安装/同步/路径越界/供应链属于安全范围；公开后使用 GitHub “Report a vulnerability”；不要在公开 issue 附凭据；目前没有远程私密报告通道的事实边界。

`CODE_OF_CONDUCT.md` 采用 Contributor Covenant 2.1 的官方中文文本或忠实中文版本，在末尾注明版本、上游 URL 和 CC BY 4.0 归属；联系与执法渠道使用仓库维护者和 GitHub moderation，不写未知邮箱。

`docs/releasing.md` 固定包含：更新 manifest/CHANGELOG/forward run 版本；运行 Python 3.11/3.14；运行官方 validator（可用时）；Agent Skills smoke；ChatGPT/Codex plugin 人工安装；创建远程后补 repository metadata；用户确认后 tag/merge/publish。

- [ ] **Step 3: 更新 README，不做无意义重写**

保留现有项目定位与四个核心对象，调整为以下层级：

```text
# Repository Documentation Workflow
项目身份与适用边界
## 当前发布状态
## 安装
### Agent Skills CLI（当前可验证）
### OpenAI plugin（已包装，公开目录尚未发布）
## 使用
## 工作流
## 验证边界
## 参与贡献与发布
## 仓库结构
## 暂缓能力
## 许可证
```

Agent CLI 命令固定 `npx skills@1.5.23`。plugin 部分只陈述 manifest 已准备和正式发布后的安装入口，不伪造当前可用的 public plugin URL。现有 checkbox 改成“暂缓能力”事实，不表现为本轮未完成项。

- [ ] **Step 4: 添加 GitHub 模板与 CI**

三个 issue form 分别要求复现、期望/边界、模型/输入隔离与 reviewer 证据。PR template 要求 Summary、Test plan、分发影响、第三方与未覆盖边界。

`.github/workflows/verify.yml` 使用：

```yaml
name: verify
on:
  push:
  pull_request:
permissions:
  contents: read
jobs:
  deterministic:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ["3.11", "3.14"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python }}
      - run: scripts/verify
  agent-skills-install:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v6
        with:
          python-version: "3.14"
      - uses: actions/setup-node@v5
        with:
          node-version: "24"
      - run: python3 scripts/smoke_agent_skills_install.py
```

- [ ] **Step 5: 验证文档、tracked 边界和 workflow YAML**

Run: `scripts/verify`

Expected: root Markdown local links、tracked delivery 和所有既有测试通过。

Run: `python3 -c 'import json; from pathlib import Path; json.loads(Path("skills/repository-documentation-workflow/UPSTREAM.lock.yaml").read_text())'`

Expected: exit 0，确认新增文档没有改变 lock 的 JSON-compatible 约束。

- [ ] **Step 6: Commit**

```bash
git add .github CHANGELOG.md CODE_OF_CONDUCT.md CONTRIBUTING.md README.md SECURITY.md docs/releasing.md scripts/verify scripts/verify_tracked.py
git commit -m "docs: 补齐开源治理与发布入口"
```

### Task 6: 官方校验、跨版本验证与交付审计

**Files:**
- Modify only if validation exposes a defect in Tasks 1–5.

**Interfaces:**
- Consumes: `scripts/verify`、官方 `quick_validate.py`、官方 `validate_plugin.py`、Agent Skills smoke。
- Produces: clean `feature/initial-workflow` 和按功能拆分的 commit 历史。

- [ ] **Step 1: Python 3.14 与 3.11 全量验证**

Run: `python3.14 scripts/verify_skill_schema.py skills/repository-documentation-workflow`

Expected: PASS。

Run: `UV_CACHE_DIR=/tmp/repository-documentation-uv-cache uv run --python 3.11 scripts/verify`

Expected: 下载或复用隔离 Python 3.11 后全部 PASS。

Run: `python3.14 scripts/verify`

Expected: 全部 PASS。

- [ ] **Step 2: 叠加官方 Skill 与 plugin validator**

Run:

```bash
skill_creator_root="${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator"
UV_CACHE_DIR=/tmp/repository-documentation-uv-cache uv run --with pyyaml python "$skill_creator_root/scripts/quick_validate.py" skills/repository-documentation-workflow
```

Expected: `Skill is valid!` 或官方脚本等价 PASS 输出。

Run:

```bash
plugin_creator_root="${CODEX_HOME:-$HOME/.codex}/skills/.system/plugin-creator"
UV_CACHE_DIR=/tmp/repository-documentation-uv-cache uv run --with pyyaml python "$plugin_creator_root/scripts/validate_plugin.py" .
```

Expected: plugin validation PASS。

- [ ] **Step 3: 重跑真实 Agent Skills CLI smoke**

Run: `NPM_CONFIG_CACHE=/tmp/repository-documentation-npm-cache python3.14 scripts/smoke_agent_skills_install.py`

Expected: 安装副本与源码 inventory/hash 一致。

- [ ] **Step 4: 审计完整目标而非只看绿灯**

逐项核对设计说明：双通道是否同源、核心能力是否未误改、中文文档是否无占位、forward run 是否为真实双 PASS、官方 validator 是否实际运行、plugin 桌面安装是否仍明确为人工边界、远程/tag/merge 是否没有被提前执行。

Run: `git diff --check`

Expected: 无输出。

Run: `git status --short --branch`

Expected: `## feature/initial-workflow` 且无未提交文件。

任何失败都返回负责该文件的 Task，先补失败测试，再修复并用该 Task 的 commit 语义提交；不创建空 commit 或把多类修复揉成一个收尾 commit。
