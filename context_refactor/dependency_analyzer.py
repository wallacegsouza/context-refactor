"""Dependency analysis engine — builds import graphs and computes dependency weights.

Extracts dependency edges from source files using AST (Python) or regex
(TypeScript, JavaScript, Java, Go), resolves modules to project-internal or
external scope, builds a directed dependency graph, and computes a
dependency-weight multiplier per file.

The dependency weight is combined with the raw token count to produce an
``effective_token_size`` that better reflects the real cost of reading,
understanding, and refactoring a file.
"""

from __future__ import annotations

import ast
import math
import os
import re
import sys
from collections import defaultdict
from collections.abc import Sequence

from .models import (
    DependencyEdge,
    DependencyGraph,
    DependencyKind,
    DependencyScope,
    DependencyWeightResult,
    FileCategory,
    FileDependencyInfo,
    FileTokenInfo,
)

# ── Python stdlib modules (used to classify imports as external) ─────────────

_PYTHON_STDLIB_MODULES: frozenset[str] = frozenset(sys.stdlib_module_names)

# ── Regex patterns for non-Python languages ──────────────────────────────────

# TypeScript / JavaScript
_TS_IMPORT_FROM_RE = re.compile(
    r"""import\s+(?:type\s+)?(?:"""
    r"""\{[^}]*\}"""          # named imports
    r"""|[\w*]+"""            # default import
    r"""(?:\s*,\s*\{[^}]*\})?"""  # default + named
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


# ══════════════════════════════════════════════════════════════════════════════
# Import extraction
# ══════════════════════════════════════════════════════════════════════════════


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
        # import foo, import foo.bar
        if isinstance(node, ast.Import):
            for alias in node.names:
                edges.append(DependencyEdge(
                    source_file=filepath,
                    target_module=alias.name,
                    target_file=None,  # resolved later
                    kind=DependencyKind.IMPORT,
                    scope=DependencyScope.EXTERNAL,  # resolved later
                    symbol=alias.asname or alias.name,
                    line_number=node.lineno,
                ))

        # from foo import bar
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            # For relative imports, prefix with dots
            if node.level and node.level > 0:
                module = "." * node.level + module

            for alias in node.names:
                edges.append(DependencyEdge(
                    source_file=filepath,
                    target_module=module,
                    target_file=None,
                    kind=DependencyKind.IMPORT,
                    scope=DependencyScope.EXTERNAL,
                    symbol=alias.name,
                    line_number=node.lineno,
                ))

        # class Foo(Bar, Baz): -> inheritance
        elif isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = _ast_name(base)
                if base_name:
                    edges.append(DependencyEdge(
                        source_file=filepath,
                        target_module="",
                        target_file=None,
                        kind=DependencyKind.INHERITANCE,
                        scope=DependencyScope.INTERNAL,
                        symbol=base_name,
                        line_number=node.lineno,
                    ))

            # Decorators on classes
            for dec in node.decorator_list:
                dec_name = _ast_name(dec)
                if dec_name:
                    edges.append(DependencyEdge(
                        source_file=filepath,
                        target_module="",
                        target_file=None,
                        kind=DependencyKind.DECORATOR,
                        scope=DependencyScope.INTERNAL,
                        symbol=dec_name,
                        line_number=getattr(dec, "lineno", node.lineno),
                    ))

        # Decorators on functions
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                dec_name = _ast_name(dec)
                if dec_name:
                    edges.append(DependencyEdge(
                        source_file=filepath,
                        target_module="",
                        target_file=None,
                        kind=DependencyKind.DECORATOR,
                        scope=DependencyScope.INTERNAL,
                        symbol=dec_name,
                        line_number=getattr(dec, "lineno", node.lineno),
                    ))

    return edges


def _ast_name(node: ast.AST) -> str | None:
    """Extract a readable name from an AST node (Name, Attribute, Call)."""
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
    lines = source.split("\n")

    for pattern in (_TS_IMPORT_FROM_RE, _TS_IMPORT_SIDE_RE, _TS_REQUIRE_RE):
        for m in pattern.finditer(source):
            module = m.group(1)
            if module in seen:
                continue
            seen.add(module)
            line_no = source[:m.start()].count("\n") + 1
            edges.append(DependencyEdge(
                source_file=filepath,
                target_module=module,
                target_file=None,
                kind=DependencyKind.IMPORT,
                scope=DependencyScope.EXTERNAL,
                symbol=module.split("/")[-1],
                line_number=line_no,
            ))


def _extract_java(
    filepath: str,
    source: str,
    edges: list[DependencyEdge],
) -> None:
    """Extract imports from Java/Kotlin source."""
    for m in _JAVA_IMPORT_RE.finditer(source):
        module = m.group(1)
        line_no = source[:m.start()].count("\n") + 1
        edges.append(DependencyEdge(
            source_file=filepath,
            target_module=module,
            target_file=None,
            kind=DependencyKind.IMPORT,
            scope=DependencyScope.EXTERNAL,
            symbol=module.rsplit(".", 1)[-1],
            line_number=line_no,
        ))


def _extract_go(
    filepath: str,
    source: str,
    edges: list[DependencyEdge],
) -> None:
    """Extract imports from Go source."""
    seen: set[str] = set()

    # Single imports
    for m in _GO_IMPORT_SINGLE_RE.finditer(source):
        module = m.group(1)
        if module not in seen:
            seen.add(module)
            line_no = source[:m.start()].count("\n") + 1
            edges.append(DependencyEdge(
                source_file=filepath,
                target_module=module,
                target_file=None,
                kind=DependencyKind.IMPORT,
                scope=DependencyScope.EXTERNAL,
                symbol=module.rsplit("/", 1)[-1],
                line_number=line_no,
            ))

    # Block imports
    for block_m in _GO_IMPORT_BLOCK_RE.finditer(source):
        block_start_line = source[:block_m.start()].count("\n") + 1
        block_text = block_m.group(1)
        for line_m in _GO_IMPORT_LINE_RE.finditer(block_text):
            module = line_m.group(1)
            if module not in seen:
                seen.add(module)
                rel_line = block_text[:line_m.start()].count("\n")
                edges.append(DependencyEdge(
                    source_file=filepath,
                    target_module=module,
                    target_file=None,
                    kind=DependencyKind.IMPORT,
                    scope=DependencyScope.EXTERNAL,
                    symbol=module.rsplit("/", 1)[-1],
                    line_number=block_start_line + rel_line + 1,
                ))


# ══════════════════════════════════════════════════════════════════════════════
# Module resolution
# ══════════════════════════════════════════════════════════════════════════════


def _resolve_module_to_file(
    module_path: str,
    project_path: str,
    source_file: str,
    ext: str,
    symbol: str | None = None,
) -> tuple[str | None, DependencyScope]:
    """Attempt to resolve a module name to a file path within the project.

    Returns (relative_path_or_None, scope).  If the module cannot be mapped
    to a file inside *project_path*, scope is EXTERNAL.
    """
    if ext == ".py":
        return _resolve_python_module(module_path, project_path, source_file, symbol=symbol)
    if ext in {".ts", ".tsx", ".js", ".jsx"}:
        return _resolve_ts_module(module_path, project_path, source_file)
    # Java/Go/others: best-effort
    return None, DependencyScope.EXTERNAL


def _resolve_python_module(
    module_path: str,
    project_path: str,
    source_file: str,
    symbol: str | None = None,
) -> tuple[str | None, DependencyScope]:
    """Resolve a Python module path to a project file."""
    if not module_path:
        return None, DependencyScope.EXTERNAL

    module_candidates: list[str] = []
    if symbol and symbol != "*":
        if module_path.endswith("."):
            module_candidates.append(f"{module_path}{symbol}")
        elif module_path:
            module_candidates.append(f"{module_path}.{symbol}")
    module_candidates.append(module_path)

    for candidate_module in module_candidates:
        # Relative import (starts with dots)
        if candidate_module.startswith("."):
            dots = len(candidate_module) - len(candidate_module.lstrip("."))
            remainder = candidate_module[dots:]

            # Resolve relative to source_file
            source_dir = os.path.dirname(source_file)
            for _ in range(dots - 1):
                source_dir = os.path.dirname(source_dir)

            if remainder:
                parts = remainder.split(".")
            else:
                parts = []

            base = os.path.join(project_path, source_dir, *parts)
            resolved = _check_python_path(base, project_path)
            if resolved[0] is not None:
                return resolved

        # Absolute import — check if it's a stdlib module
        top_level = candidate_module.split(".")[0]
        if top_level in _PYTHON_STDLIB_MODULES:
            continue

        # Try to resolve within project
        parts = candidate_module.split(".")
        base = os.path.join(project_path, *parts)
        resolved = _check_python_path(base, project_path)
        if resolved[0] is not None:
            return resolved

    return None, DependencyScope.EXTERNAL


def _check_python_path(
    base: str,
    project_path: str,
) -> tuple[str | None, DependencyScope]:
    """Check if *base*.py or *base*/__init__.py exists."""
    for candidate in (base + ".py", os.path.join(base, "__init__.py")):
        if os.path.isfile(candidate):
            rel = os.path.relpath(candidate, project_path)
            return rel, DependencyScope.INTERNAL
    return None, DependencyScope.EXTERNAL


def _resolve_ts_module(
    module_path: str,
    project_path: str,
    source_file: str,
) -> tuple[str | None, DependencyScope]:
    """Resolve a TypeScript/JavaScript module path."""
    # Non-relative imports are external (node_modules / bare specifiers)
    if not module_path.startswith("."):
        return None, DependencyScope.EXTERNAL

    # Relative import
    source_dir = os.path.dirname(os.path.join(project_path, source_file))
    base = os.path.normpath(os.path.join(source_dir, module_path))

    # Try extensions
    for suffix in ("", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.js"):
        candidate = base + suffix
        if os.path.isfile(candidate):
            rel = os.path.relpath(candidate, project_path)
            return rel, DependencyScope.INTERNAL

    return None, DependencyScope.EXTERNAL


# ══════════════════════════════════════════════════════════════════════════════
# Graph building
# ══════════════════════════════════════════════════════════════════════════════

# Language extension mapping (same as refactor_heuristics.py)
_SOURCE_EXTS: frozenset[str] = frozenset({
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".kt", ".go", ".rs", ".rb",
    ".php", ".cs", ".cpp", ".cc", ".cxx",
    ".c", ".h", ".hpp", ".swift", ".scala",
    ".lua", ".sh", ".bash", ".zsh",
})


def build_dependency_graph(
    file_infos: Sequence[FileTokenInfo],
    project_path: str,
) -> DependencyGraph:
    """Build a project-wide dependency graph from file token infos.

    Only SOURCE_CODE files participate in the graph.  Each file is parsed
    for import statements using AST (Python) or regex (other languages).
    Dependencies are resolved to internal project files where possible.
    """
    all_edges: list[DependencyEdge] = []
    adjacency: dict[str, set[str]] = defaultdict(set)
    reverse_adjacency: dict[str, set[str]] = defaultdict(set)
    # Per-file raw edges (before resolution)
    file_edges: dict[str, list[DependencyEdge]] = defaultdict(list)

    # Set of known project files (relative paths)
    known_files: set[str] = {fi.path for fi in file_infos}

    for fi in file_infos:
        if fi.category != FileCategory.SOURCE_CODE:
            continue
        if fi.ext.lower() not in _SOURCE_EXTS:
            continue

        abs_path = os.path.join(project_path, fi.path)
        try:
            with open(abs_path, encoding="utf-8", errors="ignore") as fh:
                source = fh.read()
        except OSError:
            continue

        # Extract raw edges
        ext = fi.ext.lower()
        if ext == ".py":
            raw_edges = _extract_python_dependencies(fi.path, source)
        else:
            raw_edges = _extract_regex_dependencies(fi.path, source, ext)

        # Resolve each edge
        resolved_edges: list[DependencyEdge] = []
        for edge in raw_edges:
            # Only resolve IMPORT edges (inheritance/decorator are intra-file)
            if edge.kind == DependencyKind.IMPORT:
                target_file, scope = _resolve_module_to_file(
                    edge.target_module, project_path, fi.path, ext, symbol=edge.symbol,
                )
                edge = DependencyEdge(
                    source_file=edge.source_file,
                    target_module=edge.target_module,
                    target_file=target_file,
                    kind=edge.kind,
                    scope=scope,
                    symbol=edge.symbol,
                    line_number=edge.line_number,
                )
                # Build adjacency for internal edges only
                if scope == DependencyScope.INTERNAL and target_file:
                    adjacency[fi.path].add(target_file)
                    reverse_adjacency[target_file].add(fi.path)

            resolved_edges.append(edge)

        file_edges[fi.path] = resolved_edges
        all_edges.extend(resolved_edges)

    # Ensure all known files are in adjacency maps (even if no edges)
    for fi in file_infos:
        if fi.category == FileCategory.SOURCE_CODE:
            adjacency.setdefault(fi.path, set())
            reverse_adjacency.setdefault(fi.path, set())

    # Detect cycles
    cycle_groups = _tarjan_scc(dict(adjacency))

    # Build FileDependencyInfo for each source file
    dep_infos: dict[str, FileDependencyInfo] = {}
    for fi in file_infos:
        if fi.category != FileCategory.SOURCE_CODE:
            continue

        deps = file_edges.get(fi.path, [])
        dependents_edges: list[DependencyEdge] = []
        for src in reverse_adjacency.get(fi.path, set()):
            for e in file_edges.get(src, []):
                if e.target_file == fi.path:
                    dependents_edges.append(e)

        fan_out = len(adjacency.get(fi.path, set()))
        fan_in = len(reverse_adjacency.get(fi.path, set()))

        internal_count = sum(
            1 for e in deps
            if e.kind == DependencyKind.IMPORT and e.scope == DependencyScope.INTERNAL
        )
        external_count = sum(
            1 for e in deps
            if e.kind == DependencyKind.IMPORT and e.scope == DependencyScope.EXTERNAL
        )

        dep_infos[fi.path] = FileDependencyInfo(
            file_path=fi.path,
            direct_dependencies=deps,
            direct_dependents=dependents_edges,
            fan_out=fan_out,
            fan_in=fan_in,
            internal_dependency_count=internal_count,
            external_dependency_count=external_count,
        )

    return DependencyGraph(
        edges=all_edges,
        file_infos=dep_infos,
        adjacency=dict(adjacency),
        reverse_adjacency=dict(reverse_adjacency),
        cycle_groups=cycle_groups,
        total_files=len(dep_infos),
        total_edges=len(all_edges),
    )


# ── Tarjan's SCC (iterative) ────────────────────────────────────────────────


def _tarjan_scc(adjacency: dict[str, set[str]]) -> list[set[str]]:
    """Find strongly connected components using iterative Tarjan's algorithm.

    Returns only SCCs with more than one node (actual cycles).
    """
    index_counter = [0]
    stack: list[str] = []
    on_stack: set[str] = set()
    index: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    result: list[set[str]] = []

    def strongconnect(v: str) -> None:
        # Iterative DFS using an explicit call stack
        call_stack: list[tuple[str, list[str], int]] = []
        call_stack.append((v, list(adjacency.get(v, set())), 0))
        index[v] = lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack.add(v)

        while call_stack:
            node, neighbors, i = call_stack[-1]

            if i < len(neighbors):
                call_stack[-1] = (node, neighbors, i + 1)
                w = neighbors[i]
                if w not in index:
                    index[w] = lowlink[w] = index_counter[0]
                    index_counter[0] += 1
                    stack.append(w)
                    on_stack.add(w)
                    call_stack.append((w, list(adjacency.get(w, set())), 0))
                elif w in on_stack:
                    lowlink[node] = min(lowlink[node], index[w])
            else:
                # All neighbors processed
                if lowlink[node] == index[node]:
                    scc: set[str] = set()
                    while True:
                        w = stack.pop()
                        on_stack.discard(w)
                        scc.add(w)
                        if w == node:
                            break
                    if len(scc) > 1:
                        result.append(scc)

                call_stack.pop()
                if call_stack:
                    parent = call_stack[-1][0]
                    lowlink[parent] = min(lowlink[parent], lowlink[node])

    for v in adjacency:
        if v not in index:
            strongconnect(v)

    return result


# ══════════════════════════════════════════════════════════════════════════════
# Transitive dependency counting & weight computation
# ══════════════════════════════════════════════════════════════════════════════


def _count_dependencies_by_level(
    file_path: str,
    adjacency: dict[str, set[str]],
    max_depth: int,
) -> list[int]:
    """BFS to count dependencies at each depth level.

    Returns a list where index *i* is the count of **new** dependencies
    discovered at depth ``i + 1``.  Handles cycles via a visited set.
    """
    counts: list[int] = []
    visited: set[str] = {file_path}
    current_level: set[str] = {file_path}

    for _ in range(max_depth):
        next_level: set[str] = set()
        for node in current_level:
            for neighbor in adjacency.get(node, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    next_level.add(neighbor)
        counts.append(len(next_level))
        current_level = next_level
        if not current_level:
            break

    # Pad to max_depth
    while len(counts) < max_depth:
        counts.append(0)

    return counts


def compute_dependency_weights(
    file_infos: Sequence[FileTokenInfo],
    graph: DependencyGraph,
    max_depth: int = 3,
    max_multiplier: float = 5.0,
    base_weight: float = 1.0,
    depth_decay: float = 0.5,
    depth_weights: Sequence[float] | None = None,
    internal_dependency_weight: float = 1.0,
    external_dependency_weight: float = 0.7,
    fan_in_weight: float = 0.15,
    cycle_penalty: float = 0.10,
) -> list[DependencyWeightResult]:
    """Compute dependency weight for each source file.

    Formula per file F::

        level_n_count = new deps at depth n (not counted at earlier levels)
        raw_weight = external_direct_count * external_dependency_weight
                     + SUM(n=1..max_depth) [
                         internal_level_n_count
                         * internal_dependency_weight
                         * level_weight(n)
                       ]
        dampened   = sqrt(raw_weight)
        multiplier = min(base_weight + dampened, max_multiplier)
        effective  = floor(tokens * multiplier)

    Parameters
    ----------
    file_infos:
        Token-annotated file list.
    graph:
        Pre-built dependency graph.
    max_depth:
        Maximum transitive depth to analyze (default 3).
    max_multiplier:
        Cap for the dependency multiplier (default 5.0).
    base_weight:
        Base multiplier when a file has zero dependencies (default 1.0).
    depth_decay:
        Decay factor per depth level (default 0.5).
    depth_weights:
        Explicit per-level weights overriding ``depth_decay`` when provided.
    internal_dependency_weight:
        Relative weight for project-internal dependencies.
    external_dependency_weight:
        Relative weight for project-external direct dependencies.
    fan_in_weight:
        Extra priority contribution from normalized fan-in.
    cycle_penalty:
        Fixed priority bonus applied to files participating in cycles.

    Returns
    -------
    list[DependencyWeightResult]
        One result per source file, unsorted.
    """
    results: list[DependencyWeightResult] = []
    cycle_nodes = {node for group in graph.cycle_groups for node in group}

    def level_weight(level_index: int) -> float:
        if depth_weights:
            if level_index < len(depth_weights):
                return float(depth_weights[level_index])
            return float(depth_weights[-1])
        return depth_decay ** level_index

    for fi in file_infos:
        if fi.category != FileCategory.SOURCE_CODE:
            continue

        dep_info = graph.file_infos.get(fi.path)
        if dep_info is None:
            results.append(DependencyWeightResult(
                file_path=fi.path,
                tokens=fi.tokens,
                direct_dependencies_count=0,
                direct_internal_dependencies_count=0,
                direct_external_dependencies_count=0,
                transitive_dependencies_count=0,
                dependency_depth_analyzed=max_depth,
                fan_in=0,
                fan_out=0,
                dependency_weight=base_weight,
                effective_token_size=fi.tokens,
                refactor_priority_score=0.0,
            ))
            continue

        # Count deps at each level via BFS
        level_counts = _count_dependencies_by_level(
            fi.path, graph.adjacency, max_depth,
        )

        direct_internal_count = level_counts[0] if level_counts else 0
        direct_external_count = dep_info.external_dependency_count
        direct_count = direct_internal_count + direct_external_count
        transitive_count = sum(level_counts[1:]) if len(level_counts) > 1 else 0

        # Weighted sum with explicit handling for external direct dependencies.
        raw_weight = (direct_external_count * external_dependency_weight) + sum(
            count * internal_dependency_weight * level_weight(level)
            for level, count in enumerate(level_counts)
        )

        dampened = math.sqrt(raw_weight) if raw_weight > 0 else 0.0
        multiplier = min(base_weight + dampened, max_multiplier)
        effective = math.floor(fi.tokens * multiplier)

        results.append(DependencyWeightResult(
            file_path=fi.path,
            tokens=fi.tokens,
            direct_dependencies_count=direct_count,
            direct_internal_dependencies_count=direct_internal_count,
            direct_external_dependencies_count=direct_external_count,
            transitive_dependencies_count=transitive_count,
            dependency_depth_analyzed=max_depth,
            fan_in=dep_info.fan_in,
            fan_out=dep_info.fan_out,
            dependency_weight=multiplier,
            effective_token_size=effective,
            refactor_priority_score=0.0,  # normalized below
        ))

    # Normalize priority scores
    if results:
        max_effective = max(r.effective_token_size for r in results)
        max_fan_in = max(r.fan_in for r in results)
        if max_effective > 0:
            results = [
                DependencyWeightResult(
                    file_path=r.file_path,
                    tokens=r.tokens,
                    direct_dependencies_count=r.direct_dependencies_count,
                    direct_internal_dependencies_count=r.direct_internal_dependencies_count,
                    direct_external_dependencies_count=r.direct_external_dependencies_count,
                    transitive_dependencies_count=r.transitive_dependencies_count,
                    dependency_depth_analyzed=r.dependency_depth_analyzed,
                    fan_in=r.fan_in,
                    fan_out=r.fan_out,
                    dependency_weight=r.dependency_weight,
                    effective_token_size=r.effective_token_size,
                    refactor_priority_score=min(
                        1.0,
                        (r.effective_token_size / max_effective)
                        + (
                            ((r.fan_in / max_fan_in) * fan_in_weight)
                            if max_fan_in > 0 else 0.0
                        )
                        + (cycle_penalty if r.file_path in cycle_nodes else 0.0),
                    ),
                )
                for r in results
            ]

    return results
