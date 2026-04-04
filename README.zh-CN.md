# 🚀 ai-research-workflow-skills

<p>
  <a href="./README.md">English</a> |
  <a href="./README.zh-CN.md">简体中文</a>
</p>

<p>
  <img alt="trusted by default" src="https://img.shields.io/badge/lane-trusted%20by%20default-1f6feb?style=flat-square">
  <img alt="explicit exploration" src="https://img.shields.io/badge/explore-explicit%20only-238636?style=flat-square">
  <img alt="platforms" src="https://img.shields.io/badge/platforms-Windows%20%7C%20Linux-0a7ea4?style=flat-square">
  <img alt="skills" src="https://img.shields.io/badge/skills-11-8b949e?style=flat-square">
  <img alt="public skills" src="https://img.shields.io/badge/public%20skills-9-0969da?style=flat-square">
  <img alt="tests" src="https://img.shields.io/badge/tests-42%20scripts-8250df?style=flat-square">
  <img alt="clients" src="https://img.shields.io/badge/clients-Agent%20Skills%20%C2%B7%20Codex%20%C2%B7%20Claude%20Code-6f42c1?style=flat-square">
</p>

品牌说明：仓库对外品牌名已经统一为 `ai-research-workflow-skills`。如果 GitHub 仓库 slug 还没有迁移，请继续使用 `lllllllama/ai-paper-reproduction-skills` 作为 clone 和 `npx skills add` 的路径，直到 slug 迁移完成。

迁移说明：
- `ai-paper-reproduction` -> `ai-research-reproduction`
- `research-explore` -> `ai-research-explore`

这是一个面向深度学习研究工作流的 lane-aware skill 仓库。

> 🔒 默认走可信链路：复现、环境准备、分析、训练验证、调试。  
> 🧪 只有研究者显式授权时，才进入 candidate-only 的探索链路。  
> 🔗 同一套 `SKILL.md` 合同可复用于 Agent Skills、Codex、Claude Code。

本仓库遵循一个核心默认原则：`trusted by default`。

- 模糊请求默认进入 trusted lane。
- 探索必须显式授权。
- trusted 输出强调可审计、可复用、可回看。
- explore 输出始终是 candidate-only、可丢弃的探索结果。

## 🧭 当前仓库快照

当前仓库状态：

- 共 `11` 个 skill，其中 `9` 个 public skill，`2` 个 helper skill。
- 共 `6` 个 trusted-lane public skill，`3` 个 explore-lane public skill。
- `.claude/commands/` 下当前提供 `4` 个项目级 Claude Code wrappers。
- 共有 `42` 个 Python 测试脚本，其中 `15` 个专门覆盖 `research-explore` 主链路。
- 第三场景 explore 现在已经接通：bounded idea seed generation、显式 idea score breakdown、atomic idea decomposition、以及 planned / heuristic / observed 分层的 implementation fidelity。
- 当前文档和命令示例按 Windows PowerShell 与 Linux shell 的共同使用方式整理。

本仓库采用开放的 `SKILL.md` 布局，因此同一套技能既可以安装到中立的 Agent Skills 目录，也可以安装到 Codex 和 Claude Code。共享本地安装优先使用 `~/.agents/skills/` 或 `./.agents/skills/`；`~/.codex/skills/` 和 `~/.claude/skills/` 仍然可用。

## 💻 Windows 与 Linux 使用说明

本仓库当前要求在 Windows 和 Linux 环境中都能正常使用，因此 README 中的命令示例保持为跨 shell 友好的形式。

- 下方命令统一围绕 `python ...`、`npx ...` 和相对路径编写，适合 Linux shell，也适合 Windows PowerShell。
- 用户级安装目录优先写成 `$HOME/.agents/skills`、`$HOME/.codex/skills`、`$HOME/.claude/skills`。Linux 可直接使用，PowerShell 也能正常展开；Python 在 Windows 上同样可以处理正斜杠路径。
- 项目级路径如 `./.agents/skills`、`./tmp/codex-skills` 在 Windows 和 Linux 上都可直接使用。
- 当前本地回归和 CI 说明也明确覆盖 Windows 与 Linux 场景。

## 🛠️ 安装

对大多数用户来说，优先用 `npx` 即可。这是最短路径，也最接近“开箱即用”。

### 推荐：`npx`

安装整套 skills：

```bash
npx skills add lllllllama/ai-paper-reproduction-skills --all
```

只安装 trusted 主入口：

```bash
npx skills add lllllllama/ai-paper-reproduction-skills --skill ai-research-reproduction
```

只安装 explore 主入口：

```bash
npx skills add lllllllama/ai-paper-reproduction-skills --skill ai-research-explore
```

如果你只是想尽快开始，用上面这几条就够了。

Claude Code 可以根据描述自动调用这些 skills，也可以直接使用 `/ai-research-reproduction`、`/ai-research-explore`、`/safe-debug` 这样的命令。

当前仓库提供的项目级 Claude Code slash commands：

- `/ai-research-reproduction`
- `/ai-research-explore`
- `/analyze-project`
- `/safe-debug`

### 高级用法：本地 clone 安装

只有在以下场景才建议继续用 Python 安装脚本：

- 你正在本地开发这个仓库
- 你需要 project-scoped 安装
- 你要手动安装到中立 Agent Skills、Codex 或 Claude Code 目录

<details>
<summary>展开本地安装命令</summary>

从本地 clone 安装到中立的 Agent Skills 目录：

```bash
python scripts/install_skills.py --client agents --target "$HOME/.agents/skills" --force
```

安装到项目内的中立 Agent Skills 目录：

```bash
python scripts/install_skills.py --client agents --target ./.agents/skills --force
```

使用默认中立安装目标：

```bash
python scripts/install_skills.py --force
```

在 Codex 中安装整套 skill：

```bash
npx skills add lllllllama/ai-paper-reproduction-skills --all
```

在 Codex 中只安装 trusted reproduction orchestrator：

```bash
npx skills add lllllllama/ai-paper-reproduction-skills --skill ai-research-reproduction
```

从本地 clone 安装到 Codex：

```bash
python scripts/install_skills.py --client codex --target "$HOME/.codex/skills" --force
```

从本地 clone 安装到 Claude Code：

```bash
python scripts/install_skills.py --client claude --target "$HOME/.claude/skills" --force
```

安装到项目内的 Claude Code skills 目录：

```bash
python scripts/install_skills.py --client claude --target ./.claude/skills --force
```

PowerShell 补充说明：

- Windows PowerShell 下，上面的命令可以直接照抄运行。
- 如果你更习惯显式 Windows 路径，也可以把 `$HOME/.codex/skills` 换成 `$env:USERPROFILE\\.codex\\skills` 这类写法。

</details>

## 🎯 入口选择

| 如果你想要… | 使用 |
|---|---|
| 从 README 出发，端到端复现一个仓库 | `ai-research-reproduction` |
| 在 `current_research` 之上，基于冻结的 task / eval / SOTA 运行第三场景 campaign | `ai-research-explore` |
| 只做只读分析，不改代码、不跑重任务 | `analyze-project` |
| 梳理环境、数据集、checkpoint、缓存等前置条件 | `env-and-assets-bootstrap` |
| 保守地执行 README 中记录的 inference 或 evaluation 命令 | `minimal-run-and-audit` |
| 保守地启动或恢复训练 | `run-train` |
| 安全诊断 traceback 或失败的训练 / 推理流程 | `safe-debug` |
| 只做隔离式 exploratory code 改动 | `explore-code` |
| 只做隔离式 exploratory run 试验 | `explore-run` |

内置 helper skills：

- `repo-intake-and-plan`
- `paper-context-resolver`

## 🛣️ Lane 结构

### 🔒 Trusted Lane

trusted lane 负责复现、环境准备、只读分析、保守执行、训练验证和安全调试。

- 主 orchestrator：`ai-research-reproduction`
- 主要输出目录：`repro_outputs/`、`train_outputs/`、`analysis_outputs/`、`debug_outputs/`
- 默认立场：尽量保持科学含义不变，尽量减少语义性改动，显式暴露假设和 blocker

### 🧪 Explore Lane

explore lane 只在研究者显式授权 candidate-only 探索时启用。

- 主 orchestrator：`ai-research-explore`
- 窄职责 leaf skills：`explore-code`、`explore-run`
- 主输出目录：`explore_outputs/`
- 核心锚点：`current_research`

`current_research` 应该是一个可持续引用的研究状态，例如 branch、commit、checkpoint、run record，或者已经训练好的本地模型状态。它不是 trusted baseline 的同义词，而是探索流程起步时所依赖的上下文锚点。

### 🧰 Helper Lane

helper skills 保持窄职责，通常应该由 orchestrator 调用，而不是作为用户的第一入口。

## 🔗 客户端兼容性

本仓库中，`SKILL.md` 是跨客户端的 canonical contract。

- 便携性必需：`SKILL.md`、skill 自带的 `scripts/`、`references/`
- Codex 可选元数据：`agents/openai.yaml`
- Claude Code 可选入口：`.claude/commands/*.md`
- 不允许：让 skill 行为依赖某个 client-specific metadata 文件

详见 [references/client-compatibility-policy.md](references/client-compatibility-policy.md)。

## 🗺️ 路由总览

```mermaid
flowchart TD
    A[用户请求] --> B{是否显式授权 candidate-only 探索?}
    B -- 否 --> C[Trusted lane]
    B -- 是 --> D[Explore lane]

    C --> C1[ai-research-reproduction]
    C --> C2[analyze-project]
    C --> C3[env-and-assets-bootstrap]
    C --> C4[minimal-run-and-audit]
    C --> C5[run-train]
    C --> C6[safe-debug]

    D --> D1[ai-research-explore]
    D --> D2[explore-code]
    D --> D3[explore-run]

    C1 -. helper .-> H1[repo-intake-and-plan]
    C1 -. helper .-> H2[paper-context-resolver]
```

## 🧠 第三场景 Explore 流程

`ai-research-explore` 面向第三场景：研究者已经冻结 task family、dataset、evaluation method，并且给出了 SOTA 参考；AI 需要在 `current_research` 上进行受约束、可审计、candidate-only 的探索。

```mermaid
flowchart LR
    A[current_research + research_campaign] --> B[analysis_outputs 与 sources]
    B --> C[IDEA_SEEDS.json<br/>受约束的 seed 扩展]
    C --> D[IDEA_SCORES.json<br/>IDEA_EVALUATION.md]
    D --> E[ATOMIC_IDEA_MAP.md 和 .json]
    E --> F[IMPLEMENTATION_FIDELITY.md 和 .json]
    F --> G{checkpoint 和 manifest 是否允许继续?}
    G -- 否 --> H[停止并输出 candidate-only blocker]
    G -- 是 --> I[bounded short-cycle runs]
    I --> J[explore_outputs<br/>candidate-only 总结]
```

当前实现的关键点：

- researcher ideas 会先保留，再按策略补充 bounded synthesized / hybrid seed ideas，输出到 `analysis_outputs/IDEA_SEEDS.json`。
- idea ranking 使用 hard gates + 显式 weighted breakdown，输出到 `analysis_outputs/IDEA_SCORES.json`。
- selected idea 会被拆成 atomic academic concepts，输出到 `analysis_outputs/ATOMIC_IDEA_MAP.md` 和 `analysis_outputs/ATOMIC_IDEA_MAP.json`。
- implementation fidelity 会区分 planned / heuristic / observed 三层证据，输出到 `analysis_outputs/IMPLEMENTATION_FIDELITY.md` 和 `analysis_outputs/IMPLEMENTATION_FIDELITY.json`。
- observed evidence 现在来自 executor 真实产出的 `changed_files`、`new_files`、`deleted_files`、`touched_paths`，而不是计划位点的伪观测。

explore lane 不得宣称 trusted reproduction success、完整 benchmark 结论、或已经验证的 novelty。

## 📦 Public Skill Matrix

| Lane | Skill | 作用 |
|---|---|---|
| Trusted | `ai-research-reproduction` | 端到端 README-first 复现 orchestrator |
| Trusted | `env-and-assets-bootstrap` | 保守的环境、数据集、checkpoint、缓存规划 |
| Trusted | `minimal-run-and-audit` | 保守的 inference、evaluation、smoke、sanity 执行 |
| Trusted | `analyze-project` | 只读项目分析、模型映射、风险暴露 |
| Trusted | `run-train` | 训练启动验证、resume 处理、有限监控与训练记录 |
| Trusted | `safe-debug` | 研究仓库安全调试：先分析，批准后才 patch |
| Explore | `ai-research-explore` | 在 `current_research` 上运行第三场景 exploratory orchestration，负责 idea gate 与 experiment governance |
| Explore | `explore-code` | 隔离分支上的 exploratory code 适配、拼接、移植 |
| Explore | `explore-run` | 小样本 probe、短周期试验、candidate run 排序 |
| Helper | `repo-intake-and-plan` | README 命令提取与仓库初扫 helper |
| Helper | `paper-context-resolver` | README 与论文上下文差距补齐 helper |

## 🧪 测试覆盖范围

本 README 不伪造一个单独的 line coverage 百分比，而是直接说明当前仓库已经被哪些回归面覆盖。

| 覆盖面 | 当前范围 | 代表性测试 |
|---|---|---|
| Registry、安装、wrapper | registry 一致性、安装目标、Claude wrappers、README 路由 | `test_skill_registry.py`、`test_install_targets.py`、`test_claude_command_wrappers.py`、`test_readme_selection.py` |
| Trusted lane 渲染与路由 | reproduction、training、analysis、debug、lane routing | `test_output_rendering.py`、`test_train_output_rendering.py`、`test_analysis_output_rendering.py`、`test_safe_debug_output_rendering.py`、`test_training_lane_routing.py` |
| Explore 主链路编排 | dry run、campaign flow、checkpoint、abandon 路径、artifact consistency、execution feasibility | `test_research_explore_dry_run.py`、`test_research_explore_campaign_flow.py`、`test_research_explore_campaign_checkpoint.py`、`test_research_explore_campaign_abandon.py`、`test_research_explore_artifact_consistency.py` |
| Explore idea 与实现合同 | idea seeds、atomic decomposition、implementation fidelity、contract schema | `test_idea_seed_generation.py`、`test_atomic_idea_decomposition.py`、`test_implementation_fidelity.py`、`test_research_explore_contracts.py` |
| Explore 执行证据链 | training / non-training executor evidence 透传 | `test_research_explore_variant_execution.py`、`test_research_explore_nontraining_execution.py` |
| Research lookup | provider、cache、inventory rendering、repo extractors、evidence layering | `test_research_lookup_arxiv_provider.py`、`test_research_lookup_repo_extractor.py`、`test_research_lookup_inventory_rendering.py`、`test_research_lookup_evidence_layers.py` |

覆盖说明：

- `scripts/validate_repo.py` 仍然是快速的文件级 validator。
- 更深的行为合同主要由上述 explore 和 rendering 回归测试来锁定。
- GitHub Actions 会在 `ubuntu-latest`、`macos-latest`、`windows-latest` 上验证该仓库。

## 📁 输出目录

| 目录 | 作用 |
|---|---|
| `repro_outputs/` | trusted reproduction 输出包 |
| `train_outputs/` | trusted training 输出包 |
| `analysis_outputs/` | 只读项目分析，以及 research map、change map、eval contract、source inventory / support、improvement bank、idea cards、idea seeds、atomic idea map、implementation fidelity、mapping、resource plan |
| `debug_outputs/` | 安全调试诊断与 patch plan |
| `sources/` | free-first research lookup 记录，包含 `sources/records/`、稳定命名、受限 provider 解析、repo-local extraction、可审计索引 |
| `explore_outputs/` | exploratory changeset、idea gate、experiment plan、experiment manifest、split static/runtime smoke reporting、ledger、top runs summary |

## 🧩 Campaign 输入

`ai-research-explore` 仍然接受普通的 `variant_spec.json`，但第三场景更推荐使用 `research_campaign.json` 或 `research_campaign.yaml`。

campaign 建议冻结：

- `task_family`
- `dataset`
- `benchmark`
- `evaluation_source`
- `sota_reference`
- `compute_budget`
- `variant_spec`

`candidate_ideas` 是推荐项，但不是必需项。`ai-research-explore` 会保留 researcher ideas，并且在策略允许时补充少量 bounded synthesized / hybrid seed ideas。新增 seed 会绑定 `current_research`、`task_family`、`dataset` 和冻结的 `evaluation_source`。

可选 campaign block：

- `research_lookup`
- `idea_policy`
- `idea_generation`
- `source_constraints`
- `feasibility_policy`

详见 [skills/ai-research-explore/references/research-campaign-spec.md](skills/ai-research-explore/references/research-campaign-spec.md)。

## 💬 示例提示词

**Trusted reproduction**

```text
Use ai-research-reproduction on this AI repo. Stay README-first, prefer documented inference or evaluation, avoid unnecessary repo changes, and write outputs to repro_outputs/.
```

**Current-research exploration**

```text
Use ai-research-explore on top of current_research improved-model@branch. Work on an isolated branch, coordinate code and run exploration together, try several variants, and rank candidates in explore_outputs/.
```

**Third-scenario campaign exploration**

```text
Use ai-research-explore with research_campaign.json. Treat the provided task family, dataset, evaluation source, and SOTA table as frozen inputs, rank the candidate ideas, keep each candidate single-variable, and write governed outputs to analysis_outputs/ and explore_outputs/.
```

**Read-only analysis**

```text
Use analyze-project on this repo. Read the code, map the model and training entrypoints, and flag suspicious patterns without editing files.
```

**Trusted training**

```text
Use run-train on this repo. Run the selected documented training command conservatively for startup verification and write train_outputs/.
```

**Safe debug**

```text
Use safe-debug on this traceback. Diagnose the failure first, propose the smallest safe fix, and do not patch until I approve.
```

**Exploratory code only**

```text
Use explore-code on an isolated branch. Try a LoRA adaptation for this backbone, keep it exploratory only, and summarize the changes in explore_outputs/.
```

**Exploratory runs only**

```text
Use explore-run on an experiment branch. Do a small-subset short-cycle sweep, rank the top runs, and treat the results as candidates only.
```

## ✅ 本地自检

运行仓库基础检查：

```bash
python scripts/validate_repo.py
python scripts/test_skill_registry.py
python scripts/test_trigger_boundaries.py
python scripts/test_claude_command_wrappers.py
python scripts/test_readme_selection.py
```

运行输出与 orchestrator 回归：

```bash
python scripts/test_output_rendering.py
python scripts/test_train_output_rendering.py
python scripts/test_analysis_output_rendering.py
python scripts/test_safe_debug_output_rendering.py
python scripts/test_explore_output_rendering.py
python scripts/test_explore_variant_matrix.py
python scripts/test_atomic_idea_decomposition.py
python scripts/test_idea_seed_generation.py
python scripts/test_implementation_fidelity.py
python scripts/test_research_explore_contracts.py
python scripts/test_research_explore_dry_run.py
python scripts/test_research_explore_campaign_flow.py
python scripts/test_research_explore_campaign_abandon.py
python scripts/test_research_explore_campaign_checkpoint.py
python scripts/test_research_explore_artifact_consistency.py
python scripts/test_research_explore_variant_execution.py
python scripts/test_research_explore_nontraining_execution.py
python scripts/test_orchestrator_dry_run.py
python scripts/test_training_lane_routing.py
```

运行 research lookup 回归：

```bash
python scripts/test_research_lookup_arxiv_provider.py
python scripts/test_research_lookup_doi_provider.py
python scripts/test_research_lookup_github_provider.py
python scripts/test_research_lookup_url_provider.py
python scripts/test_research_lookup_repo_extractor.py
python scripts/test_research_lookup_cache.py
python scripts/test_research_lookup_inventory_rendering.py
python scripts/test_research_lookup_evidence_layers.py
```

运行 setup 与安装相关回归：

```bash
python scripts/test_bootstrap_env.py
python scripts/test_install_targets.py
python scripts/test_setup_planning.py
python scripts/install_skills.py --client agents --target ./tmp/agents-skills --force
python scripts/install_skills.py --client codex --target ./tmp/codex-skills --force
python scripts/install_skills.py --client claude --target ./tmp/claude-skills --force
```

## 📚 参考文档

- Skill registry: [references/skill-registry.json](references/skill-registry.json)
- Explore variant spec: [references/explore-variant-spec.md](references/explore-variant-spec.md)
- Explore module roadmap: [references/explore-module-roadmap.md](references/explore-module-roadmap.md)
- Client compatibility policy: [references/client-compatibility-policy.md](references/client-compatibility-policy.md)
- Routing policy: [references/routing-policy.md](references/routing-policy.md)
- Trigger boundary policy: [references/trigger-boundary-policy.md](references/trigger-boundary-policy.md)
- Branch and commit policy: [references/branch-and-commit-policy.md](references/branch-and-commit-policy.md)
- Output contract: [references/output-contract.md](references/output-contract.md)
- Research pitfall checklist: [references/research-pitfall-checklist.md](references/research-pitfall-checklist.md)

## ⚠️ 当前限制

- `run-train` 是受限的训练监控器，不是长时间运行的训练调度器。
- trusted reproduction 仍然避免静默语义改动。
- helper skills 保持窄职责，不会被扩成公共兜底入口。
- exploratory work 必须与 trusted baseline 隔离。
- `ai-research-explore` 是受治理的第三场景 orchestrator，不是开放式 autonomous research agent。

## 🧱 仓库定位

这是一个强调安全性、可观测性、可复用性和边界清晰度的 lane-aware 深度学习研究技能仓库。
