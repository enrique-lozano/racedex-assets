"""What the scripts print: colors, progress bars and tables, with rich

The colors are off when the output is not a terminal (a file, a pipe) or when NO_COLOR is set.
"""

import sys
from typing import NoReturn

from rich.console import Console
from rich.markup import escape
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

try:
    sys.stdout.reconfigure(encoding='utf-8')  # the console of Windows can't print every name
except (AttributeError, ValueError):
    pass

console = Console(highlight=False)
error_console = Console(stderr=True, highlight=False)

# Plain symbols if the terminal can't show the nice ones
_fancy = 'utf' in (console.encoding or '').lower() and not console.options.legacy_windows
OK, INFO, WARN, FAIL = ('✓', '•', '!', '✗') if _fancy else ('+', '-', '!', 'x')


def ok(message: str) -> None:
    console.print(f'[green]{OK}[/green] {escape(message)}')


def info(message: str) -> None:
    console.print(f'[cyan]{INFO}[/cyan] {escape(message)}')


def warn(message: str) -> None:
    console.print(f'[yellow]{WARN}[/yellow] {escape(message)}')


def fail(message: str) -> NoReturn:
    error_console.print(f'[red]{FAIL}[/red] {escape(message)}')
    sys.exit(1)


def progress() -> Progress:
    """A progress bar. Add a task with `add_task(description, total=n, found='')` and update its `found` text"""
    return Progress(
        SpinnerColumn(),
        TextColumn('{task.description}', table_column=None),
        BarColumn(bar_width=30),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TextColumn('{task.fields[found]}'),
        console=console,
    )


def table(*columns: str) -> Table:
    result = Table(box=None, pad_edge=False, header_style='bold')
    for column in columns:
        result.add_column(column, overflow='fold')
    return result
