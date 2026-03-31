"""CLI command registration."""

from __future__ import annotations

from ..runtime import typer
from .analysis import register_analysis_commands
from .heuristics import register_heuristics_commands
from .server import register_server_commands


def register_commands(app: typer.Typer) -> None:
    register_analysis_commands(app)
    register_heuristics_commands(app)
    register_server_commands(app)
