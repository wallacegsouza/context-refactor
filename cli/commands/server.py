"""Server-related CLI commands."""

from __future__ import annotations

from ..runtime import typer


def register_server_commands(app: typer.Typer) -> None:
    @app.command()
    def serve() -> None:
        """Start the MCP server (stdio transport)."""
        import asyncio

        from mcp_server.server import run_server

        asyncio.run(run_server())
