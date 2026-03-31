"""Reusable Typer option and argument definitions."""

from __future__ import annotations

from typing import Any

from .runtime import typer


def project_path_argument() -> Any:
    return typer.Argument(..., help="Path to the project root.")


def context_size_option(help_text: str = "LLM context window size.") -> Any:
    return typer.Option(128_000, "--context-size", "-c", help=help_text)


def safety_margin_option(help_text: str = "Usable fraction (0-1).") -> Any:
    return typer.Option(0.80, "--safety-margin", "-s", help=help_text)


def estimator_option(help_text: str = "bytes|chars|whitespace|heuristic") -> Any:
    return typer.Option("bytes", "--estimator", "-e", help=help_text)


def output_json_option(help_text: str = "Output raw JSON instead of tables.") -> Any:
    return typer.Option(False, "--json", help=help_text)


def top_n_option(help_text: str = "Top N files to display.") -> Any:
    return typer.Option(50, "--top", "-n", help=help_text)


def profile_option() -> Any:
    return typer.Option(
        "default",
        "--profile",
        help="Analysis profile: default|full|source-only|docs",
    )


def config_path_option() -> Any:
    return typer.Option(None, "--config", help="Path to a .context-refactor.json file.")


def exclude_dirs_option() -> Any:
    return typer.Option(
        None,
        "--exclude-dirs",
        help="Comma-separated directory names or relative paths to exclude.",
    )


def exclude_globs_option() -> Any:
    return typer.Option(
        None,
        "--exclude-globs",
        help="Comma-separated glob patterns to exclude.",
    )


def exclude_files_option() -> Any:
    return typer.Option(
        None,
        "--exclude-files",
        help="Comma-separated file patterns to exclude.",
    )


def include_categories_option() -> Any:
    return typer.Option(
        None,
        "--include-categories",
        help="Comma-separated categories to include.",
    )


def exclude_categories_option() -> Any:
    return typer.Option(
        None,
        "--exclude-categories",
        help="Comma-separated categories to exclude.",
    )


def dependency_mode_option() -> Any:
    return typer.Option(None, "--dependency-mode", help="off|report_only|blended|weighted")


def dependency_max_depth_option(
    help_text: str = "Maximum dependency depth to analyze.",
) -> Any:
    return typer.Option(None, "--dependency-max-depth", help=help_text)


def dependency_max_multiplier_option() -> Any:
    return typer.Option(None, "--dependency-max-multiplier", help="Cap for the dependency multiplier.")


def dependency_base_weight_option() -> Any:
    return typer.Option(None, "--dependency-base-weight", help="Base dependency multiplier.")


def dependency_depth_decay_option() -> Any:
    return typer.Option(None, "--dependency-depth-decay", help="Geometric decay per dependency level.")


def dependency_depth_weights_option() -> Any:
    return typer.Option(
        None,
        "--dependency-depth-weights",
        help="Comma-separated explicit per-level weights.",
    )
