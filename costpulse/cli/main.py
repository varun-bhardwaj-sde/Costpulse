"""Command-line interface for CostPulse."""

import asyncio
import csv
import json
import os
import sys
import time
from typing import List, Dict, Any

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
@click.version_option()
def cli() -> None:
    """CostPulse - Real-time Databricks Cost Intelligence."""
    pass


@cli.group()
def config() -> None:
    """Configuration management."""
    pass


@config.command()
def init() -> None:
    """Initialize CostPulse configuration."""
    from costpulse.core.config import settings

    console.print("[bold green]CostPulse Configuration[/bold green]\n")

    # Check if .env exists and warn before overwriting
    if os.path.exists(".env"):
        if not click.confirm(
            ".env file already exists. Overwrite?", default=False
        ):
            console.print("[yellow]Configuration initialization cancelled.[/yellow]")
            return

    host = click.prompt("Databricks Host URL", default=settings.databricks.host or "")
    token = click.prompt("Databricks Token", hide_input=True)

    # Save to .env file
    try:
        with open(".env", "w") as f:
            f.write(f"DATABRICKS_HOST={host}\n")
            f.write(f"DATABRICKS_TOKEN={token}\n")
    except IOError as e:
        console.print(f"[red]Failed to write .env file: {e}[/red]")
        return

    console.print("\n[green]✓ Configuration saved to .env[/green]")


@cli.group()
def query() -> None:
    """Query cost data."""
    pass


@query.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
def today(format: str) -> None:
    """Get today's costs."""
    from costpulse.collectors.system_tables import SystemTablesCollector
    from costpulse.core.config import settings

    async def _get_costs() -> List[Dict[str, Any]]:
        collector = SystemTablesCollector(
            host=settings.databricks.host, token=settings.databricks.token
        )
        return await collector.run()

    data = asyncio.run(_get_costs())

    if format == "table":
        _display_table(data)
    elif format == "json":
        click.echo(json.dumps(data, default=str, indent=2))
    else:
        _display_csv(data)


def _display_table(data: List[Dict[str, Any]]) -> None:
    """Display data as Rich table.

    Args:
        data: List of cost records
    """
    table = Table(title="Today's Databricks Costs")

    table.add_column("Workspace", style="cyan")
    table.add_column("SKU", style="green")
    table.add_column("DBUs", justify="right")
    table.add_column("Cost (USD)", justify="right", style="yellow")

    total_cost = 0.0
    for row in data:
        cost = row.get("cost_usd", 0)
        total_cost += cost
        table.add_row(
            str(row.get("workspace_id", ""))[:20],
            row.get("sku_name", ""),
            f"{row.get('dbu_count', 0):.2f}",
            f"${cost:.2f}",
        )

    table.add_section()
    table.add_row("", "", "[bold]TOTAL[/bold]", f"[bold]${total_cost:.2f}[/bold]")

    console.print(table)


def _display_csv(data: List[Dict[str, Any]]) -> None:
    """Display data as CSV.

    Args:
        data: List of cost records
    """
    if not data:
        return

    writer = csv.DictWriter(sys.stdout, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)


@cli.command()
@click.option("--refresh", "-r", default=30, help="Refresh interval in seconds")
def watch(refresh: int) -> None:
    """Watch costs in real-time."""
    from costpulse.collectors.system_tables import SystemTablesCollector
    from costpulse.core.config import settings

    console.print(f"[bold]Watching costs (refresh every {refresh}s)...[/bold]")
    console.print("Press Ctrl+C to stop\n")

    async def _watch() -> None:
        collector = SystemTablesCollector(
            host=settings.databricks.host, token=settings.databricks.token
        )

        while True:
            try:
                data = await collector.run()
                console.clear()
                _display_table(data)
                console.print(f"\n[dim]Last updated: {time.strftime('%H:%M:%S')}[/dim]")
                await asyncio.sleep(refresh)
            except KeyboardInterrupt:
                break

    asyncio.run(_watch())


if __name__ == "__main__":
    cli()
