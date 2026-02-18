# roam-agent-eval

Benchmark that measures the **code quality** produced by AI coding agents, evaluated by [roam-code](https://github.com/Cranot/roam-code) -- including algorithm anti-pattern detection.

**Live results:** [cranot.github.io/roam-agent-eval](https://cranot.github.io/roam-agent-eval/)

## Results at a Glance

Agent Quality Score (AQS) per task. Scale: 0-100. Grade: A (90+), B (80+), C (70+), D (60+), F (<60).

All results include `roam math` algorithm anti-pattern detection.

### Standard Tasks

| Task | Sonnet 4.6 | Sonnet 4.5 | Opus 4.6 | Codex / GPT-5.3 |
|---|---|---|---|---|
| React TODO | 72 (C) | 88 (B) | 85 (B) | 72 (C) |
| Astro Landing | 90 (A) | 100 (A) | 98 (A) | 93 (A) |
| Python Crawler | 74 (C) | 73 (C) | 68 (D) | 64 (D) |
| C++ Calculator | 50 (F) | 84 (B) | 85 (B) | 87 (B) |
| Go Log Analyzer | 52 (F) | 80 (B) | 67 (D) | 71 (C) |
| **Average** | **68 (D)** | **85 (B)** | **81 (B)** | **77 (C)** |

### Algorithm Tasks

Designed to surface algorithmic anti-patterns via `roam math`. Sonnet 4.5 not included (model deprecated before these tasks were added).

| Task | Sonnet 4.6 | Opus 4.6 | Codex / GPT-5.3 |
|---|---|---|---|
| Python ETL Pipeline | 60 (D) | **98 (A)** | 57 (F) |
| TypeScript Pathfinder | 52 (F) | 50 (F) | 50 (F) |

> All scores use the v2 AQS model (6 categories including Algorithms: health 35, quality 20, architecture 15, algorithms 10, testing 15, completeness 5).

## What Is This?

We give AI coding agents identical prompts for real-world projects across multiple languages, then measure the structural quality of their output using [roam-code](https://github.com/Cranot/roam-code) -- a static analysis tool that scores codebases on health, dead code, complexity, architecture, algorithm quality, and more.

This is **not** a functional correctness benchmark. We measure whether the code an agent produces is well-structured, maintainable, and follows engineering best practices -- the qualities that determine long-term codebase health.

## Combos, Not Just Models

We test **combos** -- specific combinations of CLI tool + version + model -- because the quality of generated code depends on both the model and the tooling around it.

Combo metadata lives in `combos.json`. CLI versions are auto-detected at evaluation time, so adding a new combo is just one JSON entry + workspace directories.

Combo IDs follow the format `{cli}-{model}`. CLI version is auto-detected at eval time — display names like `"Claude Code 2.14 / Sonnet 4.6"` are generated from `claude --version`.

| Combo ID | CLI Tool | Model | Status |
|---|---|---|---|
| `cc-sonnet4.6` | Claude Code | claude-sonnet-4-6 | Active |
| `claude-code` | Claude Code | claude-opus-4-6 | Historical (do not re-run — expensive) |
| `claude-code-sonnet` | Claude Code | claude-sonnet-4-5 | Historical (model deprecated) |
| `codex` | Codex | gpt-5.3-codex | Tested |
| `gemini-cli` | Gemini CLI | gemini-3-pro-preview | Partial |

CLI versions are recorded in each result file's `signature` field, auto-detected at eval time.

## Research Question

> How does the structural quality of AI-generated code compare across different tool + model combos and languages?

## Tasks

Each combo receives the same detailed prompt. No human editing. No follow-up guidance.

### Standard Tasks (5)

| # | Task ID | Language | What It Builds |
|---|---|---|---|
| 1 | `react-todo` | JavaScript/React | Full TODO app with categories, priorities, persistence |
| 2 | `astro-landing` | JavaScript/Astro | SaaS landing page with all sections |
| 3 | `python-crawler` | Python | Async web crawler with reports |
| 4 | `cpp-calculator` | C++ | Expression parser with REPL |
| 5 | `go-loganalyzer` | Go | Concurrent log file analyzer |

### Algorithm Tasks (2)

Designed to surface algorithmic anti-patterns that `roam math` detects: O(n^2) nested loops, N+1 query patterns, redundant computation, suboptimal data structure choices.

| # | Task ID | Language | What It Builds |
|---|---|---|---|
| 6 | `python-etl` | Python | ETL data pipeline with joins, dedup, anomaly detection |
| 7 | `ts-pathfinder` | TypeScript | Grid pathfinding library (BFS, Dijkstra, A*, JPS) |

## Methodology

1. **Prompt** -- Give each combo the same task prompt (see `prompts/`)
2. **Generate** -- Agent writes the full project from scratch into an empty workspace
3. **Index** -- Run `roam init` to build a structural index of the generated code
4. **Analyze** -- Run `roam health`, `roam dead`, `roam complexity`, `roam coupling`, `roam math`
5. **Score** -- Compute the Agent Quality Score (AQS) from roam metrics + structural checks
6. **Compare** -- Aggregate across tasks and combos

No cherry-picking. No re-runs. Each workspace in `workspaces/` is the raw, unedited output.

## Agent Quality Score (AQS)

Composite 0-100 score combining roam metrics with structural checks.

| Category | Max | What It Measures |
|---|---|---|
| Health | 35 | `roam health` score (0-100 scaled to 0-35) |
| Quality | 20 | Dead code, complexity, coupling penalties |
| Architecture | 15 | Tangle ratio, critical issues, file structure |
| Algorithms | 10 | Anti-pattern detections from `roam math` (O(n^2) loops, N+1 queries, etc.) |
| Testing | 15 | Test file count and coverage |
| Completeness | 5 | README, build config, valid project |

**Grade scale:** A (90+), B (80+), C (70+), D (60+), F (<60)

## How to Reproduce

### Prerequisites

- Python 3.9+
- [roam-code](https://github.com/Cranot/roam-code) (`pip install roam-code`)
- Git

### Generate workspaces

```bash
# See what would be generated
python generate.py --dry-run

# Generate all missing workspaces (reads combos.json for CLI commands)
python generate.py

# Generate only one combo
python generate.py --combo cc-sonnet4.6

# Generate only algorithm tasks
python generate.py --group algorithm

# Generate with 3 agents running in parallel
python generate.py --parallel 3

# Force-regenerate even if workspace has files
python generate.py --combo cc-sonnet4.6 --force
```

### Run evaluations

```bash
# List discovered workspaces and evaluation status
python run_eval.py --list

# Evaluate all workspaces (skips already-evaluated ones)
python run_eval.py

# Force re-evaluation (rescores with latest AQS model)
python run_eval.py --force

# Evaluate only one combo
python run_eval.py --combo cc-sonnet4.6

# Generate comparison report
python compare.py results/ --html results/report.html --docs
```

### Evaluate a single workspace

```bash
python evaluate.py workspaces/cc-sonnet4.6/react-todo_vanilla/ \
    --agent cc-sonnet4.6 --mode vanilla --task react-todo \
    --output results/cc-sonnet4.6_react-todo_vanilla.json
```

## How to Add a Combo

1. Add entry to `combos.json` with `cli`, `model`, and `invoke` fields
2. Create workspace directories: `workspaces/<combo-id>/<task>_vanilla/`
3. Generate: `python generate.py --combo <combo-id>`
4. Evaluate: `python run_eval.py --combo <combo-id>`

CLI version is auto-detected. Display name is auto-generated from detected version + model.

## How to Add a Task

1. Add the task definition in `prompts.py` under the `TASKS` dict (include `group` field)
2. Run `python run_eval.py --export-prompts` to generate prompt files
3. Generate workspaces: `python generate.py --task <task-id>`
4. Evaluate: `python run_eval.py`

Tasks, combos, and display names are all auto-discovered from result files and workspace directories. No hardcoded lists to update.

## Repository Structure

```
roam-agent-eval/
  combos.json         # Combo definitions: cli, model, invoke command
  generate.py         # Workspace generation: run agent CLIs on prompts
  evaluate.py         # Single-workspace evaluation using roam-code
  scoring.py          # Agent Quality Score (AQS) computation (v2: 6 categories)
  compare.py          # Cross-combo comparison + HTML report generation
  prompts.py          # Task definitions and prompt generation
  run_eval.py         # Orchestration: evaluate all workspaces
  prompts/            # Generated prompt text files (one per task+mode)
  results/            # Evaluation result JSONs + HTML report
  logs/               # Agent generation logs
  workspaces/         # Raw agent output (one dir per combo/task/mode)
  docs/               # GitHub Pages (auto-generated from compare.py --docs)
```

## Links

- **Live report:** [cranot.github.io/roam-agent-eval](https://cranot.github.io/roam-agent-eval/)
- **roam-code** (the evaluator): [github.com/Cranot/roam-code](https://github.com/Cranot/roam-code)
- **PyPI:** [pypi.org/project/roam-code](https://pypi.org/project/roam-code/)

## License

MIT
