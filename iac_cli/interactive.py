from typing import Dict, List, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from pathlib import Path
import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

console = Console()

class InteractiveMode:
    def __init__(self):
        self.console = Console()
        self.session = PromptSession()
        self.commands = {
            'validate': self.validate_command,
            'plan': self.plan_command,
            'apply': self.apply_command,
            'cost': self.cost_command,
            'security': self.security_command,
            'git': self.git_command,
            'help': self.help_command,
            'exit': self.exit_command
        }
        self.command_completer = WordCompleter(list(self.commands.keys()))

    def start(self) -> None:
        """Start the interactive mode."""
        self.console.print(Panel(
            "[bold blue]Welcome to IAC CLI Interactive Mode[/bold blue]\n"
            "Type 'help' for available commands or 'exit' to quit.",
            title="Interactive Mode"
        ))
        
        while True:
            try:
                command = self.session.prompt(
                    "iac-cli> ",
                    completer=self.command_completer
                ).strip()
                
                if not command:
                    continue
                
                if command in self.commands:
                    self.commands[command]()
                else:
                    self.console.print(f"[red]Unknown command: {command}[/red]")
            
            except KeyboardInterrupt:
                continue
            except EOFError:
                break

    def validate_command(self) -> None:
        """Handle validate command."""
        file_path = Prompt.ask("Enter Terraform file path")
        if not Path(file_path).exists():
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        # Call validation logic here
        self.console.print("[yellow]Running validation...[/yellow]")

    def plan_command(self) -> None:
        """Handle plan command."""
        file_path = Prompt.ask("Enter Terraform file path")
        if not Path(file_path).exists():
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        # Call plan logic here
        self.console.print("[yellow]Generating plan...[/yellow]")

    def apply_command(self) -> None:
        """Handle apply command."""
        if not Confirm.ask("Are you sure you want to apply changes?"):
            return
        
        file_path = Prompt.ask("Enter Terraform file path")
        if not Path(file_path).exists():
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        # Call apply logic here
        self.console.print("[yellow]Applying changes...[/yellow]")

    def cost_command(self) -> None:
        """Handle cost estimation command."""
        file_path = Prompt.ask("Enter Terraform file path")
        if not Path(file_path).exists():
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        # Call cost estimation logic here
        self.console.print("[yellow]Estimating costs...[/yellow]")

    def security_command(self) -> None:
        """Handle security scan command."""
        file_path = Prompt.ask("Enter Terraform file path")
        if not Path(file_path).exists():
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        # Call security scan logic here
        self.console.print("[yellow]Running security scan...[/yellow]")

    def git_command(self) -> None:
        """Handle git operations."""
        git_commands = {
            'status': self.git_status,
            'commit': self.git_commit,
            'push': self.git_push,
            'pr': self.git_pr
        }
        
        command = Prompt.ask(
            "Git command",
            choices=list(git_commands.keys())
        )
        
        git_commands[command]()

    def git_status(self) -> None:
        """Show git status."""
        # Call git status logic here
        self.console.print("[yellow]Checking git status...[/yellow]")

    def git_commit(self) -> None:
        """Create a git commit."""
        message = Prompt.ask("Commit message")
        # Call git commit logic here
        self.console.print("[yellow]Creating commit...[/yellow]")

    def git_push(self) -> None:
        """Push changes to remote."""
        # Call git push logic here
        self.console.print("[yellow]Pushing changes...[/yellow]")

    def git_pr(self) -> None:
        """Create a pull request."""
        title = Prompt.ask("PR title")
        body = Prompt.ask("PR description")
        # Call git PR logic here
        self.console.print("[yellow]Creating pull request...[/yellow]")

    def help_command(self) -> None:
        """Show help information."""
        table = Table(title="Available Commands")
        table.add_column("Command")
        table.add_column("Description")
        
        table.add_row("validate", "Validate Terraform files")
        table.add_row("plan", "Generate Terraform plan")
        table.add_row("apply", "Apply Terraform changes")
        table.add_row("cost", "Estimate infrastructure costs")
        table.add_row("security", "Run security scan")
        table.add_row("git", "Git operations")
        table.add_row("help", "Show this help message")
        table.add_row("exit", "Exit interactive mode")
        
        self.console.print(table)

    def exit_command(self) -> None:
        """Exit interactive mode."""
        if Confirm.ask("Are you sure you want to exit?"):
            raise EOFError() 