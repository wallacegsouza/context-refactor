"""Tests for dependency graph building and weight computation."""

from __future__ import annotations

from pathlib import Path

from context_refactor.dependency_analyzer import (
    build_dependency_graph,
    compute_dependency_weights,
)
from context_refactor.models import FileCategory, FileTokenInfo


def _source_file(path: str, tokens: int = 100) -> FileTokenInfo:
    return FileTokenInfo(
        path=path,
        ext=Path(path).suffix,
        tokens=tokens,
        bytes_=tokens * 4,
        chars=tokens * 4,
        category=FileCategory.SOURCE_CODE,
    )


def test_build_dependency_graph_resolves_internal_and_external_python_imports(
    tmp_path: Path,
) -> None:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pkg" / "b.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "a.py").write_text(
        "import json\nfrom pkg import b\n\nprint(b.VALUE)\n",
        encoding="utf-8",
    )

    file_infos = [
        _source_file("a.py"),
        _source_file("pkg/__init__.py"),
        _source_file("pkg/b.py"),
    ]

    graph = build_dependency_graph(file_infos, str(tmp_path))

    a_info = graph.file_infos["a.py"]
    assert graph.adjacency["a.py"] == {"pkg/b.py"}
    assert a_info.internal_dependency_count == 1
    assert a_info.external_dependency_count == 1
    assert a_info.fan_out == 1
    assert graph.total_files == 3


def test_build_dependency_graph_detects_cycles(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("import b\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("import a\n", encoding="utf-8")

    file_infos = [
        _source_file("a.py"),
        _source_file("b.py"),
    ]

    graph = build_dependency_graph(file_infos, str(tmp_path))

    assert {"a.py", "b.py"} in graph.cycle_groups


def test_compute_dependency_weights_counts_transitive_dependencies(
    tmp_path: Path,
) -> None:
    (tmp_path / "a.py").write_text("import json\nimport b\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("import c\n", encoding="utf-8")
    (tmp_path / "c.py").write_text("VALUE = 42\n", encoding="utf-8")

    file_infos = [
        _source_file("a.py", tokens=120),
        _source_file("b.py", tokens=90),
        _source_file("c.py", tokens=60),
    ]

    graph = build_dependency_graph(file_infos, str(tmp_path))
    results = compute_dependency_weights(file_infos, graph, max_depth=3)
    by_path = {result.file_path: result for result in results}

    a_result = by_path["a.py"]
    assert a_result.direct_dependencies_count == 2
    assert a_result.direct_internal_dependencies_count == 1
    assert a_result.direct_external_dependencies_count == 1
    assert a_result.transitive_dependencies_count == 1
    assert a_result.effective_token_size > a_result.tokens
    assert a_result.refactor_priority_score > 0.0
