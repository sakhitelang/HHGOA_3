"""HH Goa–inspired terminal UI for the pipeline demo."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

console = Console()

# HH Goa palette: deep green, maize yellow, magenta accent
GREEN = "#1a4d2e"
YELLOW = "#f5c518"
PINK = "#e91e8c"
WHITE = "#f0f0f0"
MUTED = "#8a9a8e"


def print_banner():
    banner = Text()
    banner.append("╔══════════════════════════════════════════════════════════╗\n", style=f"bold {YELLOW}")
    banner.append("║  ", style=f"bold {YELLOW}")
    banner.append("HACKER HOUSE GOA", style=f"bold {YELLOW}")
    banner.append("  ·  ", style=MUTED)
    banner.append("Face ID + Blockchain Pipeline", style=f"bold {WHITE}")
    banner.append("  ║\n", style=f"bold {YELLOW}")
    banner.append("╚══════════════════════════════════════════════════════════╝", style=f"bold {YELLOW}")
    console.print(banner)
    console.print()


def print_disclosure():
    console.print(
        Panel(
            "[bold yellow]⚠  SIMULATED PIPELINE · CONSENTED TEST IMAGES ONLY[/bold yellow]\n"
            "[dim]Developer/team consented demo · No liveness detection · "
            "Hash-only verification · Simulated blockchain[/dim]",
            border_style=PINK,
            box=box.ROUNDED,
            padding=(0, 2),
        )
    )
    console.print()


def stage_header(stage: int, title: str):
    console.rule(f"[bold {YELLOW}]Stage {stage}[/bold {YELLOW}] · [bold {WHITE}]{title}[/bold {WHITE}]", style=GREEN)


def stage_ok(message: str):
    console.print(f"  [bold green]✓[/bold green] {message}")


def stage_fail(message: str):
    console.print(f"  [bold red]✗[/bold red] {message}")


def stage_info(message: str):
    console.print(f"  [dim]→[/dim] {message}")


def print_hash(label: str, value: str):
    console.print(f"  [dim]{label}:[/dim] [cyan]{value[:16]}…{value[-8:]}[/cyan]")


def print_result_table(rows: list[tuple[str, str, str]]):
    table = Table(box=box.SIMPLE, show_header=True, header_style=f"bold {YELLOW}")
    table.add_column("Field", style=MUTED)
    table.add_column("Value", style=WHITE)
    table.add_column("Status", justify="center")
    for field, value, status in rows:
        style = "bold green" if status == "PASS" else "bold red"
        table.add_row(field, value[:80] + ("…" if len(value) > 80 else ""), f"[{style}]{status}[/{style}]")
    console.print(table)


def print_verdict(passed: bool):
    if passed:
        console.print(
            Panel(
                "[bold green]VERIFICATION PASS[/bold green]\n"
                "Re-computed hash matches on-chain record.",
                border_style="green",
                box=box.DOUBLE,
                padding=(1, 4),
            )
        )
    else:
        console.print(
            Panel(
                "[bold red]VERIFICATION FAIL[/bold red]\n"
                "Re-computed hash does NOT match on-chain record.",
                border_style="red",
                box=box.DOUBLE,
                padding=(1, 4),
            )
        )
