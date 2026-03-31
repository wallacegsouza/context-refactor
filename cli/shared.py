"""Helpers shared across CLI command modules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .runtime import Panel, console, typer


def resolve_path(project_path: str) -> str:
    path = Path(project_path).resolve()
    if not path.is_dir():
        console.print(f"[red]Error:[/] {path} is not a directory.")
        raise typer.Exit(1)
    return str(path)


def print_json(data: dict[str, Any]) -> None:
    console.print_json(json.dumps(data, indent=2, ensure_ascii=False))


def human(number: int) -> str:
    return f"{number:,}"


def csv_to_list(value: str | None) -> list[str] | None:
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def csv_to_float_list(value: str | None) -> list[float] | None:
    items = csv_to_list(value)
    if not items:
        return None
    return [float(item) for item in items]


def analysis_options(
    profile: str,
    config_path: str | None,
    exclude_dirs: str | None,
    exclude_globs: str | None,
    exclude_files: str | None,
    include_categories: str | None,
    exclude_categories: str | None,
) -> dict[str, object]:
    return {
        "analysis_profile": profile,
        "config_path": config_path,
        "exclude_dirs": csv_to_list(exclude_dirs),
        "exclude_globs": csv_to_list(exclude_globs),
        "exclude_files": csv_to_list(exclude_files),
        "include_categories": csv_to_list(include_categories),
        "exclude_categories": csv_to_list(exclude_categories),
    }


def dependency_options(
    mode: str | None,
    max_depth: int | None,
    max_multiplier: float | None,
    base_weight: float | None,
    depth_decay: float | None,
    depth_weights: str | None,
) -> dict[str, object]:
    return {
        "dependency_mode": mode,
        "dependency_max_depth": max_depth,
        "dependency_max_multiplier": max_multiplier,
        "dependency_base_weight": base_weight,
        "dependency_depth_decay": depth_decay,
        "dependency_depth_weights": csv_to_float_list(depth_weights),
    }


def print_analysis_scope(result: dict[str, Any]) -> None:
    scope = result.get("analysis_scope") or {}
    if not scope:
        return

    include_categories = ", ".join(scope.get("include_categories") or []) or "all"
    exclude_categories = ", ".join(scope.get("exclude_categories") or []) or "none"
    exclude_dirs = ", ".join(scope.get("exclude_dirs") or []) or "none"
    exclude_globs = ", ".join(scope.get("exclude_globs") or []) or "none"
    exclude_files = ", ".join(scope.get("exclude_files") or []) or "none"
    category_counts = result.get("category_counts") or {}
    category_tokens = result.get("category_tokens") or {}
    noise_summary = result.get("noise_summary") or {}
    signal_score = result.get("signal_score") or {}
    category_lines: list[str] = []
    for category in sorted(category_counts):
        category_lines.append(
            f"{category}: {human(category_counts[category])} files / {human(category_tokens.get(category, 0))} tokens"
        )

    body = (
        f"[bold]Profile:[/] {scope.get('profile', 'default')}\n"
        f"[bold]Config:[/] {scope.get('config_path') or 'none'}\n"
        f"[bold]Include categories:[/] {include_categories}\n"
        f"[bold]Exclude categories:[/] {exclude_categories}\n"
        f"[bold]Exclude dirs:[/] {exclude_dirs}\n"
        f"[bold]Exclude globs:[/] {exclude_globs}\n"
        f"[bold]Exclude files:[/] {exclude_files}"
    )
    if category_lines:
        body += "\n[bold]Category mix:[/] " + " | ".join(category_lines)

    if noise_summary:
        body += (
            "\n[bold]Noise summary:[/] "
            f"scanner={human(noise_summary.get('scanner_files', 0))} files / {human(noise_summary.get('scanner_tokens', 0))} tokens"
            f" -> after filters={human(noise_summary.get('files_after_filters', 0))} files / {human(noise_summary.get('tokens_after_filters', 0))} tokens"
            f" | filtered_by_category={human(noise_summary.get('filtered_by_category_files', 0))} files"
            f" ({noise_summary.get('file_reduction_ratio', 0.0):.1%})"
        )

    if signal_score:
        body += (
            "\n[bold]Signal score:[/] "
            f"{signal_score.get('value', 0)} / 100"
            f" | noise_ratio={signal_score.get('noise_ratio', 0.0):.1%}"
            f" | method={signal_score.get('method', '-')}"
        )

    console.print(Panel(body, title="Analysis Scope", border_style="blue"))


def print_dependency_summary(result: dict[str, Any]) -> None:
    dependency = result.get("dependency_analysis") or {}
    if not dependency.get("enabled"):
        return

    effective_tokens = dependency.get("effective_tokens")
    details = (
        f"[bold]Mode:[/] {dependency.get('mode', 'off')}\n"
        f"[bold]Max depth:[/] {dependency.get('max_depth', '-')}\n"
        f"[bold]Edges:[/] {human(int(dependency.get('dependency_edges', 0) or 0))}\n"
        f"[bold]Cycle groups:[/] {human(int(dependency.get('cycle_groups', 0) or 0))}"
    )
    if effective_tokens is not None:
        details += f"\n[bold]Effective tokens:[/] {human(int(effective_tokens))}"

    console.print(Panel(details, title="Dependency Analysis", border_style="magenta"))
