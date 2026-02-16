#!/usr/bin/env python3
"""
Compare evaluation results across agents, modes, and tasks.

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


AGENTS = ["claude-code", "claude-code-sonnet", "codex", "gemini-cli"]
MODES = ["vanilla", "roam-cli", "roam-mcp"]
TASKS = ["react-todo", "astro-landing", "python-crawler", "cpp-calculator", "go-loganalyzer"]

TASK_DISPLAY = {
    "react-todo": "React TODO",
    "astro-landing": "Astro Landing",
    "python-crawler": "Python Crawler",
    "cpp-calculator": "C++ Calculator",
    "go-loganalyzer": "Go Log Analyzer",
}

AGENT_DISPLAY = {
    "claude-code": "Claude Opus 4.6",
    "claude-code-sonnet": "Claude Sonnet 4.5",
    "codex": "Codex (GPT-5.3)",
    "gemini-cli": "Gemini CLI",
}

SCORE_COLUMNS = [
    ("health", "Health", "{}", True),              # higher is better
    ("dead_symbols", "Dead", "{}", False),          # lower is better
    ("avg_complexity", "AvgCx", "{:.1f}", False),   # lower is better
    ("p90_complexity", "P90Cx", "{:.1f}", False),   # lower is better
    ("high_complexity_count", "HiCx", "{}", False), # lower is better
    ("tangle_ratio", "Tangle", "{:.2f}", False),    # lower is better
    ("hidden_coupling", "HidCoup", "{}", False),    # lower is better
    ("critical_issues", "Crit", "{}", False),       # lower is better
    ("warning_issues", "Warn", "{}", False),        # lower is better
]


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


def print_task_table(task: str, lookup: dict):
    """Print comparison table for one task."""
    print(f"\n{'=' * 80}")
    print(f"  TASK: {task}")
    print(f"{'=' * 80}")

    # Header
    header = f"{'Agent':<14} {'Mode':<10}"
    for _, label, _, _ in SCORE_COLUMNS:
        header += f" {label:>8}"
    print(header)
    print("-" * len(header))

    for agent in AGENTS:
        for mode in MODES:
            key = (agent, mode, task)
            scores = lookup.get(key)
            if not scores:
                continue

            row = f"{agent:<14} {mode:<10}"
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


def print_agent_summary(agent: str, lookup: dict):
    """Print aggregate scores for one agent across all tasks."""
    print(f"\n--- {agent} ---")
    for mode in MODES:
        health_scores = []
        dead_total = 0
        complexities = []
        cycles_total = 0
        gate_passes = 0
        task_count = 0

        for task in TASKS:
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
            if scores.get("cycle_count") is not None:
                cycles_total += scores["cycle_count"]
            if scores.get("gate_passed"):
                gate_passes += 1

        if task_count == 0:
            continue

        avg_health = sum(health_scores) / len(health_scores) if health_scores else None
        avg_cx = sum(complexities) / len(complexities) if complexities else None

        print(f"  {mode:<10}  "
              f"avg_health={avg_health or 'N/A':>5}  "
              f"dead={dead_total:>3}  "
              f"avg_cx={f'{avg_cx:.1f}' if avg_cx else 'N/A':>5}  "
              f"cycles={cycles_total:>2}  "
              f"gates={gate_passes}/{task_count}")


def print_mode_comparison(lookup: dict):
    """Show how roam modes compare to vanilla for each agent."""
    print(f"\n{'=' * 80}")
    print("  MODE IMPACT -- Health score delta (roam mode - vanilla)")
    print(f"{'=' * 80}")

    header = f"{'Agent':<14}"
    for task in TASKS:
        header += f" {task[:10]:>12}"
    header += f" {'AVG':>8}"
    print(header)
    print("-" * len(header))

    for agent in AGENTS:
        for mode in ["roam-cli", "roam-mcp"]:
            row = f"{agent:<14}"
            deltas = []
            for task in TASKS:
                vanilla = lookup.get((agent, "vanilla", task), {}).get("health")
                enhanced = lookup.get((agent, mode, task), {}).get("health")
                if vanilla is not None and enhanced is not None:
                    delta = enhanced - vanilla
                    deltas.append(delta)
                    sign = "+" if delta > 0 else ""
                    row += f" {sign}{delta:>10}"
                else:
                    row += f" {'N/A':>12}"
            avg_delta = sum(deltas) / len(deltas) if deltas else None
            if avg_delta is not None:
                sign = "+" if avg_delta > 0 else ""
                row += f" {sign}{avg_delta:>6.1f}"
            else:
                row += f" {'N/A':>8}"
            print(f"{row}  ({mode})")


def _grade_cls(grade: str) -> str:
    """Return CSS class name for a letter grade."""
    return f"grade-{grade.lower()}"


def _grade_badge(grade: str, score: int) -> str:
    """Return an HTML badge for a grade + score."""
    return f'<span class="badge {_grade_cls(grade)}">{score} ({grade})</span>'


def _score_grade(score: float) -> str:
    """Return letter grade for a numeric score."""
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _th(label: str, cls: str = "") -> str:
    """Emit a <th> with optional class."""
    if cls:
        return f'<th class="{cls}">{label}</th>'
    return f'<th>{label}</th>'


def _td(content: str, cls: str = "") -> str:
    """Emit a <td> with optional class."""
    if cls:
        return f'<td class="{cls}">{content}</td>'
    return f'<td>{content}</td>'


def generate_html_report(lookup: dict, aqs_lookup: dict, signatures: dict, output: Path):
    """Generate an HTML comparison report with AQS overview."""
    # Check if mode impact data exists
    has_mode_data = False
    for agent in AGENTS:
        for mode in ["roam-cli", "roam-mcp"]:
            for task in TASKS:
                if (agent, mode, task) in lookup:
                    has_mode_data = True
                    break

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

  /* --- Tables --- */
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

  /* Alignment: label columns left, data columns center */
  th, td { text-align: left; }
  th.c, td.c { text-align: center; }
  th.r, td.r { text-align: right; font-variant-numeric: tabular-nums; }
  td.muted { color: #999; text-align: center; }

  /* Summary row separator */
  tr.summary td { border-top: 2px solid var(--hdr); font-weight: 600; }

  /* --- Badges --- */
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
  .badge-pass { background: var(--green-bg); color: var(--green); }
  .badge-fail { background: var(--red-bg); color: var(--red); }

  /* --- Bars --- */
  .bar {
    display: inline-block; height: 8px; border-radius: 4px;
    vertical-align: middle; margin-left: 6px;
  }
  .bar-health    { background: var(--green); }
  .bar-quality   { background: var(--blue); }
  .bar-arch      { background: var(--purple); }
  .bar-testing   { background: var(--orange); }
  .bar-complete  { background: var(--slate); }

  /* --- Deltas --- */
  .pos { color: var(--green); font-weight: 600; }
  .neg { color: var(--red); font-weight: 600; }

  /* --- Footer --- */
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

    active_agents = [a for a in AGENTS if any((a, m, t) in aqs_lookup for m in MODES for t in TASKS)]
    active_tasks = [t for t in TASKS if any((a, m, t) in lookup for a in AGENTS for m in MODES)]
    n_evals = sum(1 for a in AGENTS for m in MODES for t in TASKS if (a, m, t) in lookup)

    html.append(f'<p class="meta">{len(active_tasks)} tasks &middot; '
                f'{len(active_agents)} agents &middot; {n_evals} evaluations &middot; '
                f'<a href="https://github.com/Cranot/roam-agent-eval">Source &amp; methodology</a></p>')

    # ---- AQS Overview Table ----
    html.append('<h2>Results at a Glance</h2>')
    html.append('<p>Agent Quality Score (AQS) per task. Scale: 0&ndash;100. '
                'Grade: A (90+), B (80+), C (70+), D (60+), F (&lt;60).</p>')
    html.append('<table>')
    html.append(f'<tr>{_th("Task")}')
    for agent in active_agents:
        html.append(_th(AGENT_DISPLAY.get(agent, agent), "c"))
    html.append('</tr>')

    agent_totals: dict[str, list[int]] = {a: [] for a in active_agents}

    for task in TASKS:
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

    # ---- Per-task AQS Category Breakdown ----
    categories = ["health", "quality", "architecture", "testing", "completeness"]
    cat_max = {"health": 40, "quality": 25, "architecture": 15, "testing": 15, "completeness": 5}
    cat_bar_cls = {"health": "bar-health", "quality": "bar-quality",
                   "architecture": "bar-arch", "testing": "bar-testing",
                   "completeness": "bar-complete"}
    cat_short = {"health": "Health", "quality": "Quality", "architecture": "Arch",
                 "testing": "Testing", "completeness": "Complete"}
    bar_max_px = 60  # max bar width in pixels

    html.append('<h2>Category Breakdown by Task</h2>')
    html.append('<p>AQS breaks into 5 categories: Health (40), Quality (25), '
                'Architecture (15), Testing (15), Completeness (5).</p>')

    for task in TASKS:
        html.append(f'<h3>{TASK_DISPLAY.get(task, task)}</h3>')
        html.append(f'<table><tr>{_th("Agent")}{_th("AQS", "c")}')
        for cat in categories:
            html.append(_th(f'{cat_short[cat]} /{cat_max[cat]}', "r"))
        html.append('</tr>')

        for agent in active_agents:
            aqs = aqs_lookup.get((agent, "vanilla", task))
            if not aqs:
                continue
            bd = aqs.get("breakdown", {})
            html.append(f'<tr><td>{AGENT_DISPLAY.get(agent, agent)}</td>')
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

    # ---- Agent Averages Summary ----
    html.append('<h2>Agent Averages</h2>')
    html.append('<p>Average scores across all 5 tasks (vanilla mode).</p>')
    html.append(f'<table><tr>{_th("Agent")}{_th("Avg AQS", "c")}')
    for cat in categories:
        html.append(_th(f'Avg {cat_short[cat]}', "r"))
    html.append('</tr>')

    for agent in active_agents:
        cat_sums: dict[str, list] = {c: [] for c in categories}
        aqs_scores: list[int] = []
        for task in TASKS:
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

        html.append(f'<tr><td>{AGENT_DISPLAY.get(agent, agent)}</td>')
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

    # ---- Agent Signatures ----
    if signatures:
        html.append('<h2>Agent Signatures</h2>')
        html.append(f'<table><tr>{_th("Agent")}{_th("CLI Version")}{_th("Model")}</tr>')
        for agent in active_agents:
            sig = signatures.get(agent, {})
            if sig:
                html.append(f'<tr><td>{AGENT_DISPLAY.get(agent, agent)}</td>'
                            f'<td>{sig.get("cli_version", "N/A")}</td>'
                            f'<td>{sig.get("model", "N/A")}</td></tr>')
        roam_ver = next((s.get("roam_version") for s in signatures.values() if s.get("roam_version")), None)
        html.append('</table>')
        if roam_ver:
            html.append(f'<p>Evaluator: <strong>roam-code {roam_ver}</strong></p>')

    # ---- Per-task Raw Metrics Tables ----
    html.append('<h2>Raw Metrics by Task</h2>')
    html.append('<p>Detailed roam-code metrics for each task and agent.</p>')

    for task in TASKS:
        html.append(f'<h3>{TASK_DISPLAY.get(task, task)}</h3>')
        html.append(f'<table><tr>{_th("Agent")}{_th("Mode")}')
        for _, label, _, _ in SCORE_COLUMNS:
            html.append(_th(label, "r"))
        html.append('</tr>')

        for agent in AGENTS:
            for mode in MODES:
                scores = lookup.get((agent, mode, task))
                if not scores:
                    continue
                html.append(f'<tr><td>{AGENT_DISPLAY.get(agent, agent)}</td><td>{mode}</td>')
                for field, _, fmt, _ in SCORE_COLUMNS:
                    val = scores.get(field)
                    if val is None:
                        html.append(_td("--", "muted"))
                    elif isinstance(val, bool):
                        cls = "badge-pass" if val else "badge-fail"
                        txt = "PASS" if val else "FAIL"
                        html.append(_td(f'<span class="badge {cls}">{txt}</span>', "c"))
                    else:
                        try:
                            formatted = fmt.format(val)
                        except (ValueError, TypeError):
                            formatted = str(val)
                        html.append(_td(formatted, "r"))
                html.append('</tr>')
        html.append('</table>')

    # ---- Mode Impact (only if data exists) ----
    if has_mode_data:
        html.append('<h2>Mode Impact (Health Delta vs Vanilla)</h2>')
        html.append(f'<table><tr>{_th("Agent")}{_th("Mode")}')
        for task in TASKS:
            html.append(_th(TASK_DISPLAY.get(task, task)[:12], "c"))
        html.append(_th("AVG", "c"))
        html.append('</tr>')

        for agent in AGENTS:
            for mode in ["roam-cli", "roam-mcp"]:
                has_any = any(
                    lookup.get((agent, "vanilla", t), {}).get("health") is not None
                    and lookup.get((agent, mode, t), {}).get("health") is not None
                    for t in TASKS
                )
                if not has_any:
                    continue
                html.append(f'<tr><td>{AGENT_DISPLAY.get(agent, agent)}</td><td>{mode}</td>')
                deltas = []
                for task in TASKS:
                    vanilla = lookup.get((agent, "vanilla", task), {}).get("health")
                    enhanced = lookup.get((agent, mode, task), {}).get("health")
                    if vanilla is not None and enhanced is not None:
                        delta = enhanced - vanilla
                        deltas.append(delta)
                        cls = "pos" if delta > 0 else "neg" if delta < 0 else ""
                        sign = "+" if delta > 0 else ""
                        html.append(_td(f'{sign}{delta}', f"c {cls}".strip()))
                    else:
                        html.append(_td("--", "muted"))
                if deltas:
                    avg = sum(deltas) / len(deltas)
                    cls = "pos" if avg > 0 else "neg" if avg < 0 else ""
                    sign = "+" if avg > 0 else ""
                    html.append(_td(f'<strong>{sign}{avg:.1f}</strong>', f"c {cls}".strip()))
                else:
                    html.append(_td("--", "muted"))
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
    lookup = build_lookup(results)
    aqs_lookup = build_aqs_lookup(results)
    signatures = build_signature_lookup(results)

    # Print agent signatures
    if signatures:
        print(f"{'=' * 80}")
        print("  AGENT SIGNATURES")
        print(f"{'=' * 80}")
        print(f"{'Agent':<20} {'CLI Version':<25} {'Model':<30}")
        print("-" * 80)
        for agent in AGENTS:
            sig = signatures.get(agent)
            if sig:
                print(f"{agent:<20} {sig.get('cli_version', 'N/A'):<25} {sig.get('model', 'N/A'):<30}")
        roam_ver = next((s.get("roam_version") for s in signatures.values() if s.get("roam_version")), None)
        if roam_ver:
            print(f"\nEvaluator: roam-code {roam_ver}")
        print()

    # Print per-task tables
    for task in TASKS:
        if any(k[2] == task for k in lookup):
            print_task_table(task, lookup)

    # Agent summaries
    print(f"\n{'=' * 80}")
    print("  AGENT SUMMARIES")
    print(f"{'=' * 80}")
    for agent in AGENTS:
        if any(k[0] == agent for k in lookup):
            print_agent_summary(agent, lookup)

    # Mode impact
    print_mode_comparison(lookup)

    # HTML report
    if args.html:
        generate_html_report(lookup, aqs_lookup, signatures, args.html)

    # Also output to docs/ for GitHub Pages
    if args.docs:
        docs_path = Path(__file__).parent / "docs" / "index.html"
        generate_html_report(lookup, aqs_lookup, signatures, docs_path)


if __name__ == "__main__":
    main()
