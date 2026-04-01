"""Dependency graph construction helpers."""

from __future__ import annotations

import os
from collections import defaultdict
from collections.abc import Sequence

from .dependency_extraction import extract_dependency_edges
from .dependency_resolution import resolve_module_to_file
from .models import (
    DependencyEdge,
    DependencyGraph,
    DependencyKind,
    DependencyScope,
    FileCategory,
    FileDependencyInfo,
    FileTokenInfo,
)

_SOURCE_EXTS: frozenset[str] = frozenset(
    {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".kt",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".cs",
        ".cpp",
        ".cc",
        ".cxx",
        ".c",
        ".h",
        ".hpp",
        ".swift",
        ".scala",
        ".lua",
        ".sh",
        ".bash",
        ".zsh",
    }
)


def build_dependency_graph(
    file_infos: Sequence[FileTokenInfo],
    project_path: str,
) -> DependencyGraph:
    """Build a project-wide dependency graph from source files."""
    all_edges: list[DependencyEdge] = []
    adjacency: dict[str, set[str]] = defaultdict(set)
    reverse_adjacency: dict[str, set[str]] = defaultdict(set)
    file_edges: dict[str, list[DependencyEdge]] = defaultdict(list)

    for file_info in file_infos:
        if file_info.category != FileCategory.SOURCE_CODE:
            continue
        if file_info.ext.lower() not in _SOURCE_EXTS:
            continue

        abs_path = os.path.join(project_path, file_info.path)
        try:
            with open(abs_path, encoding="utf-8", errors="ignore") as handle:
                source = handle.read()
        except OSError:
            continue

        ext = file_info.ext.lower()
        raw_edges = extract_dependency_edges(file_info.path, source, ext)
        resolved_edges = _resolve_edges(raw_edges, file_info.path, project_path, ext, adjacency, reverse_adjacency)
        file_edges[file_info.path] = resolved_edges
        all_edges.extend(resolved_edges)

    for file_info in file_infos:
        if file_info.category == FileCategory.SOURCE_CODE:
            adjacency.setdefault(file_info.path, set())
            reverse_adjacency.setdefault(file_info.path, set())

    cycle_groups = _tarjan_scc(dict(adjacency))
    dep_infos = _build_file_dependency_infos(file_infos, file_edges, adjacency, reverse_adjacency)

    return DependencyGraph(
        edges=all_edges,
        file_infos=dep_infos,
        adjacency=dict(adjacency),
        reverse_adjacency=dict(reverse_adjacency),
        cycle_groups=cycle_groups,
        total_files=len(dep_infos),
        total_edges=len(all_edges),
    )


def _resolve_edges(
    raw_edges: list[DependencyEdge],
    file_path: str,
    project_path: str,
    ext: str,
    adjacency: dict[str, set[str]],
    reverse_adjacency: dict[str, set[str]],
) -> list[DependencyEdge]:
    resolved_edges: list[DependencyEdge] = []
    for edge in raw_edges:
        if edge.kind == DependencyKind.IMPORT:
            target_file, scope = resolve_module_to_file(
                edge.target_module,
                project_path,
                file_path,
                ext,
                symbol=edge.symbol,
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
            if scope == DependencyScope.INTERNAL and target_file:
                adjacency[file_path].add(target_file)
                reverse_adjacency[target_file].add(file_path)

        resolved_edges.append(edge)
    return resolved_edges


def _build_file_dependency_infos(
    file_infos: Sequence[FileTokenInfo],
    file_edges: dict[str, list[DependencyEdge]],
    adjacency: dict[str, set[str]],
    reverse_adjacency: dict[str, set[str]],
) -> dict[str, FileDependencyInfo]:
    dep_infos: dict[str, FileDependencyInfo] = {}

    for file_info in file_infos:
        if file_info.category != FileCategory.SOURCE_CODE:
            continue

        deps = file_edges.get(file_info.path, [])
        dependents_edges: list[DependencyEdge] = []
        for source in reverse_adjacency.get(file_info.path, set()):
            for edge in file_edges.get(source, []):
                if edge.target_file == file_info.path:
                    dependents_edges.append(edge)

        internal_count = sum(
            1
            for edge in deps
            if edge.kind == DependencyKind.IMPORT and edge.scope == DependencyScope.INTERNAL
        )
        external_count = sum(
            1
            for edge in deps
            if edge.kind == DependencyKind.IMPORT and edge.scope == DependencyScope.EXTERNAL
        )

        dep_infos[file_info.path] = FileDependencyInfo(
            file_path=file_info.path,
            direct_dependencies=deps,
            direct_dependents=dependents_edges,
            fan_out=len(adjacency.get(file_info.path, set())),
            fan_in=len(reverse_adjacency.get(file_info.path, set())),
            internal_dependency_count=internal_count,
            external_dependency_count=external_count,
        )

    return dep_infos


def _tarjan_scc(adjacency: dict[str, set[str]]) -> list[set[str]]:
    """Find strongly connected components using iterative Tarjan's algorithm."""
    index_counter = [0]
    stack: list[str] = []
    on_stack: set[str] = set()
    index: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    result: list[set[str]] = []

    def strongconnect(node: str) -> None:
        call_stack: list[tuple[str, list[str], int]] = []
        call_stack.append((node, list(adjacency.get(node, set())), 0))
        index[node] = lowlink[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)
        on_stack.add(node)

        while call_stack:
            current, neighbors, current_index = call_stack[-1]

            if current_index < len(neighbors):
                call_stack[-1] = (current, neighbors, current_index + 1)
                neighbor = neighbors[current_index]
                if neighbor not in index:
                    index[neighbor] = lowlink[neighbor] = index_counter[0]
                    index_counter[0] += 1
                    stack.append(neighbor)
                    on_stack.add(neighbor)
                    call_stack.append((neighbor, list(adjacency.get(neighbor, set())), 0))
                elif neighbor in on_stack:
                    lowlink[current] = min(lowlink[current], index[neighbor])
            else:
                if lowlink[current] == index[current]:
                    scc: set[str] = set()
                    while True:
                        member = stack.pop()
                        on_stack.discard(member)
                        scc.add(member)
                        if member == current:
                            break
                    if len(scc) > 1:
                        result.append(scc)

                call_stack.pop()
                if call_stack:
                    parent = call_stack[-1][0]
                    lowlink[parent] = min(lowlink[parent], lowlink[current])

    for node in adjacency:
        if node not in index:
            strongconnect(node)

    return result
