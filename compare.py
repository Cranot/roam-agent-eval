#!/usr/bin/env python3
"""
Compare evaluation results across combos, modes, and tasks.

Auto-discovers combos, tasks, and display names from result JSON files.
No hardcoded agent lists — everything is derived from the data.

Usage:
    python compare.py results/              # compare all results in directory
    python compare.py results/ --html       # generate HTML report
    python compare.py results/ --html --docs  # also output to docs/index.html
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# Task display names — only these need to be known ahead of time
TASK_DISPLAY = {
    "react-todo": "React TODO",
    "astro-landing": "Astro Landing",
    "python-crawler": "Python Crawler",
    "cpp-calculator": "C++ Calculator",
    "go-loganalyzer": "Go Log Analyzer",
    "python-etl": "Python ETL Pipeline",
    "ts-pathfinder": "TypeScript Pathfinder",
}

# Task groups
TASK_GROUPS = {
    "standard": ["react-todo", "astro-landing", "python-crawler", "cpp-calculator", "go-loganalyzer"],
    "algorithm": ["python-etl", "ts-pathfinder"],
}

MODES = ["vanilla", "roam-cli", "roam-mcp"]

SCORE_COLUMNS = [
    ("health", "Health", "{}", True),              # higher is better
    ("dead_symbols", "Dead", "{}", False),          # lower is better
    ("avg_complexity", "AvgCx", "{:.1f}", False),   # lower is better
    ("p90_complexity", "P90Cx", "{:.1f}", False),   # lower is better
    ("high_complexity_count", "HiCx", "{}", False), # lower is better
    ("tangle_ratio", "Tangle", "{:.2f}", False),    # lower is better
    ("hidden_coupling", "HidCoup", "{}", False),    # lower is better
    ("antipattern_total", "AntiPat", "{}", False),  # lower is better
    ("antipattern_high", "AP-Hi", "{}", False),     # lower is better
    ("critical_issues", "Crit", "{}", False),       # lower is better
    ("warning_issues", "Warn", "{}", False),        # lower is better
]


# ---------------------------------------------------------------------------
# Data loading — everything auto-discovered from results
# ---------------------------------------------------------------------------

def load_results(results_dir: Path) -> list[dict]:
    """Load all result JSON files from a directory."""
    results = []
    for f in sorted(results_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            results.append(data)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: skipping {f}: {e}", file=sys.stderr)
    return results


def discover_combos(results: list[dict]) -> list[str]:
    """Auto-discover combo IDs from results, in a stable order."""
    seen = {}
    for r in results:
        agent = r.get("agent", "?")
        if agent not in seen:
            seen[agent] = len(seen)
    return sorted(seen, key=lambda a: seen[a])


def discover_tasks(results: list[dict]) -> list[str]:
    """Auto-discover task IDs from results, in a stable order."""
    seen = {}
    for r in results:
        task = r.get("task", "?")
        if task not in seen:
            seen[task] = len(seen)
    return sorted(seen, key=lambda t: seen[t])


def discover_groups(results: list[dict]) -> dict[str, list[str]]:
    """Auto-discover task groups from results."""
    groups: dict[str, set[str]] = {}
    for r in results:
        group = r.get("group", "standard")
        task = r.get("task", "?")
        groups.setdefault(group, set()).add(task)
    # Return with stable ordering
    return {g: sorted(tasks) for g, tasks in sorted(groups.items())}


def build_combo_display(results: list[dict]) -> dict[str, str]:
    """Build display names from signature data in results."""
    display = {}
    for r in results:
        agent = r.get("agent")
        sig = r.get("signature", {})
        if agent and sig and agent not in display:
            d = sig.get("display")
            if d:
                display[agent] = d
            else:
                # Build from parts
                cli = sig.get("cli_cmd", "?")
                ver = sig.get("cli_version", "?")
                model = sig.get("model_short", sig.get("model", "?"))
                display[agent] = f"{cli} {ver} / {model}"
    return display


def build_lookup(results: list[dict]) -> dict:
    """Build a {(agent, mode, task): scores} lookup."""
    lookup = {}
    for r in results:
        key = (r.get("agent", "?"), r.get("mode", "?"), r.get("task", "?"))
        lookup[key] = r.get("scores", {})
    return lookup


def build_aqs_lookup(results: list[dict]) -> dict:
    """Build a {(agent, mode, task): aqs_dict} lookup."""
    lookup = {}
    for r in results:
        key = (r.get("agent", "?"), r.get("mode", "?"), r.get("task", "?"))
        aqs = r.get("aqs", {})
        if aqs:
            lookup[key] = aqs
    return lookup


def build_signature_lookup(results: list[dict]) -> dict:
    """Build a {agent: signature} lookup from results."""
    sigs = {}
    for r in results:
        agent = r.get("agent")
        sig = r.get("signature")
        if agent and sig:
            sigs[agent] = sig
    return sigs


# ---------------------------------------------------------------------------
# Text output
# ---------------------------------------------------------------------------

def print_task_table(task: str, agents: list[str], lookup: dict, combo_display: dict):
    """Print comparison table for one task."""
    print(f"\n{'=' * 80}")
    print(f"  TASK: {TASK_DISPLAY.get(task, task)}")
    print(f"{'=' * 80}")

    header = f"{'Combo':<30} {'Mode':<10}"
    for _, label, _, _ in SCORE_COLUMNS:
        header += f" {label:>8}"
    print(header)
    print("-" * len(header))

    for agent in agents:
        for mode in MODES:
            key = (agent, mode, task)
            scores = lookup.get(key)
            if not scores:
                continue

            display = combo_display.get(agent, agent)[:28]
            row = f"{display:<30} {mode:<10}"
            for field, _, fmt, _ in SCORE_COLUMNS:
                val = scores.get(field)
                if val is None:
                    row += f" {'N/A':>8}"
                elif isinstance(val, bool):
                    row += f" {'PASS' if val else 'FAIL':>8}"
                else:
                    try:
                        row += f" {fmt.format(val):>8}"
                    except (ValueError, TypeError):
                        row += f" {str(val)[:8]:>8}"
            print(row)


def print_agent_summary(agent: str, tasks: list[str], lookup: dict, combo_display: dict):
    """Print aggregate scores for one agent across all tasks."""
    display = combo_display.get(agent, agent)
    print(f"\n--- {display} ---")
    for mode in MODES:
        health_scores = []
        dead_total = 0
        complexities = []
        task_count = 0

        for task in tasks:
            scores = lookup.get((agent, mode, task))
            if not scores:
                continue
            task_count += 1
            if scores.get("health") is not None:
                health_scores.append(scores["health"])
            if scores.get("dead_symbols") is not None:
                dead_total += scores["dead_symbols"]
            if scores.get("avg_complexity") is not None:
                complexities.append(scores["avg_complexity"])

        if task_count == 0:
            continue

        avg_health = sum(health_scores) / len(health_scores) if health_scores else None
        avg_cx = sum(complexities) / len(complexities) if complexities else None

        print(f"  {mode:<10}  "
              f"avg_health={avg_health or 'N/A':>5}  "
              f"dead={dead_total:>3}  "
              f"avg_cx={f'{avg_cx:.1f}' if avg_cx else 'N/A':>5}  "
              f"tasks={task_count}")


# ---------------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------------

def _grade_cls(grade: str) -> str:
    return f"grade-{grade.lower()}"


def _grade_badge(grade: str, score: int) -> str:
    return f'<span class="badge {_grade_cls(grade)}">{score} ({grade})</span>'


def _score_grade(score: float) -> str:
    if score >= 90: return "A"
    if score >= 80: return "B"
    if score >= 70: return "C"
    if score >= 60: return "D"
    return "F"


def _th(label: str, cls: str = "") -> str:
    if cls:
        return f'<th class="{cls}">{label}</th>'
    return f'<th>{label}</th>'


def _td(content: str, cls: str = "") -> str:
    if cls:
        return f'<td class="{cls}">{content}</td>'
    return f'<td>{content}</td>'


def generate_html_report(
    lookup: dict, aqs_lookup: dict, signatures: dict,
    combo_display: dict, agents: list[str], tasks: list[str],
    groups: dict[str, list[str]], output: Path,
):
    """Generate an HTML comparison report with AQS overview."""
    html = ["""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Agent Code Quality Benchmark — roam-agent-eval</title>
<style>
  :root {
    --bg: #f8f9fa; --fg: #1a1a2e; --card: white;
    --border: #e2e8f0; --hdr: #1a1a2e;
    --green: #2d8a4e; --green-bg: #e6f4ea;
    --blue: #3b82f6; --blue-bg: #dbeafe;
    --orange: #e67e22; --orange-bg: #fef3e2;
    --red: #d32f2f; --red-bg: #fce8e6;
    --purple: #9333ea; --slate: #64748b;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    max-width: 1200px; margin: 0 auto; padding: 40px 20px;
    background: var(--bg); color: var(--fg); line-height: 1.6;
  }
  h1 { text-align: center; margin-bottom: 4px; font-size: 2em; }
  .subtitle { text-align: center; color: #666; margin-bottom: 12px; font-size: 1.1em; }
  .meta { text-align: center; color: #999; margin-bottom: 40px; font-size: 0.9em; }
  .meta a { color: var(--blue); text-decoration: none; }
  .meta a:hover { text-decoration: underline; }
  h2 { border-bottom: 2px solid var(--hdr); padding-bottom: 8px; margin-top: 48px; }
  h3 { margin-top: 32px; color: #444; }
  p { margin: 8px 0; }
  .group-label {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.5px; margin-left: 8px; vertical-align: middle;
  }
  .group-standard { background: var(--blue-bg); color: var(--blue); }
  .group-algorithm { background: var(--red-bg); color: var(--red); }

  table {
    width: 100%; border-collapse: collapse; margin: 16px 0;
    background: var(--card); border-radius: 8px; overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  th, td { padding: 10px 14px; font-size: 14px; }
  th {
    background: var(--hdr); color: white;
    font-size: 12px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.5px; white-space: nowrap;
  }
  td { border-bottom: 1px solid var(--border); }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #f0f4ff; }
  th, td { text-align: left; }
  th.c, td.c { text-align: center; }
  th.r, td.r { text-align: right; font-variant-numeric: tabular-nums; }
  td.muted { color: #999; text-align: center; }
  tr.summary td { border-top: 2px solid var(--hdr); font-weight: 600; }

  .badge {
    display: inline-block; padding: 3px 10px; border-radius: 4px;
    font-size: 13px; font-weight: 700; letter-spacing: 0.3px;
    white-space: nowrap;
  }
  .grade-a { background: var(--green-bg); color: var(--green); }
  .grade-b { background: var(--blue-bg); color: var(--blue); }
  .grade-c { background: var(--orange-bg); color: var(--orange); }
  .grade-d { background: var(--red-bg); color: var(--red); }
  .grade-f { background: var(--red-bg); color: #8b0000; }

  .bar {
    display: inline-block; height: 8px; border-radius: 4px;
    vertical-align: middle; margin-left: 6px;
  }
  .bar-health    { background: var(--green); }
  .bar-quality   { background: var(--blue); }
  .bar-arch      { background: var(--purple); }
  .bar-algo      { background: #e74c3c; }
  .bar-testing   { background: var(--orange); }
  .bar-complete  { background: var(--slate); }

  .pos { color: var(--green); font-weight: 600; }
  .neg { color: var(--red); font-weight: 600; }

  footer {
    margin-top: 60px; padding-top: 20px; border-top: 1px solid var(--border);
    text-align: center; color: #999; font-size: 0.85em;
  }
  footer a { color: var(--blue); text-decoration: none; }

  @media (max-width: 768px) {
    body { padding: 20px 10px; }
    table { font-size: 12px; }
    th, td { padding: 6px 8px; }
    .bar { display: none; }
  }
</style></head><body>
<h1>AI Agent Code Quality Benchmark</h1>
<p class="subtitle">How well do AI coding agents write code? Measured by <a href="https://github.com/Cranot/roam-code">roam-code</a>.</p>
"""]

    active_agents = [a for a in agents if any(
        (a, m, t) in aqs_lookup for m in MODES for t in tasks
    )]
    n_evals = sum(1 for a in agents for m in MODES for t in tasks if (a, m, t) in lookup)

    html.append(f'<p class="meta">{len(tasks)} tasks &middot; '
                f'{len(active_agents)} combos &middot; {n_evals} evaluations &middot; '
                f'<a href="https://github.com/Cranot/roam-agent-eval">Source &amp; methodology</a></p>')

    # ---- Generate sections per group ----
    for group_name, group_tasks in groups.items():
        group_active_tasks = [t for t in group_tasks if any(
            (a, m, t) in lookup for a in agents for m in MODES
        )]
        if not group_active_tasks:
            continue

        group_cls = f"group-{group_name}"
        group_label = f'<span class="group-label {group_cls}">{group_name}</span>'

        # ---- AQS Overview Table ----
        html.append(f'<h2>Results: {group_name.title()} Tasks {group_label}</h2>')
        html.append('<p>Agent Quality Score (AQS) per task. Scale: 0&ndash;100. '
                    'Grade: A (90+), B (80+), C (70+), D (60+), F (&lt;60).</p>')
        html.append('<table>')
        html.append(f'<tr>{_th("Task")}')
        for agent in active_agents:
            html.append(_th(combo_display.get(agent, agent), "c"))
        html.append('</tr>')

        agent_totals: dict[str, list[int]] = {a: [] for a in active_agents}

        for task in group_active_tasks:
            html.append(f'<tr><td><strong>{TASK_DISPLAY.get(task, task)}</strong></td>')
            for agent in active_agents:
                aqs = aqs_lookup.get((agent, "vanilla", task))
                if not aqs:
                    for mode in MODES:
                        aqs = aqs_lookup.get((agent, mode, task))
                        if aqs:
                            break
                if aqs:
                    html.append(_td(_grade_badge(aqs["grade"], aqs["aqs"]), "c"))
                    agent_totals[agent].append(aqs["aqs"])
                else:
                    html.append(_td("--", "muted"))
            html.append('</tr>')

        # Average row
        html.append('<tr class="summary"><td><strong>Average</strong></td>')
        for agent in active_agents:
            scores = agent_totals[agent]
            if scores:
                avg = sum(scores) / len(scores)
                g = _score_grade(avg)
                html.append(_td(_grade_badge(g, round(avg)), "c"))
            else:
                html.append(_td("--", "muted"))
        html.append('</tr></table>')

        # ---- Category Breakdown ----
        categories = ["health", "quality", "architecture", "algorithms", "testing", "completeness"]
        cat_max = {"health": 35, "quality": 20, "architecture": 15,
                   "algorithms": 10, "testing": 15, "completeness": 5}
        cat_bar_cls = {"health": "bar-health", "quality": "bar-quality",
                       "architecture": "bar-arch", "algorithms": "bar-algo",
                       "testing": "bar-testing", "completeness": "bar-complete"}
        cat_short = {"health": "Health", "quality": "Quality", "architecture": "Arch",
                     "algorithms": "Algo", "testing": "Testing", "completeness": "Complete"}
        bar_max_px = 60

        html.append(f'<h3>Category Breakdown</h3>')
        html.append('<p>AQS breaks into 6 categories: Health (35), Quality (20), '
                    'Architecture (15), Algorithms (10), Testing (15), Completeness (5).</p>')

        for task in group_active_tasks:
            html.append(f'<h3>{TASK_DISPLAY.get(task, task)}</h3>')
            html.append(f'<table><tr>{_th("Combo")}{_th("AQS", "c")}')
            for cat in categories:
                html.append(_th(f'{cat_short[cat]} /{cat_max[cat]}', "r"))
            html.append('</tr>')

            for agent in active_agents:
                aqs = aqs_lookup.get((agent, "vanilla", task))
                if not aqs:
                    continue
                bd = aqs.get("breakdown", {})
                html.append(f'<tr><td>{combo_display.get(agent, agent)}</td>')
                html.append(_td(f'<strong>{aqs["aqs"]}</strong>', "c"))
                for cat in categories:
                    val = bd.get(cat, 0)
                    mx = cat_max[cat]
                    pct = val / mx if mx > 0 else 0
                    px = round(pct * bar_max_px)
                    bar = f'<span class="bar {cat_bar_cls[cat]}" style="width:{px}px"></span>'
                    html.append(_td(f'{val}{bar}', "r"))
                html.append('</tr>')
            html.append('</table>')

    # ---- Overall Combo Averages ----
    categories = ["health", "quality", "architecture", "algorithms", "testing", "completeness"]
    cat_max = {"health": 35, "quality": 20, "architecture": 15,
               "algorithms": 10, "testing": 15, "completeness": 5}
    cat_short = {"health": "Health", "quality": "Quality", "architecture": "Arch",
                 "algorithms": "Algo", "testing": "Testing", "completeness": "Complete"}

    html.append('<h2>Combo Averages (All Tasks)</h2>')
    html.append('<p>Average scores across all tasks (vanilla mode).</p>')
    html.append(f'<table><tr>{_th("Combo")}{_th("Avg AQS", "c")}')
    for cat in categories:
        html.append(_th(f'Avg {cat_short[cat]}', "r"))
    html.append('</tr>')

    for agent in active_agents:
        cat_sums: dict[str, list] = {c: [] for c in categories}
        aqs_scores: list[int] = []
        for task in tasks:
            aqs = aqs_lookup.get((agent, "vanilla", task))
            if not aqs:
                continue
            aqs_scores.append(aqs["aqs"])
            bd = aqs.get("breakdown", {})
            for cat in categories:
                if cat in bd:
                    cat_sums[cat].append(bd[cat])

        if not aqs_scores:
            continue

        avg_aqs = sum(aqs_scores) / len(aqs_scores)
        g = _score_grade(avg_aqs)

        html.append(f'<tr><td>{combo_display.get(agent, agent)}</td>')
        html.append(_td(_grade_badge(g, round(avg_aqs)), "c"))
        for cat in categories:
            vals = cat_sums[cat]
            if vals:
                avg = sum(vals) / len(vals)
                html.append(_td(f'{avg:.1f}/{cat_max[cat]}', "r"))
            else:
                html.append(_td("--", "muted"))
        html.append('</tr>')
    html.append('</table>')

    # ---- Combo Signatures ----
    if signatures:
        html.append('<h2>Combo Signatures</h2>')
        html.append(f'<table><tr>{_th("Combo")}{_th("CLI Tool")}{_th("CLI Version")}{_th("Model")}</tr>')
        for agent in active_agents:
            sig = signatures.get(agent, {})
            if sig:
                html.append(f'<tr><td>{combo_display.get(agent, agent)}</td>'
                            f'<td>{sig.get("cli_cmd", "N/A")}</td>'
                            f'<td>{sig.get("cli_version", "N/A")}</td>'
                            f'<td>{sig.get("model", "N/A")}</td></tr>')
        roam_ver = next((s.get("roam_version") for s in signatures.values() if s.get("roam_version")), None)
        html.append('</table>')
        if roam_ver:
            html.append(f'<p>Evaluator: <strong>roam-code {roam_ver}</strong></p>')

    # ---- Raw Metrics Tables ----
    html.append('<h2>Raw Metrics by Task</h2>')
    html.append('<p>Detailed roam-code metrics for each task and combo.</p>')

    for task in tasks:
        if not any((a, m, task) in lookup for a in agents for m in MODES):
            continue
        html.append(f'<h3>{TASK_DISPLAY.get(task, task)}</h3>')
        html.append(f'<table><tr>{_th("Combo")}{_th("Mode")}')
        for _, label, _, _ in SCORE_COLUMNS:
            html.append(_th(label, "r"))
        html.append('</tr>')

        for agent in agents:
            for mode in MODES:
                scores = lookup.get((agent, mode, task))
                if not scores:
                    continue
                html.append(f'<tr><td>{combo_display.get(agent, agent)}</td><td>{mode}</td>')
                for field, _, fmt, _ in SCORE_COLUMNS:
                    val = scores.get(field)
                    if val is None:
                        html.append(_td("--", "muted"))
                    else:
                        try:
                            formatted = fmt.format(val)
                        except (ValueError, TypeError):
                            formatted = str(val)
                        html.append(_td(formatted, "r"))
                html.append('</tr>')
        html.append('</table>')

    # ---- Footer ----
    html.append("""<footer>
<p>Generated by <a href="https://github.com/Cranot/roam-agent-eval">roam-agent-eval</a>
&middot; Evaluated with <a href="https://github.com/Cranot/roam-code">roam-code</a></p>
</footer>
</body></html>""")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(html), encoding="utf-8")
    print(f"HTML report saved to: {output}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Compare agent evaluation results")
    parser.add_argument("results_dir", type=Path, help="Directory with result JSON files")
    parser.add_argument("--html", type=Path, help="Generate HTML report")
    parser.add_argument("--docs", action="store_true",
                        help="Also output report to docs/index.html (for GitHub Pages)")
    args = parser.parse_args()

    if not args.results_dir.is_dir():
        print(f"Error: {args.results_dir} is not a directory")
        sys.exit(1)

    results = load_results(args.results_dir)
    if not results:
        print("No result files found.")
        sys.exit(1)

    print(f"Loaded {len(results)} result files.\n")

    # Auto-discover everything from the data
    agents = discover_combos(results)
    tasks = discover_tasks(results)
    groups = discover_groups(results)
    combo_display = build_combo_display(results)
    lookup = build_lookup(results)
    aqs_lookup = build_aqs_lookup(results)
    signatures = build_signature_lookup(results)

    # Print combo signatures
    if signatures:
        print(f"{'=' * 90}")
        print("  COMBO SIGNATURES")
        print(f"{'=' * 90}")
        print(f"{'Combo':<30} {'CLI Version':<20} {'Model':<30}")
        print("-" * 90)
        for agent in agents:
            sig = signatures.get(agent)
            if sig:
                display = combo_display.get(agent, agent)
                print(f"{display:<30} {sig.get('cli_version', 'N/A'):<20} {sig.get('model', 'N/A'):<30}")
        roam_ver = next((s.get("roam_version") for s in signatures.values() if s.get("roam_version")), None)
        if roam_ver:
            print(f"\nEvaluator: roam-code {roam_ver}")
        print()

    # Print per-task tables
    for task in tasks:
        if any(k[2] == task for k in lookup):
            print_task_table(task, agents, lookup, combo_display)

    # Combo summaries
    print(f"\n{'=' * 80}")
    print("  COMBO SUMMARIES")
    print(f"{'=' * 80}")
    for agent in agents:
        if any(k[0] == agent for k in lookup):
            print_agent_summary(agent, tasks, lookup, combo_display)

    # HTML report
    if args.html:
        generate_html_report(lookup, aqs_lookup, signatures,
                             combo_display, agents, tasks, groups, args.html)

    # Also output to docs/ for GitHub Pages
    if args.docs:
        docs_path = Path(__file__).parent / "docs" / "index.html"
        generate_html_report(lookup, aqs_lookup, signatures,
                             combo_display, agents, tasks, groups, docs_path)


if __name__ == "__main__":
    main()
