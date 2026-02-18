#!/usr/bin/env python3
"""
Run evaluation for all completed workspaces and generate comparison report.

Auto-discovers combos and tasks from the workspaces/ directory.
Reads combo metadata (cli_cmd, model) from combos.json.

Usage:
    python run_eval.py                    # evaluate all workspaces, generate report
    python run_eval.py --list             # list discovered workspaces and their status
    python run_eval.py --force            # re-evaluate even if results exist
    python run_eval.py --export-prompts   # export all prompts to prompts/ directory
    python run_eval.py --combo cc-sonnet4.6  # evaluate only one combo
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from prompts import TASKS, get_prompt, get_all_combinations


MODES = ["vanilla", "roam-cli", "roam-mcp"]

# Task groups for tagging results
TASK_GROUPS = {
    "react-todo": "standard",
    "astro-landing": "standard",
    "python-crawler": "standard",
    "cpp-calculator": "standard",
    "go-loganalyzer": "standard",
    "python-etl": "algorithm",
    "ts-pathfinder": "algorithm",
}

BASE_DIR = Path(__file__).parent
WORKSPACES_DIR = BASE_DIR / "workspaces"
RESULTS_DIR = BASE_DIR / "results"
PROMPTS_DIR = BASE_DIR / "prompts"
COMBOS_FILE = BASE_DIR / "combos.json"


def load_combos() -> dict:
    """Load combo definitions from combos.json."""
    if COMBOS_FILE.is_file():
        return json.loads(COMBOS_FILE.read_text(encoding="utf-8"))
    return {}


def discover_workspaces() -> list[dict]:
    """Auto-discover all workspaces from the filesystem.

    Scans workspaces/<combo_id>/<task_id>_<mode>/ directories.
    Returns list of {combo, task, mode, path} dicts.
    """
    found = []
    if not WORKSPACES_DIR.is_dir():
        return found

    for combo_dir in sorted(WORKSPACES_DIR.iterdir()):
        if not combo_dir.is_dir() or combo_dir.name.startswith("."):
            continue
        combo_id = combo_dir.name

        for ws_dir in sorted(combo_dir.iterdir()):
            if not ws_dir.is_dir() or ws_dir.name.startswith("."):
                continue
            # Parse <task_id>_<mode> directory name
            name = ws_dir.name
            # Try known modes first (longest match)
            task_id = None
            mode = None
            for m in sorted(MODES, key=len, reverse=True):
                suffix = f"_{m}"
                if name.endswith(suffix):
                    task_id = name[:-len(suffix)]
                    mode = m
                    break
            if not task_id:
                # Assume vanilla if no mode suffix
                task_id = name
                mode = "vanilla"

            found.append({
                "combo": combo_id,
                "task": task_id,
                "mode": mode,
                "path": ws_dir,
                "group": TASK_GROUPS.get(task_id, "standard"),
            })

    return found


def result_path(combo: str, task_id: str, mode: str) -> Path:
    return RESULTS_DIR / f"{combo}_{task_id}_{mode}.json"


def list_status():
    """List all discovered workspaces and their evaluation status."""
    combos_meta = load_combos()
    workspaces = discover_workspaces()

    if not workspaces:
        print("No workspaces found. Create directories under workspaces/<combo>/<task>_<mode>/")
        return

    print(f"{'Combo':<20} {'Task':<18} {'Mode':<10} {'Group':<10} {'Evaluated':<10} {'Combo Info'}")
    print("-" * 95)

    done = 0
    for ws in workspaces:
        rs = result_path(ws["combo"], ws["task"], ws["mode"])
        rs_status = "YES" if rs.is_file() else "no"
        if rs.is_file():
            done += 1

        meta = combos_meta.get(ws["combo"], {})
        info = f"{meta.get('cli', '?')} / {meta.get('model', '?')}" if meta else "(not in combos.json)"

        print(f"{ws['combo']:<20} {ws['task']:<18} {ws['mode']:<10} "
              f"{ws['group']:<10} {rs_status:<10} {info}")

    print(f"\nTotal workspaces: {len(workspaces)} | Evaluated: {done}")

    # Show combos from combos.json that have no workspaces
    ws_combos = {w["combo"] for w in workspaces}
    missing = [c for c in combos_meta if c not in ws_combos]
    if missing:
        print(f"\nCombos in combos.json without workspaces: {', '.join(missing)}")


def export_prompts():
    """Export all prompts to text files."""
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    for task_id in TASKS:
        for mode in MODES:
            prompt = get_prompt(task_id, mode)
            filename = f"{task_id}_{mode}.txt"
            (PROMPTS_DIR / filename).write_text(prompt, encoding="utf-8")

    # Master file with all prompts
    master = []
    for task_id, task in TASKS.items():
        master.append(f"{'=' * 80}")
        master.append(f"TASK: {task['name']} ({task_id})")
        master.append(f"Language: {task['language']}")
        master.append(f"{'=' * 80}\n")
        for mode in MODES:
            master.append(f"--- MODE: {mode} ---\n")
            master.append(get_prompt(task_id, mode))
            master.append("")

    (PROMPTS_DIR / "_all_prompts.txt").write_text("\n".join(master), encoding="utf-8")

    count = len(TASKS) * len(MODES)
    print(f"Exported {count} prompts to {PROMPTS_DIR}/")
    print(f"Master file: {PROMPTS_DIR / '_all_prompts.txt'}")


def evaluate_all(force: bool = False, combo_filter: str | None = None):
    """Evaluate all discovered workspaces."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    combos_meta = load_combos()
    workspaces = discover_workspaces()

    if combo_filter:
        workspaces = [w for w in workspaces if w["combo"] == combo_filter]

    if not workspaces:
        print("No workspaces found to evaluate.")
        return

    evaluated = 0
    skipped = 0

    for ws in workspaces:
        rs = result_path(ws["combo"], ws["task"], ws["mode"])

        if rs.is_file() and not force:
            skipped += 1
            continue

        print(f"\n{'=' * 60}")
        print(f"Evaluating: {ws['combo']} / {ws['task']} / {ws['mode']}")
        print(f"{'=' * 60}")

        # Build evaluate.py args
        cmd = [
            sys.executable, str(BASE_DIR / "evaluate.py"),
            str(ws["path"]),
            "--agent", ws["combo"],
            "--mode", ws["mode"],
            "--task", ws["task"],
            "--group", ws["group"],
            "--output", str(rs),
        ]

        # Pass cli-cmd and model from combos.json if available
        meta = combos_meta.get(ws["combo"], {})
        if meta.get("cli"):
            cmd.extend(["--cli-cmd", meta["cli"]])
        if meta.get("model"):
            cmd.extend(["--model", meta["model"]])

        try:
            result = subprocess.run(cmd, timeout=600)
            if result.returncode == 0:
                evaluated += 1
            else:
                print(f"  FAILED (exit code {result.returncode})")
        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT")

    print(f"\nDone. Evaluated: {evaluated}, Skipped (already done): {skipped}")

    # Generate report
    if any(RESULTS_DIR.glob("*.json")):
        print("\nGenerating comparison report...")
        subprocess.run([
            sys.executable, str(BASE_DIR / "compare.py"),
            str(RESULTS_DIR),
            "--html", str(RESULTS_DIR / "report.html"),
        ])


def main():
    parser = argparse.ArgumentParser(description="Run agent evaluation benchmark")
    parser.add_argument("--list", action="store_true", help="List discovered workspaces")
    parser.add_argument("--export-prompts", action="store_true", help="Export prompts to files")
    parser.add_argument("--force", action="store_true", help="Re-evaluate even if results exist")
    parser.add_argument("--combo", type=str, help="Evaluate only this combo ID")
    args = parser.parse_args()

    if args.list:
        list_status()
    elif args.export_prompts:
        export_prompts()
    else:
        evaluate_all(force=args.force, combo_filter=args.combo)


if __name__ == "__main__":
    main()
