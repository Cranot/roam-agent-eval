#!/usr/bin/env bash
#
# generate.sh — Generate agent workspaces for roam-agent-eval
#
# Runs an AI coding agent CLI on task prompts, writing output into workspaces/.
# Reads combo definitions from combos.json. Skips workspaces that already have files.
#
# Usage:
#   ./generate.sh                           # generate all missing workspaces
#   ./generate.sh --combo cc-sonnet4.6      # only this combo
#   ./generate.sh --task react-todo         # only this task
#   ./generate.sh --group algorithm         # only algorithm-group tasks
#   ./generate.sh --force                   # regenerate even if workspace has files
#   ./generate.sh --dry-run                 # show what would run without running it
#   ./generate.sh --parallel 3             # run N agents concurrently (default: 1)
#
set -euo pipefail

# Resolve to Windows-style path for Python compatibility
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Convert /d/... to D:/... for Python on Windows
SCRIPT_DIR_WIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -W 2>/dev/null || pwd)"
WORKSPACES_DIR="$SCRIPT_DIR/workspaces"
PROMPTS_DIR="$SCRIPT_DIR/prompts"
COMBOS_FILE="$SCRIPT_DIR/combos.json"
COMBOS_FILE_WIN="$SCRIPT_DIR_WIN/combos.json"
LOG_DIR="$SCRIPT_DIR/logs"

# Default options
COMBO_FILTER=""
TASK_FILTER=""
GROUP_FILTER=""
FORCE=false
DRY_RUN=false
PARALLEL=1

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --combo)    COMBO_FILTER="$2"; shift 2 ;;
        --task)     TASK_FILTER="$2"; shift 2 ;;
        --group)    GROUP_FILTER="$2"; shift 2 ;;
        --force)    FORCE=true; shift ;;
        --dry-run)  DRY_RUN=true; shift ;;
        --parallel) PARALLEL="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [--combo ID] [--task ID] [--group NAME] [--force] [--dry-run] [--parallel N]"
            exit 0 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

# Task definitions — group mapping
declare -A TASK_GROUP=(
    [react-todo]=standard
    [astro-landing]=standard
    [python-crawler]=standard
    [cpp-calculator]=standard
    [go-loganalyzer]=standard
    [python-etl]=algorithm
    [ts-pathfinder]=algorithm
)

MODES=(vanilla)  # only vanilla for generation; roam-cli/roam-mcp are prompt suffixes

# Ensure prompts are exported
if [[ ! -d "$PROMPTS_DIR" ]] || [[ -z "$(ls "$PROMPTS_DIR"/*.txt 2>/dev/null)" ]]; then
    echo "Exporting prompts..."
    python "$SCRIPT_DIR/run_eval.py" --export-prompts
fi

# Ensure combos.json exists
if [[ ! -f "$COMBOS_FILE" ]]; then
    echo "Error: $COMBOS_FILE not found"
    exit 1
fi

# Read combos from JSON
COMBOS=$(python -c "import json; d=json.load(open(r'$COMBOS_FILE_WIN')); print(' '.join(d.keys()))")

# Logging
mkdir -p "$LOG_DIR"

# Count pending jobs
pending=0
total=0

# Build job list
jobs=()

for combo in $COMBOS; do
    [[ -n "$COMBO_FILTER" && "$combo" != "$COMBO_FILTER" ]] && continue

    # Get invoke command from combos.json
    invoke=$(python -c "import json; d=json.load(open(r'$COMBOS_FILE_WIN')); print(d.get('$combo',{}).get('invoke',''))")
    if [[ -z "$invoke" ]]; then
        echo "SKIP $combo: no invoke command in combos.json"
        continue
    fi

    for task in "${!TASK_GROUP[@]}"; do
        [[ -n "$TASK_FILTER" && "$task" != "$TASK_FILTER" ]] && continue
        [[ -n "$GROUP_FILTER" && "${TASK_GROUP[$task]}" != "$GROUP_FILTER" ]] && continue

        for mode in "${MODES[@]}"; do
            total=$((total + 1))
            ws_dir="$WORKSPACES_DIR/$combo/${task}_${mode}"
            prompt_file="$PROMPTS_DIR/${task}_${mode}.txt"
            log_file="$LOG_DIR/${combo}_${task}_${mode}.log"

            # Skip if workspace already has files (unless --force)
            file_count=$(find "$ws_dir" -maxdepth 1 -type f 2>/dev/null | wc -l)
            if [[ "$FORCE" != "true" && "$file_count" -gt 0 ]]; then
                echo "SKIP $combo / $task / $mode (${file_count} files exist)"
                continue
            fi

            if [[ ! -f "$prompt_file" ]]; then
                echo "SKIP $combo / $task / $mode (no prompt file)"
                continue
            fi

            pending=$((pending + 1))
            jobs+=("$combo|$task|$mode|$ws_dir|$prompt_file|$invoke|$log_file")
        done
    done
done

echo ""
echo "=== Generation Plan ==="
echo "Total: $total | Pending: $pending | Skipped: $((total - pending))"
echo "Parallelism: $PARALLEL"
echo ""

if [[ "$pending" -eq 0 ]]; then
    echo "Nothing to generate."
    exit 0
fi

if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY RUN — would generate:"
    for job in "${jobs[@]}"; do
        IFS='|' read -r combo task mode ws_dir prompt_file invoke log_file <<< "$job"
        echo "  $combo / $task / $mode -> $ws_dir"
        echo "    CMD: cd $ws_dir && env CLAUDECODE= $invoke \"\$(cat $prompt_file)\""
    done
    exit 0
fi

# Run generation jobs
run_job() {
    local combo task mode ws_dir prompt_file invoke log_file
    IFS='|' read -r combo task mode ws_dir prompt_file invoke log_file <<< "$1"

    echo "[START] $combo / $task / $mode"
    mkdir -p "$ws_dir"

    local start_time=$(date +%s)

    # Run the agent CLI (unset CLAUDECODE for nested invocation)
    (
        cd "$ws_dir"
        env CLAUDECODE= $invoke "$(cat "$prompt_file")"
    ) > "$log_file" 2>&1
    local exit_code=$?

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [[ $exit_code -eq 0 ]]; then
        local out_files=$(find "$ws_dir" -maxdepth 2 -type f | wc -l)
        echo "[DONE]  $combo / $task / $mode (${duration}s, ${out_files} files)"
    else
        echo "[FAIL]  $combo / $task / $mode (exit=$exit_code, ${duration}s) — see $log_file"
    fi

    return $exit_code
}

export -f run_job
export COMBOS_FILE WORKSPACES_DIR PROMPTS_DIR LOG_DIR

if [[ "$PARALLEL" -le 1 ]]; then
    # Sequential execution
    success=0
    failed=0
    for job in "${jobs[@]}"; do
        if run_job "$job"; then
            success=$((success + 1))
        else
            failed=$((failed + 1))
        fi
    done
else
    # Parallel execution using background jobs
    success=0
    failed=0
    running=0

    for job in "${jobs[@]}"; do
        if [[ $running -ge $PARALLEL ]]; then
            wait -n 2>/dev/null || true
            running=$((running - 1))
        fi
        run_job "$job" &
        running=$((running + 1))
    done

    # Wait for remaining
    wait
fi

echo ""
echo "=== Generation Complete ==="
echo "Success: $success | Failed: $failed | Total: $pending"
echo "Logs: $LOG_DIR/"
echo ""
echo "Next: python run_eval.py --force  # evaluate and generate report"
