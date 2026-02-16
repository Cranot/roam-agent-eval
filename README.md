# roam-agent-eval

Benchmark that measures the **code quality** produced by AI coding agents, evaluated by [roam-code](https://github.com/Cranot/roam-code).

**Live results:** [cranot.github.io/roam-agent-eval](https://cranot.github.io/roam-agent-eval/)

## Results at a Glance

Agent Quality Score (AQS) per task. Scale: 0-100. Grade: A (90+), B (80+), C (70+), D (60+), F (<60).

| Task | Claude Opus | Claude Sonnet | Codex |
|---|---|---|---|
| React TODO | 90 (A) | 94 (A) | 70 (C) |
| Astro Landing | 98 (A) | 100 (A) | 91 (A) |
| Python Crawler | 75 (C) | 83 (B) | 70 (C) |
| C++ Calculator | 92 (A) | 89 (B) | 91 (A) |
| Go Log Analyzer | 74 (C) | 79 (C) | 67 (D) |
| **Average** | **86 (B)** | **89 (B)** | **78 (C)** |

## What Is This?

We gave 3 AI coding agents identical prompts for 5 real-world projects across 5 different languages, then measured the structural quality of their output using [roam-code](https://github.com/Cranot/roam-code) -- a static analysis tool that scores codebases on health, dead code, complexity, architecture, coupling, and more.

This is **not** a functional correctness benchmark. We measure whether the code an agent produces is well-structured, maintainable, and follows engineering best practices -- the qualities that determine long-term codebase health.

## Research Question

> How does the structural quality of AI-generated code compare across different agents and languages?

## Tasks

Each agent receives the same detailed prompt. No human editing. No follow-up guidance.

| # | Task ID | Language | What It Builds |
|---|---|---|---|
| 1 | `react-todo` | JavaScript/React | Full TODO app with categories, priorities, persistence |
| 2 | `astro-landing` | JavaScript/Astro | SaaS landing page with all sections |
| 3 | `python-crawler` | Python | Async web crawler with reports |
| 4 | `cpp-calculator` | C++ | Expression parser with REPL |
| 5 | `go-loganalyzer` | Go | Concurrent log file analyzer |

## Agents Tested

| Agent | CLI | Model | Invocation |
|---|---|---|---|
| Claude Code (Opus) | claude 2.1.42 | claude-opus-4-6 | `claude --model opus -p` |
| Claude Code (Sonnet) | claude 2.1.42 | claude-sonnet-4-5-20250929 | `claude --model sonnet -p` |
| Codex | codex 0.101.0 | gpt-5.3-codex | `codex exec` |

All agents ran in autonomous mode with safety checks disabled (`--dangerously-skip-permissions` / `--dangerously-bypass-approvals-and-sandbox`). Each agent received the prompt once with no human intervention.

## Methodology

1. **Prompt** -- Give each agent the same task prompt (see `prompts/`)
2. **Generate** -- Agent writes the full project from scratch into an empty workspace
3. **Index** -- Run `roam init` to build a structural index of the generated code
4. **Analyze** -- Run `roam health`, `roam dead`, `roam complexity`, `roam coupling`
5. **Score** -- Compute the Agent Quality Score (AQS) from roam metrics + structural checks
6. **Compare** -- Aggregate across tasks and agents

No cherry-picking. No re-runs. Each workspace in `workspaces/` is the raw, unedited output.

## Agent Quality Score (AQS)

Composite 0-100 score combining roam metrics with structural checks.

| Category | Max | What It Measures |
|---|---|---|
| Health | 40 | `roam health` score (0-100 scaled to 0-40) |
| Quality | 25 | Dead code, complexity, coupling penalties |
| Architecture | 15 | Tangle ratio, critical issues, file structure |
| Testing | 15 | Test file count and coverage |
| Completeness | 5 | README, build config, valid project |

**Penalties applied:**
- Dead code: -2 per dead symbol (max -10 from Quality)
- High avg complexity (>5): -1 per point (max -8 from Quality)
- High P90 complexity (>15): -1 per point (max -5 from Quality)
- High complexity functions: -2 each (max -7 from Quality)
- Tangle ratio: -10 * ratio (max -5 from Architecture)
- Critical issues: -3 each (max -10 from Architecture)

**Grade scale:** A (90+), B (80+), C (70+), D (60+), F (<60)

## Full Results

### Category Breakdown

**React TODO**

| Agent | AQS | Health /40 | Quality /25 | Arch /15 | Testing /15 | Complete /5 |
|---|---|---|---|---|---|---|
| Claude Opus | 90 | 37 | 18 | 15 | 15 | 5 |
| Claude Sonnet | 94 | 38 | 21 | 15 | 15 | 5 |
| Codex | 70 | 21 | 25 | 10 | 9 | 5 |

**Astro Landing**

| Agent | AQS | Health /40 | Quality /25 | Arch /15 | Testing /15 | Complete /5 |
|---|---|---|---|---|---|---|
| Claude Opus | 98 | 40 | 25 | 15 | 13 | 5 |
| Claude Sonnet | 100 | 40 | 25 | 15 | 15 | 5 |
| Codex | 91 | 38 | 20 | 15 | 13 | 5 |

**Python Crawler**

| Agent | AQS | Health /40 | Quality /25 | Arch /15 | Testing /15 | Complete /5 |
|---|---|---|---|---|---|---|
| Claude Opus | 75 | 31 | 15 | 9 | 15 | 5 |
| Claude Sonnet | 83 | 37 | 11 | 15 | 15 | 5 |
| Codex | 70 | 30 | 13 | 7 | 15 | 5 |

**C++ Calculator**

| Agent | AQS | Health /40 | Quality /25 | Arch /15 | Testing /15 | Complete /5 |
|---|---|---|---|---|---|---|
| Claude Opus | 92 | 40 | 17 | 15 | 15 | 5 |
| Claude Sonnet | 89 | 39 | 23 | 15 | 7 | 5 |
| Codex | 91 | 39 | 25 | 15 | 7 | 5 |

**Go Log Analyzer**

| Agent | AQS | Health /40 | Quality /25 | Arch /15 | Testing /15 | Complete /5 |
|---|---|---|---|---|---|---|
| Claude Opus | 74 | 32 | 7 | 15 | 15 | 5 |
| Claude Sonnet | 79 | 36 | 8 | 15 | 15 | 5 |
| Codex | 67 | 31 | 8 | 10 | 13 | 5 |

### Agent Averages

| Agent | Avg AQS | Avg Health | Avg Quality | Avg Arch | Avg Testing | Avg Complete |
|---|---|---|---|---|---|---|
| Claude Opus | 86 | 36.0 | 16.4 | 13.8 | 14.6 | 5.0 |
| Claude Sonnet | 89 | 38.0 | 17.6 | 15.0 | 13.4 | 5.0 |
| Codex | 78 | 31.8 | 18.2 | 11.4 | 11.4 | 5.0 |

## Key Findings

1. **Claude Sonnet leads overall** with an average AQS of 89 (B), followed by Claude Opus at 86 (B) and Codex at 78 (C).

2. **All agents struggle with Go** -- the Go Log Analyzer task produced the lowest scores across every agent. Complex concurrency patterns and Go's package structure seem to challenge current models.

3. **Codex produces lower health scores** but competitive raw code quality -- its Quality subscores are often on par with or better than Claude's, suggesting the gap is in architecture and testing habits.

4. **Testing varies wildly** -- Claude consistently generates test files across all projects, while Codex sometimes skips them (notably for C++ and React).

5. **Architecture is the differentiator** -- Claude Sonnet achieved perfect architecture scores (15/15) across all tasks, while Codex lost points on Python, Go, and React projects.

6. **Astro is the easiest task** -- all agents scored 91+ on the landing page, likely because it involves less algorithmic complexity.

## How to Reproduce

### Prerequisites

- Python 3.9+
- [roam-code](https://github.com/Cranot/roam-code) (`pip install roam-code`)
- Git

### Run evaluations

```bash
# Check which workspaces exist and their evaluation status
python run_eval.py --list

# Evaluate all workspaces (skips already-evaluated ones)
python run_eval.py

# Force re-evaluation of everything
python run_eval.py --force

# Generate comparison report
python compare.py results/ --html results/report.html --docs
```

### Evaluate a single workspace

```bash
python evaluate.py workspaces/claude-code/react-todo_vanilla/ \
    --agent claude-code --mode vanilla --task react-todo \
    --output results/claude-code_react-todo_vanilla.json
```

## How to Add an Agent

1. Create workspace directories: `workspaces/<agent-name>/<task>_vanilla/`
2. Give the agent the prompt from `prompts/<task>_vanilla.txt`
3. Run `python run_eval.py` -- it will find and evaluate the new workspaces
4. Regenerate the report: `python compare.py results/ --html results/report.html --docs`

## How to Add a Task

1. Add the task definition in `prompts.py` under the `TASKS` dict
2. Add the task ID to the `TASKS` list in `compare.py`
3. Run `python run_eval.py --export-prompts` to generate prompt files
4. Create workspaces for each agent and run evaluations

## Repository Structure

```
roam-agent-eval/
  compare.py          # Cross-agent comparison + HTML report generation
  evaluate.py         # Single-workspace evaluation using roam-code
  scoring.py          # Agent Quality Score (AQS) computation
  prompts.py          # Task definitions and prompt generation
  run_eval.py         # Orchestration: evaluate all workspaces
  prompts/            # Generated prompt text files (one per task+mode)
  results/            # Evaluation result JSONs + HTML report
  workspaces/         # Raw agent output (one dir per agent/task/mode)
    claude-code/      # Claude Code Opus workspaces
    claude-code-sonnet/ # Claude Code Sonnet workspaces
    codex/            # Codex workspaces
  docs/               # GitHub Pages (auto-generated from compare.py --docs)
```

## Links

- **Live report:** [cranot.github.io/roam-agent-eval](https://cranot.github.io/roam-agent-eval/)
- **roam-code** (the evaluator): [github.com/Cranot/roam-code](https://github.com/Cranot/roam-code)
- **PyPI:** [pypi.org/project/roam-code](https://pypi.org/project/roam-code/)

## License

MIT
