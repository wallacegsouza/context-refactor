"""Source-code smell detection and refactoring recommendation engine.

Uses **AST parsing** for Python and **regex-based heuristics** for other
supported languages (TypeScript, JavaScript, Java, Go, Rust, C/C++, etc.).

The module does NOT modify any file.  It only reads source code and emits
structured :class:`RefactorRecommendation` instances.
"""

from __future__ import annotations

import ast
import os
import re
from typing import Sequence

from .models import (
    ClassInfo,
    CodeSmell,
    FileCategory,
    FunctionInfo,
    Priority,
    RefactorRecommendation,
    RefactorTechnique,
)

# ── Thresholds ────────────────────────────────────────────────────────────────

LONG_METHOD_LINES = 60
LARGE_CLASS_LINES = 300
LARGE_CLASS_METHODS = 15
LONG_PARAM_COUNT = 5
DEEP_NESTING_LEVEL = 4
GOD_FILE_LINES = 600
GOD_FILE_TOKENS = 4000


# ══════════════════════════════════════════════════════════════════════════════
# Python analyzer (AST-based)
# ══════════════════════════════════════════════════════════════════════════════


def _python_functions(tree: ast.AST) -> list[FunctionInfo]:
    """Extract top-level and nested function/method definitions."""
    funcs: list[FunctionInfo] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = node.end_lineno or start
            params = len(node.args.args) + len(node.args.posonlyargs) + len(node.args.kwonlyargs)
            # Simple nesting depth: count enclosing function-defs
            depth = 0
            for parent in ast.walk(tree):
                if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if parent is not node and hasattr(parent, "lineno"):
                        p_end = parent.end_lineno or parent.lineno
                        if parent.lineno <= start and p_end >= end:
                            depth += 1
            funcs.append(
                FunctionInfo(
                    name=node.name,
                    start_line=start,
                    end_line=end,
                    line_count=end - start + 1,
                    parameter_count=params,
                    nesting_depth=depth,
                )
            )
    return funcs


def _python_classes(tree: ast.AST) -> list[ClassInfo]:
    classes: list[ClassInfo] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            start = node.lineno
            end = node.end_lineno or start
            methods = sum(
                1
                for child in ast.walk(node)
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                and child is not node
            )
            classes.append(
                ClassInfo(
                    name=node.name,
                    start_line=start,
                    end_line=end,
                    line_count=end - start + 1,
                    method_count=methods,
                )
            )
    return classes


def _analyze_python(filepath: str, source: str) -> tuple[list[FunctionInfo], list[ClassInfo]]:
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return [], []
    return _python_functions(tree), _python_classes(tree)


# ══════════════════════════════════════════════════════════════════════════════
# Generic (regex) analyzer — TypeScript, JavaScript, Java, Go, etc.
# ══════════════════════════════════════════════════════════════════════════════

# Patterns are intentionally simple; they capture the *start* of a construct.
# We then scan forward counting braces to estimate the body length.

_TS_FUNC_RE = re.compile(
    r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)",
    re.MULTILINE,
)
_TS_METHOD_RE = re.compile(
    r"(?:public|private|protected|static|async|\s)*(\w+)\s*\(([^)]*)\)\s*(?::\s*\S+)?\s*\{",
    re.MULTILINE,
)
_TS_ARROW_RE = re.compile(
    r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*(?::\s*\S+)?\s*=>",
    re.MULTILINE,
)
_TS_CLASS_RE = re.compile(
    r"(?:export\s+)?(?:abstract\s+)?class\s+(\w+)",
    re.MULTILINE,
)
_JAVA_METHOD_RE = re.compile(
    r"(?:public|private|protected|static|\s)+\w+(?:<[^>]+>)?\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+\S+\s*)?\{",
    re.MULTILINE,
)
_GO_FUNC_RE = re.compile(
    r"func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(([^)]*)\)",
    re.MULTILINE,
)


def _count_params(param_str: str) -> int:
    """Count comma-separated parameters, handling empty strings."""
    stripped = param_str.strip()
    if not stripped:
        return 0
    return stripped.count(",") + 1


def _brace_block_length(lines: list[str], start_idx: int) -> int:
    """Count lines in a brace-delimited block starting at *start_idx*."""
    depth = 0
    started = False
    for i in range(start_idx, len(lines)):
        for ch in lines[i]:
            if ch == "{":
                depth += 1
                started = True
            elif ch == "}":
                depth -= 1
                if started and depth == 0:
                    return i - start_idx + 1
    return len(lines) - start_idx


def _generic_functions(lines: list[str], source: str, ext: str) -> list[FunctionInfo]:
    patterns: list[re.Pattern[str]] = []
    if ext in {".ts", ".tsx", ".js", ".jsx"}:
        patterns = [_TS_FUNC_RE, _TS_METHOD_RE, _TS_ARROW_RE]
    elif ext in {".java", ".kt"}:
        patterns = [_JAVA_METHOD_RE]
    elif ext == ".go":
        patterns = [_GO_FUNC_RE]
    else:
        patterns = [_TS_FUNC_RE]  # Fallback

    funcs: list[FunctionInfo] = []
    seen_starts: set[int] = set()

    for pat in patterns:
        for m in pat.finditer(source):
            line_no = source[: m.start()].count("\n")
            if line_no in seen_starts:
                continue
            seen_starts.add(line_no)
            name = m.group(1)
            params_str = m.group(2) if m.lastindex and m.lastindex >= 2 else ""
            block_len = _brace_block_length(lines, line_no)
            funcs.append(
                FunctionInfo(
                    name=name,
                    start_line=line_no + 1,
                    end_line=line_no + block_len,
                    line_count=block_len,
                    parameter_count=_count_params(params_str),
                )
            )

    return funcs


def _generic_classes(lines: list[str], source: str, ext: str) -> list[ClassInfo]:
    if ext not in {".ts", ".tsx", ".js", ".jsx", ".java", ".kt"}:
        return []

    classes: list[ClassInfo] = []
    for m in _TS_CLASS_RE.finditer(source):
        line_no = source[: m.start()].count("\n")
        block_len = _brace_block_length(lines, line_no)
        # Count methods inside the class block
        class_body = "\n".join(lines[line_no : line_no + block_len])
        method_count = len(_TS_METHOD_RE.findall(class_body))
        classes.append(
            ClassInfo(
                name=m.group(1),
                start_line=line_no + 1,
                end_line=line_no + block_len,
                line_count=block_len,
                method_count=method_count,
            )
        )
    return classes


def _analyze_generic(filepath: str, source: str, ext: str) -> tuple[list[FunctionInfo], list[ClassInfo]]:
    lines = source.splitlines()
    return _generic_functions(lines, source, ext), _generic_classes(lines, source, ext)


# ══════════════════════════════════════════════════════════════════════════════
# Unified entry point
# ══════════════════════════════════════════════════════════════════════════════


def analyze_source_file(
    filepath: str,
    tokens: int,
) -> list[RefactorRecommendation]:
    """Analyse a single source-code file and return recommendations.

    The function:
    1. Reads the file.
    2. Dispatches to the Python AST analyser or the regex-based analyser.
    3. Detects code smells against configurable thresholds.
    4. Maps each smell to one or more refactoring techniques.
    """
    try:
        with open(filepath, encoding="utf-8", errors="ignore") as fh:
            source = fh.read()
    except OSError:
        return []

    ext = os.path.splitext(filepath)[1].lower()
    lines = source.splitlines()
    total_lines = len(lines)

    # Dispatch
    if ext == ".py":
        funcs, classes = _analyze_python(filepath, source)
    else:
        funcs, classes = _analyze_generic(filepath, source, ext)

    recommendations: list[RefactorRecommendation] = []

    # ── God File ──────────────────────────────────────────────────────────
    if total_lines >= GOD_FILE_LINES or tokens >= GOD_FILE_TOKENS:
        recommendations.append(
            RefactorRecommendation(
                file_path=filepath,
                category=FileCategory.SOURCE_CODE,
                smell=CodeSmell.GOD_FILE,
                technique=RefactorTechnique.EXTRACT_MODULE,
                priority=Priority.CRITICAL if tokens >= GOD_FILE_TOKENS * 2 else Priority.HIGH,
                description=(
                    f"File has {total_lines} lines / ~{tokens} tokens. "
                    f"Consider extracting cohesive pieces into separate modules."
                ),
                estimated_token_reduction=int(tokens * 0.30),
                details={"total_lines": total_lines},
            )
        )

    # ── Long Methods ──────────────────────────────────────────────────────
    for fn in funcs:
        if fn.line_count >= LONG_METHOD_LINES:
            recommendations.append(
                RefactorRecommendation(
                    file_path=filepath,
                    category=FileCategory.SOURCE_CODE,
                    smell=CodeSmell.LONG_METHOD,
                    technique=RefactorTechnique.EXTRACT_METHOD,
                    priority=Priority.HIGH if fn.line_count >= LONG_METHOD_LINES * 2 else Priority.MEDIUM,
                    description=(
                        f"Function `{fn.name}` has {fn.line_count} lines "
                        f"(threshold: {LONG_METHOD_LINES}). Extract smaller methods."
                    ),
                    estimated_token_reduction=int(fn.line_count * 0.8),
                    details={
                        "function": fn.name,
                        "lines": fn.line_count,
                        "start_line": fn.start_line,
                        "end_line": fn.end_line,
                    },
                )
            )

    # ── Long Parameter Lists ──────────────────────────────────────────────
    for fn in funcs:
        if fn.parameter_count >= LONG_PARAM_COUNT:
            recommendations.append(
                RefactorRecommendation(
                    file_path=filepath,
                    category=FileCategory.SOURCE_CODE,
                    smell=CodeSmell.LONG_PARAMETER_LIST,
                    technique=RefactorTechnique.EXTRACT_VARIABLE,
                    priority=Priority.LOW,
                    description=(
                        f"Function `{fn.name}` has {fn.parameter_count} parameters. "
                        f"Consider an options object or parameter object."
                    ),
                    details={
                        "function": fn.name,
                        "parameter_count": fn.parameter_count,
                    },
                )
            )

    # ── Deep Nesting ──────────────────────────────────────────────────────
    for fn in funcs:
        if fn.nesting_depth >= DEEP_NESTING_LEVEL:
            recommendations.append(
                RefactorRecommendation(
                    file_path=filepath,
                    category=FileCategory.SOURCE_CODE,
                    smell=CodeSmell.DEEP_NESTING,
                    technique=RefactorTechnique.DECOMPOSE_CONDITIONAL,
                    priority=Priority.MEDIUM,
                    description=(
                        f"Function `{fn.name}` has nesting depth {fn.nesting_depth}. "
                        f"Flatten with guard clauses or extract helper functions."
                    ),
                    details={
                        "function": fn.name,
                        "nesting_depth": fn.nesting_depth,
                    },
                )
            )

    # ── Large Classes ─────────────────────────────────────────────────────
    for cls in classes:
        is_large = cls.line_count >= LARGE_CLASS_LINES or cls.method_count >= LARGE_CLASS_METHODS
        if is_large:
            recommendations.append(
                RefactorRecommendation(
                    file_path=filepath,
                    category=FileCategory.SOURCE_CODE,
                    smell=CodeSmell.LARGE_CLASS,
                    technique=RefactorTechnique.EXTRACT_CLASS,
                    priority=Priority.HIGH,
                    description=(
                        f"Class `{cls.name}` has {cls.line_count} lines and "
                        f"{cls.method_count} methods. Split into smaller classes."
                    ),
                    estimated_token_reduction=int(cls.line_count * 0.6),
                    details={
                        "class": cls.name,
                        "lines": cls.line_count,
                        "methods": cls.method_count,
                    },
                )
            )

    return recommendations
