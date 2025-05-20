import time
from typing import Callable, Dict, List, Optional
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from pathlib import Path
import json

console = Console()

class FeedbackManager:
    def __init__(self):
        self.console = Console()
        self.last_update = time.time()
        self.update_interval = 1.0  # seconds

    def display_live_validation(self, validator_func: Callable, file_path: Path) -> None:
        """Display live validation feedback."""
        with Live(
            Panel("Starting validation...", title="Live Validation"),
            refresh_per_second=4
        ) as live:
            while True:
                errors = validator_func(file_path)
                
                if not errors:
                    live.update(Panel(
                        "[green]No validation errors found![/green]",
                        title="Live Validation"
                    ))
                    break
                
                table = Table(title="Validation Errors")
                table.add_column("Line")
                table.add_column("Message")
                
                for error in errors:
                    table.add_row(
                        str(error.get('line', 'N/A')),
                        error.get('message', 'Unknown error')
                    )
                
                live.update(Panel(table, title="Live Validation"))
                time.sleep(self.update_interval)

    def display_live_cost_estimation(self, estimator_func: Callable, plan_path: Path) -> None:
        """Display live cost estimation feedback."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Estimating costs...", total=None)
            
            costs = estimator_func(plan_path)
            
            table = Table(title="Estimated Costs")
            table.add_column("Resource")
            table.add_column("Cost")
            
            total_cost = 0.0
            for cost in costs:
                table.add_row(
                    cost.resource_name,
                    f"${cost.estimated_cost:.2f}"
                )
                total_cost += cost.estimated_cost
            
            table.add_row("Total", f"${total_cost:.2f}")
            
            self.console.print(table)

    def display_live_plan(self, plan_func: Callable, file_path: Path) -> None:
        """Display live Terraform plan feedback."""
        with Live(
            Panel("Generating plan...", title="Live Plan"),
            refresh_per_second=4
        ) as live:
            while True:
                plan = plan_func(file_path)
                
                if not plan:
                    live.update(Panel(
                        "[yellow]No changes required.[/yellow]",
                        title="Live Plan"
                    ))
                    break
                
                table = Table(title="Plan Changes")
                table.add_column("Resource")
                table.add_column("Action")
                
                for change in plan.get('resource_changes', []):
                    table.add_row(
                        f"{change['type']}.{change['name']}",
                        ', '.join(change['change']['actions'])
                    )
                
                live.update(Panel(table, title="Live Plan"))
                time.sleep(self.update_interval)

    def display_live_security_scan(self, scanner_func: Callable, file_path: Path) -> None:
        """Display live security scanning feedback."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Scanning for security issues...", total=None)
            
            issues = scanner_func(file_path)
            
            if not issues:
                self.console.print(Panel(
                    "[green]No security issues found![/green]",
                    title="Security Scan"
                ))
                return
            
            table = Table(title="Security Issues")
            table.add_column("Severity")
            table.add_column("Message")
            table.add_column("Resource")
            
            for issue in issues:
                table.add_row(
                    issue.get('severity', 'N/A'),
                    issue.get('message', 'Unknown issue'),
                    issue.get('resource', 'N/A')
                )
            
            self.console.print(table)

    def display_live_git_status(self, git_func: Callable) -> None:
        """Display live git status feedback."""
        with Live(
            Panel("Checking git status...", title="Git Status"),
            refresh_per_second=4
        ) as live:
            while True:
                status = git_func()
                
                if not status:
                    live.update(Panel(
                        "[green]Working directory is clean[/green]",
                        title="Git Status"
                    ))
                    break
                
                table = Table(title="Git Status")
                table.add_column("Status")
                table.add_column("File")
                
                for item in status:
                    if item:
                        status_code, file_path = item.split(' ', 1)
                        table.add_row(status_code, file_path)
                
                live.update(Panel(table, title="Git Status"))
                time.sleep(self.update_interval) 