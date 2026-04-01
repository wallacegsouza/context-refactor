"""Dependency edge extraction helpers."""

from __future__ import annotations

import ast
import re

from .models import (
    DependencyEdge,
    DependencyKind,
    DependencyScope,
)

# TypeScript / JavaScript
_TS_IMPORT_FROM_RE = re.compile(
    r"""import\s+(?:type\s+)?(?:"""
    r"""\{[^}]*\}"""
    r"""|[\w*]+"""
    r"""(?:\s*,\s*\{[^}]*\})?"""
    r""")\s+from\s+['"]([^'"]+)['"]""",
    re.MULTILINE,
)
_TS_IMPORT_SIDE_RE = re.compile(
    r"""import\s+['"]([^'"]+)['"]""",
    re.MULTILINE,
)
_TS_REQUIRE_RE = re.compile(
    r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""",
    re.MULTILINE,
)

# Java
_JAVA_IMPORT_RE = re.compile(
    r"^import\s+(?:static\s+)?([\w.]+(?:\.\*)?)\s*;",
    re.MULTILINE,
)

# Go
_GO_IMPORT_SINGLE_RE = re.compile(
    r'^import\s+"([^"]+)"',
    re.MULTILINE,
)
_GO_IMPORT_BLOCK_RE = re.compile(
    r"import\s+\((.*?)\)",
    re.DOTALL,
)
_GO_IMPORT_LINE_RE = re.compile(r'"([^"]+)"')


def extract_dependency_edges(
    filepath: str,
    source: str,
    ext: str,
) -> list[DependencyEdge]:
    """Extract dependency edges from source code based on file extension."""
    if ext == ".py":
        return _extract_python_dependencies(filepath, source)
    return _extract_regex_dependencies(filepath, source, ext)


def _extract_python_dependencies(
    filepath: str,
    source: str,
) -> list[DependencyEdge]:
    """Extract dependency edges from a Python source file via AST."""
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return []

    edges: list[DependencyEdge] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                edges.append(
                    DependencyEdge(
                        source_file=filepath,
                        target_module=alias.name,
                        target_file=None,
                        kind=DependencyKind.IMPORT,
                        scope=DependencyScope.EXTERNAL,
                        symbol=alias.asname or alias.name,
                        line_number=node.lineno,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level and node.level > 0:
                module = "." * node.level + module

            for alias in node.names:
                edges.append(
                    DependencyEdge(
                        source_file=filepath,
                        target_module=module,
                        target_file=None,
                        kind=DependencyKind.IMPORT,
                        scope=DependencyScope.EXTERNAL,
                        symbol=alias.name,
                        line_number=node.lineno,
                    )
                )
        elif isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = _ast_name(base)
                if base_name:
                    edges.append(
                        DependencyEdge(
                            source_file=filepath,
                            target_module="",
                            target_file=None,
                            kind=DependencyKind.INHERITANCE,
                            scope=DependencyScope.INTERNAL,
                            symbol=base_name,
                            line_number=node.lineno,
                        )
                    )

            for dec in node.decorator_list:
                dec_name = _ast_name(dec)
                if dec_name:
                    edges.append(
                        DependencyEdge(
                            source_file=filepath,
                            target_module="",
                            target_file=None,
                            kind=DependencyKind.DECORATOR,
                            scope=DependencyScope.INTERNAL,
                            symbol=dec_name,
                            line_number=getattr(dec, "lineno", node.lineno),
                        )
                    )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                dec_name = _ast_name(dec)
                if dec_name:
                    edges.append(
                        DependencyEdge(
                            source_file=filepath,
                            target_module="",
                            target_file=None,
                            kind=DependencyKind.DECORATOR,
                            scope=DependencyScope.INTERNAL,
                            symbol=dec_name,
                            line_number=getattr(dec, "lineno", node.lineno),
                        )
                    )

    return edges


def _ast_name(node: ast.AST) -> str | None:
    """Extract a readable name from an AST node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _ast_name(node.value)
        if prefix:
            return f"{prefix}.{node.attr}"
        return node.attr
    if isinstance(node, ast.Call):
        return _ast_name(node.func)
    return None


def _extract_regex_dependencies(
    filepath: str,
    source: str,
    ext: str,
) -> list[DependencyEdge]:
    """Extract dependency edges using regex patterns for non-Python languages."""
    edges: list[DependencyEdge] = []

    if ext in {".ts", ".tsx", ".js", ".jsx"}:
        _extract_ts_js(filepath, source, edges)
    elif ext in {".java", ".kt"}:
        _extract_java(filepath, source, edges)
    elif ext == ".go":
        _extract_go(filepath, source, edges)

    return edges


def _extract_ts_js(
    filepath: str,
    source: str,
    edges: list[DependencyEdge],
) -> None:
    """Extract imports from TypeScript/JavaScript source."""
    seen: set[str] = set()

    for pattern in (_TS_IMPORT_FROM_RE, _TS_IMPORT_SIDE_RE, _TS_REQUIRE_RE):
        for match in pattern.finditer(source):
            module = match.group(1)
            if module in seen:
                continue
            seen.add(module)
            line_no = source[: match.start()].count("\n") + 1
            edges.append(
                DependencyEdge(
                    source_file=filepath,
                    target_module=module,
                    target_file=None,
                    kind=DependencyKind.IMPORT,
                    scope=DependencyScope.EXTERNAL,
                    symbol=module.split("/")[-1],
                    line_number=line_no,
                )
            )


def _extract_java(
    filepath: str,
    source: str,
    edges: list[DependencyEdge],
) -> None:
    """Extract imports from Java/Kotlin source."""
    for match in _JAVA_IMPORT_RE.finditer(source):
        module = match.group(1)
        line_no = source[: match.start()].count("\n") + 1
        edges.append(
            DependencyEdge(
                source_file=filepath,
                target_module=module,
                target_file=None,
                kind=DependencyKind.IMPORT,
                scope=DependencyScope.EXTERNAL,
                symbol=module.rsplit(".", 1)[-1],
                line_number=line_no,
            )
        )


def _extract_go(
    filepath: str,
    source: str,
    edges: list[DependencyEdge],
) -> None:
    """Extract imports from Go source."""
    seen: set[str] = set()

    for match in _GO_IMPORT_SINGLE_RE.finditer(source):
        module = match.group(1)
        if module in seen:
            continue
        seen.add(module)
        line_no = source[: match.start()].count("\n") + 1
        edges.append(
            DependencyEdge(
                source_file=filepath,
                target_module=module,
                target_file=None,
                kind=DependencyKind.IMPORT,
                scope=DependencyScope.EXTERNAL,
                symbol=module.rsplit("/", 1)[-1],
                line_number=line_no,
            )
        )

    for block_match in _GO_IMPORT_BLOCK_RE.finditer(source):
        block_start_line = source[: block_match.start()].count("\n") + 1
        block_text = block_match.group(1)
        for line_match in _GO_IMPORT_LINE_RE.finditer(block_text):
            module = line_match.group(1)
            if module in seen:
                continue
            seen.add(module)
            rel_line = block_text[: line_match.start()].count("\n")
            edges.append(
                DependencyEdge(
                    source_file=filepath,
                    target_module=module,
                    target_file=None,
                    kind=DependencyKind.IMPORT,
                    scope=DependencyScope.EXTERNAL,
                    symbol=module.rsplit("/", 1)[-1],
                    line_number=block_start_line + rel_line + 1,
                )
            )
