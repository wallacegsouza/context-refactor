"""CLI entry point for ContextRefactor."""

from __future__ import annotations

from .app import app


def main() -> None:
    app()


if __name__ == "__main__":
    main()
