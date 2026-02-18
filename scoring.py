"""
Agent Quality Score (AQS) — Composite scoring system.

Combines roam metrics + structural checks into a single 0-100 score.

Score breakdown (100 points total):
  - Roam Health Score:    35 pts  (0-100 scaled to 0-35)
  - Code Quality:         20 pts  (dead code, complexity, coupling penalties)
  - Architecture:         15 pts  (cycles, tangle ratio, file structure)
  - Algorithms:           10 pts  (anti-pattern detections from roam math)
  - Testing:              15 pts  (test existence, count, coverage proxy)
  - Project Completeness:  5 pts  (README, build config, builds, runs)
"""
from __future__ import annotations


def compute_aqs(result: dict) -> dict:
    """Compute Agent Quality Score from an evaluation result.

    Args:
        result: Full evaluation result dict from evaluate.py

    Returns:
        Dict with overall AQS, category breakdowns, and letter grade.
    """
    scores = result.get("scores", {})
    file_stats = result.get("file_stats", {})
    structure = result.get("structure", {})
    roam = result.get("roam", {})

    breakdown = {}

    # --- 1. Roam Health Score (35 pts) ---
    health = scores.get("health")
    if health is not None:
        breakdown["health"] = round(health * 0.35)  # 0-100 -> 0-35
    else:
        breakdown["health"] = 0

    # --- 2. Code Quality (20 pts) ---
    quality_score = 20.0

    # Dead code penalty: -2 per dead symbol, max -8
    dead = scores.get("dead_symbols")
    if dead is not None and dead > 0:
        quality_score -= min(dead * 2, 8)

    # Complexity penalty: -1 per avg complexity point above 5, max -6
    avg_cx = scores.get("avg_complexity")
    if avg_cx is not None and avg_cx > 5:
        quality_score -= min((avg_cx - 5) * 1, 6)

    # P90 complexity penalty: -1 per point above 15, max -4
    p90_cx = scores.get("p90_complexity")
    if p90_cx is not None and p90_cx > 15:
        quality_score -= min((p90_cx - 15) * 1, 4)

    # High complexity count penalty: -2 per function with high complexity, max -5
    hi_cx = scores.get("high_complexity_count")
    if hi_cx is not None and hi_cx > 0:
        quality_score -= min(hi_cx * 2, 5)

    breakdown["quality"] = max(0, round(quality_score))

    # --- 3. Architecture (15 pts) ---
    arch_score = 15.0

    # Tangle ratio penalty: scales with ratio (0.0 = perfect, 1.0 = terrible)
    tangle = scores.get("tangle_ratio")
    if tangle is not None and tangle > 0:
        arch_score -= min(tangle * 10, 5)

    # Critical issues penalty: -3 per critical issue
    crit = scores.get("critical_issues")
    if crit is not None and crit > 0:
        arch_score -= min(crit * 3, 10)

    # File structure: too few files = not well-structured
    total_files = file_stats.get("total_files", 0)
    if total_files < 5:
        arch_score -= 3

    breakdown["architecture"] = max(0, round(arch_score))

    # --- 4. Algorithms (10 pts) ---
    algo_score = 10.0

    # Penalty based on anti-pattern detections from roam math.
    # High confidence: -3 each, Medium: -2 each, Low: -1 each. Max -10.
    ap_high = scores.get("antipattern_high")
    ap_med = scores.get("antipattern_medium")
    ap_low = scores.get("antipattern_low")
    ap_total = scores.get("antipattern_total")

    if ap_total is not None:
        penalty = 0
        if ap_high:
            penalty += ap_high * 3
        if ap_med:
            penalty += ap_med * 2
        if ap_low:
            penalty += ap_low * 1
        algo_score -= min(penalty, 10)

    breakdown["algorithms"] = max(0, round(algo_score))

    # --- 5. Testing (15 pts) ---
    test_info = structure.get("tests", {})
    test_score = 0.0

    test_file_count = test_info.get("test_file_count", 0)
    tests_found = test_info.get("tests_found", False)

    if tests_found:
        test_score += 5  # tests exist at all

    # Points per test file: 2 pts each, up to 8 pts
    test_score += min(test_file_count * 2, 8)

    # Bonus for having 3+ test files
    if test_file_count >= 3:
        test_score += 2

    breakdown["testing"] = min(15, round(test_score))

    # --- 6. Project Completeness (5 pts) ---
    completeness = 0.0

    if structure.get("readme", False):
        completeness += 2

    build_info = structure.get("build", {})
    if build_info.get("has_build_config", False):
        completeness += 2

    # Check if roam init succeeded (proxy for "project is valid")
    init_info = roam.get("init", {})
    if init_info.get("success", False):
        completeness += 1

    breakdown["completeness"] = round(completeness)

    # --- Total ---
    total = sum(breakdown.values())
    total = min(100, max(0, total))

    # Letter grade
    if total >= 90:
        grade = "A"
    elif total >= 80:
        grade = "B"
    elif total >= 70:
        grade = "C"
    elif total >= 60:
        grade = "D"
    else:
        grade = "F"

    return {
        "aqs": total,
        "grade": grade,
        "breakdown": breakdown,
        "max_points": {
            "health": 35,
            "quality": 20,
            "architecture": 15,
            "algorithms": 10,
            "testing": 15,
            "completeness": 5,
        },
    }


def format_aqs_report(aqs: dict) -> str:
    """Format AQS result as a readable string."""
    lines = []
    lines.append(f"Agent Quality Score: {aqs['aqs']}/100  (Grade: {aqs['grade']})")
    lines.append("")
    bd = aqs["breakdown"]
    mx = aqs["max_points"]
    for cat in ["health", "quality", "architecture", "algorithms", "testing", "completeness"]:
        if cat not in bd:
            continue
        bar_len = 20
        filled = round(bd[cat] / mx[cat] * bar_len) if mx[cat] > 0 else 0
        bar = "#" * filled + "." * (bar_len - filled)
        lines.append(f"  {cat:<15} [{bar}] {bd[cat]:>2}/{mx[cat]}")
    return "\n".join(lines)
