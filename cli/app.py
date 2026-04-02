"""CLI application factory."""

from __future__ import annotations

from .commands import register_commands
from .runtime import typer


def create_app() -> typer.Typer:
    app = typer.Typer(
        name="context-refactor",
        help="Analyse & refactor a codebase to fit inside an LLM context window.",
        add_completion=False,
    )
    register_commands(app)
    return app


app = create_app()
