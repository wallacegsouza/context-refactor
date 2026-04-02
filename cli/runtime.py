"""Runtime imports shared by the CLI modules."""

from __future__ import annotations

import sys

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError as err:
    sys.stderr.write(
        "typer and rich are required for the CLI. Install with:\n"
        "  pip install typer[all]\n"
    )
    raise SystemExit(1) from err

console = Console()

__all__ = ["Console", "Panel", "Table", "console", "typer"]
