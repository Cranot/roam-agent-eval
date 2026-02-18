#!/usr/bin/env python3
"""
Generate agent workspaces for roam-agent-eval.

Runs AI coding agent CLIs on task prompts, writing output into workspaces/.
Reads combo definitions from combos.json. Skips workspaces that already have files.

Usage:
    python generate.py                           # generate all missing workspaces
    python generate.py --combo cc-sonnet4.6      # only this combo
    python generate.py --task react-todo         # only this task
    python generate.py --group algorithm         # only algorithm-group tasks
    python generate.py --force                   # regenerate even if workspace has files
    python generate.py --dry-run                 # show what would run
    python generate.py --parallel 3              # run N agents concurrently (default: 1)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from prompts import TASKS


BASE_DIR = Path(__file__).parent
WORKSPACES_DIR = BASE_DIR / "workspaces"
PROMPTS_DIR = BASE_DIR / "prompts"
COMBOS_FILE = BASE_DIR / "combos.json"
LOG_DIR = BASE_DIR / "logs"

MODES = ["vanilla"]  # only vanilla for generation

# Task group mapping
TASK_GROUPS = {}
for tid, tdef in TASKS.items():
    TASK_GROUPS[tid] = tdef.get("group", "standard")


def load_combos() -> dict:
    """Load combo definitions from combos.json."""
    if COMBOS_FILE.is_file():
        return json.loads(COMBOS_FILE.read_text(encoding="utf-8"))
    return {}


def count_workspace_files(ws_dir: Path) -> int:
    """Count files in workspace (excluding .git)."""
    if not ws_dir.is_dir():
        return 0
    count = 0
    for f in ws_dir.iterdir():
        if f.name != ".git" and f.is_file():
            count += 1
    return count


def build_job_list(
    combos_meta: dict,
    combo_filter: str | None = None,
    task_filter: str | None = None,
    group_filter: str | None = None,
    force: bool = False,
) -> list[dict]:
    """Build list of generation jobs to run."""
    jobs = []

    for combo_id, meta in combos_meta.items():
        if combo_filter and combo_id != combo_filter:
            continue

        invoke = meta.get("invoke", "")
        if not invoke:
            print(f"SKIP {combo_id}: no invoke command in combos.json")
            continue

        for task_id in TASKS:
            if task_filter and task_id != task_filter:
                continue

            group = TASK_GROUPS.get(task_id, "standard")
            if group_filter and group != group_filter:
                continue

            for mode in MODES:
                ws_dir = WORKSPACES_DIR / combo_id / f"{task_id}_{mode}"
                prompt_file = PROMPTS_DIR / f"{task_id}_{mode}.txt"

                if not prompt_file.is_file():
                    print(f"SKIP {combo_id} / {task_id} / {mode}: no prompt file")
                    continue

                file_count = count_workspace_files(ws_dir)
                if not force and file_count > 0:
                    print(f"SKIP {combo_id} / {task_id} / {mode} ({file_count} files exist)")
                    continue

                jobs.append({
                    "combo": combo_id,
                    "task": task_id,
                    "mode": mode,
                    "group": group,
                    "ws_dir": ws_dir,
                    "prompt_file": prompt_file,
                    "invoke": invoke,
                })

    return jobs


def run_job(job: dict) -> dict:
    """Execute a single generation job. Returns result dict."""
    import shutil

    combo = job["combo"]
    task = job["task"]
    mode = job["mode"]
    ws_dir = job["ws_dir"]
    prompt_file = job["prompt_file"]
    invoke = job["invoke"]

    log_file = LOG_DIR / f"{combo}_{task}_{mode}.log"

    print(f"[START] {combo} / {task} / {mode}")

    # Ensure workspace dir exists
    ws_dir.mkdir(parents=True, exist_ok=True)

    # Read prompt
    prompt = prompt_file.read_text(encoding="utf-8")

    # Unset CLAUDECODE to allow nested invocation
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    # Build command parts
    cmd_parts = invoke.split() + [prompt]

    # On Windows, resolve .cmd/.bat executables via shutil.which()
    cli_exe = shutil.which(cmd_parts[0])
    if cli_exe:
        cmd_parts[0] = cli_exe

    start_time = time.time()

    try:
        # Force UTF-8 encoding to handle non-ASCII output on Windows
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            cmd_parts,
            cwd=str(ws_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=600,  # 10 minute timeout per task
            env=env,
        )
        stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        duration = time.time() - start_time

        # Write log
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"=== {combo} / {task} / {mode} ===\n")
            f.write(f"Command: {invoke} <prompt>\n")
            f.write(f"Duration: {duration:.1f}s\n")
            f.write(f"Exit code: {result.returncode}\n\n")
            f.write("=== STDOUT ===\n")
            f.write(stdout)
            f.write("\n=== STDERR ===\n")
            f.write(stderr)

        # Count output files
        out_files = count_workspace_files(ws_dir)

        if result.returncode == 0:
            print(f"[DONE]  {combo} / {task} / {mode} ({duration:.0f}s, {out_files} files)")
            return {"status": "success", "combo": combo, "task": task, "duration": duration, "files": out_files}
        else:
            print(f"[FAIL]  {combo} / {task} / {mode} (exit={result.returncode}, {duration:.0f}s)")
            return {"status": "failed", "combo": combo, "task": task, "exit_code": result.returncode}

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"[TIMEOUT] {combo} / {task} / {mode} ({duration:.0f}s)")
        return {"status": "timeout", "combo": combo, "task": task}
    except Exception as e:
        print(f"[ERROR] {combo} / {task} / {mode}: {e}")
        return {"status": "error", "combo": combo, "task": task, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Generate agent workspaces")
    parser.add_argument("--combo", type=str, help="Only this combo ID")
    parser.add_argument("--task", type=str, help="Only this task ID")
    parser.add_argument("--group", type=str, help="Only this task group (standard, algorithm)")
    parser.add_argument("--force", action="store_true", help="Regenerate even if files exist")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    parser.add_argument("--parallel", type=int, default=1, help="Max concurrent agents")
    args = parser.parse_args()

    # Ensure prompts are exported
    if not PROMPTS_DIR.is_dir() or not list(PROMPTS_DIR.glob("*.txt")):
        print("Exporting prompts...")
        subprocess.run([sys.executable, str(BASE_DIR / "run_eval.py"), "--export-prompts"])

    combos_meta = load_combos()
    if not combos_meta:
        print("Error: combos.json not found or empty")
        sys.exit(1)

    jobs = build_job_list(
        combos_meta,
        combo_filter=args.combo,
        task_filter=args.task,
        group_filter=args.group,
        force=args.force,
    )

    total_combos = len(combos_meta) if not args.combo else 1
    total_tasks = len(TASKS) if not args.task else 1
    print(f"\n=== Generation Plan ===")
    print(f"Pending: {len(jobs)} | Parallel: {args.parallel}")
    print()

    if not jobs:
        print("Nothing to generate.")
        return

    if args.dry_run:
        print("DRY RUN -- would generate:")
        for job in jobs:
            print(f"  {job['combo']} / {job['task']} / {job['mode']}")
            print(f"    DIR: {job['ws_dir']}")
            print(f"    CMD: {job['invoke']} <prompt>")
        return

    # Execute jobs
    results = []
    if args.parallel <= 1:
        for job in jobs:
            results.append(run_job(job))
    else:
        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            futures = {executor.submit(run_job, job): job for job in jobs}
            for future in as_completed(futures):
                results.append(future.result())

    # Summary
    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] != "success")
    print(f"\n=== Generation Complete ===")
    print(f"Success: {success} | Failed: {failed} | Total: {len(results)}")
    print(f"Logs: {LOG_DIR}/")
    print(f"\nNext: python run_eval.py --force  # evaluate and generate report")


if __name__ == "__main__":
    main()
