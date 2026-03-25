"""MCP server for ContextRefactor — stdio transport.

Exposes four tools via the Model Context Protocol:

* ``context_refactor.analyze_project``
* ``context_refactor.context_budget``
* ``context_refactor.detect_refactor_candidates``
* ``context_refactor.generate_refactor_plan``

Run with::

    python -m mcp_server.server

Or register in your MCP client configuration (e.g. Claude Desktop, VS Code)
pointing to this module.
"""

from __future__ import annotations

import asyncio
import json
import sys

# Try to use the official ``mcp`` SDK.  If it isn't installed yet, fall back
# to a minimal stdin/stdout JSON-RPC loop so the project is still functional.
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool

    _HAS_MCP_SDK = True
except ImportError:
    _HAS_MCP_SDK = False

from mcp_server.tools import (
    analyze_project,
    context_budget,
    detect_code_smells,
    detect_refactor_candidates_tool,
    generate_refactor_plan_tool,
    generate_refactor_suggestions,
)


def _analysis_scope_properties() -> dict[str, dict]:
    return {
        "analysis_profile": {
            "type": "string",
            "enum": ["default", "full", "source-only", "docs"],
            "default": "default",
            "description": "Analysis profile controlling default exclusions and category focus.",
        },
        "config_path": {
            "type": "string",
            "description": "Optional path to a .context-refactor.json config file.",
        },
        "exclude_dirs": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Directory names or relative directory paths to exclude.",
        },
        "exclude_globs": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Glob patterns to exclude from the analysis.",
        },
        "exclude_files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "File patterns to exclude from the analysis.",
        },
        "include_categories": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["source_code", "markdown", "configuration", "binary", "other"],
            },
            "description": "Optional allowlist of file categories.",
        },
        "exclude_categories": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["source_code", "markdown", "configuration", "binary", "other"],
            },
            "description": "Optional denylist of file categories.",
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# MCP SDK path (preferred)
# ══════════════════════════════════════════════════════════════════════════════

def _build_mcp_server() -> Server:
    """Construct an MCP ``Server`` with all four tools registered."""
    server = Server("context-refactor")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="context_refactor.analyze_project",
                description=(
                    "Full project analysis: token count, context budget, "
                    "refactoring recommendations, and step-by-step plan."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Absolute path to the project root.",
                        },
                        "llm_context_size": {
                            "type": "integer",
                            "description": "LLM context window size in tokens (default 128000).",
                            "default": 128000,
                        },
                        "safety_margin": {
                            "type": "number",
                            "description": "Fraction of context to use (0-1, default 0.8).",
                            "default": 0.8,
                        },
                        "estimator": {
                            "type": "string",
                            "enum": ["bytes", "chars", "whitespace", "heuristic"],
                            "default": "bytes",
                        },
                        **_analysis_scope_properties(),
                    },
                    "required": ["project_path"],
                },
            ),
            Tool(
                name="context_refactor.context_budget",
                description="Compute whether the project fits an LLM context window.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {"type": "string"},
                        "llm_context_size": {"type": "integer", "default": 128000},
                        "safety_margin": {"type": "number", "default": 0.8},
                        "estimator": {
                            "type": "string",
                            "enum": ["bytes", "chars", "whitespace", "heuristic"],
                            "default": "bytes",
                        },
                        **_analysis_scope_properties(),
                    },
                    "required": ["project_path"],
                },
            ),
            Tool(
                name="context_refactor.detect_refactor_candidates",
                description="Detect code smells and refactoring candidates in the project.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {"type": "string"},
                        "estimator": {
                            "type": "string",
                            "enum": ["bytes", "chars", "whitespace", "heuristic"],
                            "default": "bytes",
                        },
                        "top_n": {"type": "integer", "default": 50},
                        **_analysis_scope_properties(),
                    },
                    "required": ["project_path"],
                },
            ),
            Tool(
                name="context_refactor.generate_refactor_plan",
                description=(
                    "Generate a step-by-step refactoring plan to fit the "
                    "codebase inside a single LLM context window."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {"type": "string"},
                        "llm_context_size": {"type": "integer", "default": 128000},
                        "safety_margin": {"type": "number", "default": 0.8},
                        "estimator": {
                            "type": "string",
                            "enum": ["bytes", "chars", "whitespace", "heuristic"],
                            "default": "bytes",
                        },
                        **_analysis_scope_properties(),
                    },
                    "required": ["project_path"],
                },
            ),
            Tool(
                name="context_refactor.detect_code_smells",
                description=(
                    "Run the Heuristics Engine to detect code smells per file "
                    "using pluggable rules and context-window-relative thresholds."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {"type": "string"},
                        "llm_context_size": {
                            "type": "integer",
                            "description": "LLM context window size in tokens (default 128000).",
                            "default": 128000,
                        },
                        "estimator": {
                            "type": "string",
                            "enum": ["bytes", "chars", "whitespace", "heuristic"],
                            "default": "bytes",
                        },
                        "top_n": {"type": "integer", "default": 50},
                        **_analysis_scope_properties(),
                    },
                    "required": ["project_path"],
                },
            ),
            Tool(
                name="context_refactor.generate_refactor_suggestions",
                description=(
                    "Generate human-readable refactoring suggestions and a "
                    "step-by-step plan using the Heuristics Engine."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {"type": "string"},
                        "llm_context_size": {"type": "integer", "default": 128000},
                        "safety_margin": {"type": "number", "default": 0.8},
                        "estimator": {
                            "type": "string",
                            "enum": ["bytes", "chars", "whitespace", "heuristic"],
                            "default": "bytes",
                        },
                        **_analysis_scope_properties(),
                    },
                    "required": ["project_path"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        dispatchers = {
            "context_refactor.analyze_project": analyze_project,
            "context_refactor.context_budget": context_budget,
            "context_refactor.detect_refactor_candidates": detect_refactor_candidates_tool,
            "context_refactor.generate_refactor_plan": generate_refactor_plan_tool,
            "context_refactor.detect_code_smells": detect_code_smells,
            "context_refactor.generate_refactor_suggestions": generate_refactor_suggestions,
        }

        fn = dispatchers.get(name)
        if fn is None:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        try:
            result = fn(**arguments)
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        except Exception as exc:
            return [TextContent(type="text", text=f"Error: {exc}")]

    return server


# ══════════════════════════════════════════════════════════════════════════════
# Fallback JSON-RPC loop (no SDK)
# ══════════════════════════════════════════════════════════════════════════════

def _fallback_jsonrpc_loop() -> None:
    """Minimal JSON-RPC/stdio loop for environments without the mcp SDK."""
    dispatchers = {
        "context_refactor.analyze_project": analyze_project,
        "context_refactor.context_budget": context_budget,
        "context_refactor.detect_refactor_candidates": detect_refactor_candidates_tool,
        "context_refactor.generate_refactor_plan": generate_refactor_plan_tool,
        "context_refactor.detect_code_smells": detect_code_smells,
        "context_refactor.generate_refactor_suggestions": generate_refactor_suggestions,
    }

    sys.stderr.write(
        "⚠ mcp SDK not installed — running in fallback JSON-RPC mode.\n"
        "  Install with: pip install mcp\n"
    )

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        if method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {"name": n, "description": f"ContextRefactor tool: {n}"}
                        for n in dispatchers
                    ]
                },
            }
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            fn = dispatchers.get(tool_name)
            if fn is None:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
                }
            else:
                try:
                    result = fn(**arguments)
                    response = {"jsonrpc": "2.0", "id": req_id, "result": result}
                except Exception as exc:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32000, "message": str(exc)},
                    }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

async def run_server() -> None:
    """Start the MCP server (stdio transport)."""
    if _HAS_MCP_SDK:
        server = _build_mcp_server()
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    else:
        _fallback_jsonrpc_loop()


def main() -> None:
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
