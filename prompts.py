"""
Agent Evaluation Prompts — "Complete" group.

5 full-project prompts across 5 languages/frameworks.
Each prompt has 3 modes: vanilla, roam-cli, roam-mcp.
"""
from __future__ import annotations

TASKS = {
    "react-todo": {
        "id": "react-todo",
        "name": "React TODO App",
        "language": "javascript",
        "framework": "react",
        "prompt": """\
Create a complete TODO application using React, JavaScript, and Vite.

Requirements:
- Add, edit, delete, and mark tasks as complete
- Task categories: work, personal, shopping, health
- Priority levels: high, medium, low with visual indicators
- Due dates with overdue highlighting
- Filter by category, priority, completion status
- Sort by due date, priority, or creation date
- Persist all data to localStorage
- Responsive design that works on mobile and desktop
- Keyboard shortcuts: Enter to add, Escape to cancel edit
- Task count summary showing total, completed, and pending

Technical requirements:
- Use Vite as the build tool
- No external UI component libraries — write your own components
- CSS modules or styled-components for styling
- Clean component hierarchy with proper state management
- Include unit tests using Vitest
- Include a README with setup instructions
""",
    },
    "astro-landing": {
        "id": "astro-landing",
        "name": "Astro SaaS Landing Page",
        "language": "javascript",
        "framework": "astro",
        "prompt": """\
Build a complete SaaS landing page for a fictional project management tool called "FlowBoard" using Astro.

Requirements:
- Hero section: headline, subheadline, email signup CTA, hero illustration/graphic
- Features section: 6 features with icons and descriptions in a grid
- How It Works section: 3-step process with numbered steps
- Pricing section: 3 tiers (Free, Pro $12/mo, Enterprise $49/mo) with feature comparison
- Testimonials section: 3 customer testimonials with names and roles
- FAQ section: 6 questions with accordion expand/collapse
- Contact form: name, email, message fields with client-side validation
- Navigation: sticky header with smooth scroll to sections, mobile hamburger menu
- Footer: links, social icons, copyright

Technical requirements:
- Astro framework with static site generation
- Responsive design (mobile-first)
- CSS written from scratch — no Tailwind or UI libraries
- Semantic HTML with accessibility (ARIA labels, keyboard navigation)
- Optimized images and lazy loading
- Include tests where applicable
- Include a README with setup instructions
""",
    },
    "python-crawler": {
        "id": "python-crawler",
        "name": "Python Web Crawler",
        "language": "python",
        "framework": "none",
        "prompt": """\
Build a web crawler in Python as a proper package.

Requirements:
- CLI that accepts: starting URL, max depth (default 2), max pages (default 50), output format
- Respect robots.txt rules
- Configurable crawl delay (default 1 second between requests)
- Extract from each page: title, meta description, all headings (h1-h6), internal/external links, images with alt text
- Detect and report broken links (4xx, 5xx responses)
- Stay within the same domain by default (flag to allow external)
- Handle edge cases: redirects, timeouts, circular links, malformed URLs
- Use async I/O (aiohttp + asyncio) for concurrent crawling with configurable concurrency limit
- Output formats: JSON (structured report), CSV (flat table), HTML (visual report with summary stats)
- Summary statistics: total pages crawled, broken links found, average response time, most linked pages

Technical requirements:
- Proper Python package with pyproject.toml
- CLI using click or argparse
- Clean module separation: crawler engine, parser, reporter, CLI
- Comprehensive unit tests using pytest (mock HTTP responses)
- Type hints throughout
- Include a README with setup and usage instructions
""",
    },
    "cpp-calculator": {
        "id": "cpp-calculator",
        "name": "C++ Expression Calculator",
        "language": "cpp",
        "framework": "none",
        "prompt": """\
Build a mathematical expression parser and interactive calculator in C++.

Requirements:
- Parse and evaluate expressions from string input
- Operators: +, -, *, /, % (modulo), ^ (power) with correct precedence
- Parentheses for grouping, nested to arbitrary depth
- Unary minus: -5, -(3+2)
- Built-in functions: sin, cos, tan, sqrt, log, log10, abs, ceil, floor, min, max
- Variable assignment: x = 3.14, then use x in later expressions
- Built-in constants: pi, e
- Expression history: recall previous results with $1, $2, etc.
- Interactive REPL mode with prompt and help command
- File evaluation mode: read expressions from a file, output results
- Clear error messages: "Unexpected token '*' at position 5", "Unknown function 'foo'"
- Support both integer and floating-point arithmetic

Technical requirements:
- CMake build system (minimum CMake 3.16)
- Recursive descent parser or Pratt parser — no parser generators
- Clean separation: lexer (tokenizer), parser (AST), evaluator, REPL
- Header/source file separation
- Unit tests (using Catch2, GoogleTest, or doctest)
- Include a README with build and usage instructions
""",
    },
    "go-loganalyzer": {
        "id": "go-loganalyzer",
        "name": "Go Concurrent Log Analyzer",
        "language": "go",
        "framework": "none",
        "prompt": """\
Build a concurrent log file analyzer CLI tool in Go.

Requirements:
- Accept log files or directories as input (recursive directory scanning)
- Parse common formats: Apache Combined, Nginx, JSON Lines (auto-detect format)
- Concurrent processing: use goroutines + worker pool to analyze multiple files in parallel
- Statistics per file and aggregate:
  - Total requests, unique IPs, unique endpoints
  - Status code distribution (2xx, 3xx, 4xx, 5xx counts and percentages)
  - Top 10 IPs by request count
  - Top 10 endpoints by request count
  - Top 10 slowest requests (if response time available)
  - Requests per hour histogram
  - Error rate over time (detect spikes)
- Filters: date range, status code range, endpoint regex, IP whitelist/blacklist
- Output formats: text table (default), JSON, CSV
- Progress bar for large file processing
- Graceful handling of malformed lines (count and report skipped lines)

Technical requirements:
- Go modules (go.mod)
- Use standard library where possible, minimal external dependencies
- Clean package structure: cmd/, internal/parser/, internal/analyzer/, internal/output/
- Unit tests with table-driven test patterns
- Benchmarks for the parser
- Include a README with build and usage instructions
""",
    },
}

# --- Algorithm-focused tasks (group: algorithm) ---
# Designed to surface algorithmic anti-patterns: O(n^2) loops, N+1 queries,
# redundant computation, suboptimal data structures.

TASKS["python-etl"] = {
    "id": "python-etl",
    "name": "Python ETL Data Pipeline",
    "language": "python",
    "framework": "none",
    "group": "algorithm",
    "prompt": """\
Build a data pipeline (ETL) tool in Python that processes CSV datasets, joins them,
detects anomalies, and produces summary reports.

Requirements:
- CLI that accepts a directory of CSV files as input
- Auto-detect CSV schema (column names, types) from headers + sampling
- Pipeline stages:
  1. EXTRACT: Read all CSVs, validate rows, count malformed/skipped rows
  2. TRANSFORM:
     - Join datasets: match rows across files on shared key columns (like SQL JOINs)
     - Deduplication: detect and remove duplicate rows (exact + fuzzy matching on configurable columns)
     - Normalization: standardize date formats, trim whitespace, case-normalize text fields
     - Computed columns: support simple expressions (sum, difference, ratio of two columns)
     - Anomaly detection: flag rows where numeric values are >3 standard deviations from column mean
  3. LOAD: Write cleaned data to output CSV, JSON, or SQLite database
- Summary report:
  - Row counts per stage (extracted, transformed, loaded, dropped)
  - Per-column statistics: min, max, mean, median, stddev, null count, unique count
  - Top 10 most frequent values per categorical column
  - Anomaly list with row number, column, value, and z-score
  - Join statistics: matched rows, unmatched left, unmatched right
- Performance:
  - Process files up to 100MB without loading everything into memory at once
  - Use generators/iterators for streaming where possible
  - Report processing time per stage

Technical requirements:
- Proper Python package with pyproject.toml
- CLI using click or argparse
- Clean module separation: reader, transformer, joiner, anomaly_detector, writer, reporter, cli
- Type hints throughout
- Comprehensive unit tests using pytest (test each transform independently)
- Include sample CSV test fixtures (at least 3 related CSVs with 50+ rows each)
- Include a README with setup and usage instructions
""",
}

TASKS["ts-pathfinder"] = {
    "id": "ts-pathfinder",
    "name": "TypeScript Grid Pathfinder",
    "language": "typescript",
    "framework": "none",
    "group": "algorithm",
    "prompt": """\
Build a grid-based pathfinding library and visualizer CLI in TypeScript.

Requirements:
- Grid representation:
  - 2D grid with configurable dimensions (up to 1000x1000)
  - Cell types: empty (passable), wall (impassable), weighted (cost 1-9), start, goal
  - Load grids from text files (. = empty, # = wall, 1-9 = weighted, S = start, G = goal)
  - Generate random mazes using recursive backtracking or Prim's algorithm
- Pathfinding algorithms (implement ALL of these):
  - BFS (Breadth-First Search) — unweighted shortest path
  - Dijkstra — weighted shortest path
  - A* with Manhattan and Euclidean heuristics — heuristic-guided search
  - Bidirectional BFS — search from both ends
  - Jump Point Search (JPS) — optimized A* for uniform grids
- Comparison mode:
  - Run all algorithms on the same grid
  - Report for each: path length, path cost, nodes explored, time taken (ms)
  - Rank algorithms by efficiency (nodes explored) and speed
- Batch benchmarking:
  - Generate N random grids of given dimensions
  - Run all algorithms on each, compute average statistics
  - Output summary table comparing algorithms
- CLI interface:
  - `pathfind solve <grid_file>` — solve and display path
  - `pathfind compare <grid_file>` — compare all algorithms
  - `pathfind bench --size 100 --count 50` — benchmark on random grids
  - `pathfind generate --size 50 --density 0.3` — generate random grid
- Output formats: text (ASCII grid with path marked), JSON (full stats)

Technical requirements:
- TypeScript with strict mode
- Node.js compatible (no browser dependencies)
- Build with tsconfig.json (target ES2020+)
- Clean module separation: grid, algorithms/, heuristics, maze_generator, cli, benchmark
- Priority queue implementation (binary heap) — do NOT use array.sort() for the open set
- Unit tests using Vitest or Jest
- Include benchmark results in README
- Include a README with build and usage instructions
""",
}

# Suffix appended for roam-cli mode
ROAM_CLI_SUFFIX = """

--- CODE QUALITY VALIDATION ---
After completing the project, validate and improve your code quality using roam-code:

1. Run `roam init` to index the codebase
2. Run `roam health` — aim for a score above 80
3. Run `roam dead` — remove any dead/unused code found
4. Run `roam complexity` — refactor any functions with cognitive complexity > 15
5. Run `roam cycles` — eliminate any circular dependencies
6. Run `roam gate` — ensure all quality gates pass
7. Run `roam coupling` — reduce high coupling where possible

Iterate until roam reports clean results. Do not stop until health score is above 80.
"""

# Suffix appended for roam-mcp mode
ROAM_MCP_SUFFIX = """

--- CONTINUOUS CODE QUALITY ---
You have access to roam-code tools (MCP) for continuous code quality validation.
Use them throughout development, not just at the end:

- After creating file structure: check with roam health
- After implementing core logic: check complexity and coupling
- After adding all features: check for dead code and cycles
- Before finalizing: run full health check, aim for score above 80

Use roam tools proactively as you build. Fix issues as they arise rather than
accumulating technical debt. Do not finalize until health score is above 80.
"""


def get_prompt(task_id: str, mode: str = "vanilla") -> str:
    """Get the full prompt for a task + mode combination.

    Args:
        task_id: One of the TASKS keys
        mode: "vanilla", "roam-cli", or "roam-mcp"

    Returns:
        The complete prompt string
    """
    task = TASKS[task_id]
    prompt = task["prompt"]

    if mode == "roam-cli":
        prompt += ROAM_CLI_SUFFIX
    elif mode == "roam-mcp":
        prompt += ROAM_MCP_SUFFIX

    return prompt


def get_all_combinations() -> list[dict]:
    """Return all (task, mode) combinations for the benchmark."""
    modes = ["vanilla", "roam-cli", "roam-mcp"]
    combos = []
    for task_id, task in TASKS.items():
        for mode in modes:
            combos.append({
                "task_id": task_id,
                "task_name": task["name"],
                "language": task["language"],
                "mode": mode,
                "workspace_dir": f"{task_id}_{mode}",
            })
    return combos
