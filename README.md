# ContextRefactor

**Semantic, technology-aware codebase refactoring to fit inside a single LLM context window.**

ContextRefactor analyses your project's token footprint using `token_report.py`, detects code smells and structural issues, and generates a step-by-step refactoring plan to reduce the codebase's effective size.

---

## Architecture

```
ContextRector/
├── context_refactor/        # Core domain logic
│   ├── models.py            # Typed dataclasses (immutable domain models)
│   ├── analyzer.py          # Wrapper around token_report.py
│   ├── context_budget.py    # Budget computation (fits / overflow)
│   ├── markdown_refactor.py # Markdown topic-splitting recommendations
│   ├── code_refactor.py     # AST + regex code-smell detection
│   ├── refactor_engine.py   # Orchestrator routing files → analysers
│   └── refactor_planner.py  # Groups recommendations into ordered steps
├── mcp_server/              # Model Context Protocol server
│   ├── server.py            # Stdio MCP transport (+ fallback JSON-RPC)
│   └── tools.py             # Four MCP tools bridging to core logic
├── cli/                     # Typer CLI
│   └── main.py              # Commands: analyze, budget, candidates, plan, serve
├── token_report.py          # External token analysis script (source of truth)
├── pyproject.toml
└── README.md
```

## Installation

```bash
# Create a virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Install in editable mode (from repository root)
pip install -e ".[dev,mcp]"
```

## CLI Usage

### Full analysis

```bash
context-refactor analyze /path/to/project
```

### Check context budget only

```bash
context-refactor budget /path/to/project --context-size 200000 --safety-margin 0.75
```

### Detect refactoring candidates

```bash
context-refactor candidates /path/to/project --estimator heuristic --top 30
```

### Generate refactoring plan

```bash
context-refactor plan /path/to/project --context-size 128000
```

### Start MCP server

```bash
context-refactor serve
```

### JSON output

Every command supports `--json` for machine-readable output:

```bash
context-refactor analyze /path/to/project --json > report.json
```

### Noise reduction profiles

The CLI and MCP tools support analysis profiles plus repo-local configuration so
generated artifacts and oversized planning docs do not dominate normal runs.

```bash
context-refactor analyze /path/to/project --profile default
context-refactor analyze /path/to/project --profile source-only
context-refactor analyze /path/to/project --config /path/to/.context-refactor.json
```

Available profiles:

| Profile | Behavior |
|---|---|
| `default` | Excludes common generated artifacts and keeps source + markdown |
| `full` | Includes everything the scanner can see |
| `source-only` | Restricts results to `source_code` files |
| `docs` | Restricts results to markdown files |

Repo-local config example:

```json
{
  "analysis": {
    "analysis_profile": "default",
    "exclude_dirs": ["coverage", "lcov-report", "reports", "token-report"],
    "exclude_globs": ["docs/planning", "docs/planning/*"],
    "exclude_files": ["backend/lint.result.txt", "*.map"],
    "include_categories": ["source_code"],
    "exclude_categories": ["other"]
  }
}
```

---

## MCP Tools

The server exposes four tools via the Model Context Protocol:

| Tool | Description |
|---|---|
| `context_refactor.analyze_project` | Full analysis: tokens, budget, recommendations, plan |
| `context_refactor.context_budget` | Check if the project fits inside an LLM context window |
| `context_refactor.detect_refactor_candidates` | Detect code smells and refactoring candidates |
| `context_refactor.generate_refactor_plan` | Step-by-step plan to fit the context window |

All analysis tools also accept optional scope parameters:

- `analysis_profile`
- `config_path`
- `exclude_dirs`
- `exclude_globs`
- `exclude_files`
- `include_categories`
- `exclude_categories`

### MCP Client Configuration (VS Code / Claude Desktop)

Add the following to your MCP client configuration (e.g., in VS Code settings or Claude Desktop config):

```json
{
  "mcpServers": {
    "context-refactor": {
      "command": "python3",
      "args": ["-m", "mcp_server.server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

The `${workspaceFolder}` macro will be replaced with your project's root directory. If you're running from a different environment, ensure the Python path resolves correctly and the `mcp` package is installed in that environment's virtual environment.

---

## How It Works

### 1. Token Analysis

The tool delegates token counting entirely to `token_report.py`. It runs the script as a subprocess, parses the JSON output, and classifies each file into:

| Category | Treatment |
|---|---|
| **Source code** (`.py`, `.ts`, `.js`, `.java`, `.go`, …) | AST / regex analysis → code smell detection |
| **Markdown** (`.md`, `.mdx`) | Heading-based topic splitting |
| **Configuration** (`.json`, `.yaml`, `.env`, …) | Included in token count, never modified |
| **Binary** (images, compiled files) | Ignored entirely |

### 2. Code Smell Detection

For **Python** files, the tool uses full AST parsing. For other languages, it uses regex heuristics. Detected smells:

| Smell | Threshold | Technique |
|---|---|---|
| God File | ≥ 600 lines or ≥ 4000 tokens | Extract Module |
| Long Method | ≥ 60 lines | Extract Method |
| Large Class | ≥ 300 lines or ≥ 15 methods | Extract Class |
| Long Parameter List | ≥ 5 parameters | Extract Variable / Options Object |
| Deep Nesting | ≥ 4 levels | Decompose Conditional |

Refactoring techniques are drawn from [refactoring.guru/refactoring/catalog](https://refactoring.guru/refactoring/catalog).

### 3. Markdown Splitting

Large Markdown files with ≥ 3 top-level headings and ≥ 800 tokens are recommended for topic-based splitting. The original file becomes an index linking to the extracted topic files.

### 4. Context Budget

```
context_budget = llm_context_size × safety_margin
overflow_tokens = max(0, total_tokens - context_budget)
overflow_ratio  = overflow_tokens / context_budget
```

### 5. Refactoring Plan

Recommendations are grouped into ordered steps:

1. **Split large Markdown** documentation into topic modules
2. **Extract modules** from oversized God Files
3. **Extract Classes** from large monolithic classes
4. **Extract Methods** from long functions
5. **Move logic** into shared utilities
6. **Flatten** deeply nested conditionals
7. **Simplify** parameter lists and temporaries

---

## Example Output

```json
{
  "project_summary": {
    "files": 320,
    "total_tokens": 182000,
    "context_budget": 102400,
    "fits_context": false
  },
  "refactor_plan": {
    "steps": [
      {
        "step_number": 1,
        "title": "Split large Markdown documentation into topic modules",
        "techniques": ["Split Document"],
        "affected_files": ["docs/README.md", "AGENTS.md"],
        "estimated_token_reduction": 1200
      },
      {
        "step_number": 2,
        "title": "Extract modules from oversized God Files",
        "techniques": ["Extract Module"],
        "affected_files": ["backend/src/database/database.service.ts"],
        "estimated_token_reduction": 8500
      }
    ],
    "total_estimated_token_reduction": 24500,
    "projected_tokens_after": 157500,
    "fits_context_after": false
  }
}
```

---

## Design Principles

- **Clean Architecture**: Core logic has zero I/O dependencies; the MCP server and CLI are thin adapters.
- **SOLID**: Each module has a single responsibility; the refactor engine is open for extension via new analysers.
- **Immutable models**: All domain objects are frozen dataclasses.
- **Dependency Injection**: The analyser, engine, and planner are composed via function arguments, not globals.
- **No token reimplementation**: `token_report.py` is the single source of truth for token counting.

## Requirements

- Python 3.11+
- `typer[all]` + `rich` (CLI)
- `mcp` (optional, for full MCP SDK support — falls back to JSON-RPC without it)

## Advanced Tuning

See [TUNING_GUIDE.md](TUNING_GUIDE.md) for:

- profile strategy by use case
- repo config precedence
- category filters and scope metadata interpretation
- quality checklist for low-noise analyses

---

## Troubleshooting

### Installation Issues

**"No module named 'context_refactor'"**

Ensure you have activated the virtual environment and installed the package:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,mcp]"
```

### Execution Issues

**"FileNotFoundError: token_report.py not found"**

The token analysis script cannot be located. This usually means the package installation is corrupted:

```bash
pip install --force-reinstall -e .
```

**"context-refactor: command not found"**

The CLI entry point is not available. Reinstall with editable mode:

```bash
pip install -e .
```

**"mcp SDK not installed — running in fallback JSON-RPC mode"**

This is **normal** and non-blocking. The MCP server functions via JSON-RPC fallback. To use the full MCP SDK:

```bash
pip install mcp>=1.0.0
```

### Configuration Issues

**"ValueError: Unknown category 'my_category'"**

The `.context-refactor.json` mentions an invalid category. Valid categories are:
- `source_code`
- `markdown`
- `configuration`
- `binary`
- `other`

**"ValueError: Unknown analysis profile"**

Valid profiles are: `default`, `full`, `source-only`, `docs`.

### Performance Issues

**Analysis is very slow or times out**

The default timeout is 120 seconds. For very large projects:

1. Use the `source-only` profile to reduce scope:
   ```bash
   context-refactor analyze /path --profile source-only
   ```

2. Exclude additional directories:
   ```bash
   context-refactor analyze /path --exclude-dirs "coverage,reports,build"
   ```

3. Reduce the `--max-mb` in token_report.py (if running directly)

---

## Project Independence

ContextRactor is a **fully autonomous product** and does not depend on any external systems or projects:

- **All dependencies** are declared in `pyproject.toml` and installed via pip
- **No hardcoded paths** to external resources
- **No hidden environment assumptions** — works out of the box with `pip install`
- **Fallback mechanisms** for optional features (e.g., matplotlib for charts, MCP SDK for full server)
- **Clear error messages** for configuration mistakes

For detailed information about architecture and design decisions, see [TUNING_GUIDE.md](TUNING_GUIDE.md) and [TOKEN_REPORT.md](TOKEN_REPORT.md).
