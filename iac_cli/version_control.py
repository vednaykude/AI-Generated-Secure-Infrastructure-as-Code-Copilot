import subprocess
from typing import List, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
import os
from git import Repo, GitCommandError, InvalidGitRepositoryError

console = Console()

class GitManager:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        try:
            self.repo = Repo(repo_path)
        except InvalidGitRepositoryError:
            console.print(f"[red]Not a valid Git repository: {repo_path}[/red]")
            raise
        except Exception as e:
            console.print(f"[red]Error initializing Git repository: {e}[/red]")
            raise

    def _validate_git_installed(self) -> bool:
        """Check if Git is installed."""
        try:
            subprocess.run(['git', '--version'], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print("[red]Git is not installed or not in PATH[/red]")
            return False

    def _validate_repo_state(self) -> bool:
        """Validate repository state."""
        if not self._validate_git_installed():
            return False
            
        try:
            if self.repo.is_dirty():
                console.print("[yellow]Warning: Repository has uncommitted changes[/yellow]")
            if self.repo.untracked_files:
                console.print("[yellow]Warning: Repository has untracked files[/yellow]")
            return True
        except Exception as e:
            console.print(f"[red]Error checking repository state: {e}[/red]")
            return False

    def get_status(self) -> List[str]:
        """Get current Git status."""
        try:
            if not self._validate_repo_state():
                return []
                
            return self.repo.git.status('--porcelain').split('\n')
        except GitCommandError as e:
            console.print(f"[red]Error getting Git status: {e}[/red]")
            return []
        except Exception as e:
            console.print(f"[red]Unexpected error getting Git status: {e}[/red]")
            return []

    def get_branch(self) -> Optional[str]:
        """Get current branch name."""
        try:
            if not self._validate_repo_state():
                return None
                
            return self.repo.active_branch.name
        except GitCommandError as e:
            console.print(f"[red]Error getting branch name: {e}[/red]")
            return None
        except Exception as e:
            console.print(f"[red]Unexpected error getting branch name: {e}[/red]")
            return None

    def create_branch(self, branch_name: str) -> bool:
        """Create a new branch."""
        try:
            if not self._validate_repo_state():
                return False
                
            if branch_name in [b.name for b in self.repo.branches]:
                console.print(f"[red]Branch {branch_name} already exists[/red]")
                return False
                
            self.repo.git.checkout('-b', branch_name)
            console.print(f"[green]Created and switched to branch: {branch_name}[/green]")
            return True
        except GitCommandError as e:
            console.print(f"[red]Error creating branch: {e}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Unexpected error creating branch: {e}[/red]")
            return False

    def commit_changes(self, message: str) -> bool:
        """Commit changes with a message."""
        try:
            if not self._validate_repo_state():
                return False
                
            if not self.repo.is_dirty() and not self.repo.untracked_files:
                console.print("[yellow]No changes to commit[/yellow]")
                return False
                
            self.repo.git.add(A=True)
            self.repo.git.commit('-m', message)
            console.print("[green]Changes committed successfully[/green]")
            return True
        except GitCommandError as e:
            console.print(f"[red]Error committing changes: {e}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Unexpected error committing changes: {e}[/red]")
            return False

    def push_changes(self, branch: Optional[str] = None) -> bool:
        """Push changes to remote repository."""
        try:
            if not self._validate_repo_state():
                return False
                
            if not self.repo.remotes:
                console.print("[red]No remote repository configured[/red]")
                return False
                
            branch = branch or self.repo.active_branch.name
            self.repo.git.push('origin', branch)
            console.print(f"[green]Changes pushed to {branch}[/green]")
            return True
        except GitCommandError as e:
            console.print(f"[red]Error pushing changes: {e}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Unexpected error pushing changes: {e}[/red]")
            return False

    def create_pull_request(self, title: str, body: str) -> bool:
        """Create a pull request using GitHub CLI."""
        try:
            if not self._validate_repo_state():
                return False
                
            # Check if GitHub CLI is installed
            try:
                subprocess.run(['gh', '--version'], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                console.print("[red]GitHub CLI (gh) is not installed[/red]")
                return False
                
            # Create PR using GitHub CLI
            result = subprocess.run(
                ['gh', 'pr', 'create', '--title', title, '--body', body],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            console.print(f"[green]Pull request created: {result.stdout.strip()}[/green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error creating pull request: {e.stderr}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Unexpected error creating pull request: {e}[/red]")
            return False

    def get_diff(self) -> Optional[str]:
        """Get current diff."""
        try:
            if not self._validate_repo_state():
                return None
                
            return self.repo.git.diff()
        except GitCommandError as e:
            console.print(f"[red]Error getting diff: {e}[/red]")
            return None
        except Exception as e:
            console.print(f"[red]Unexpected error getting diff: {e}[/red]")
            return None

    def display_status(self) -> None:
        """Display current Git status in a formatted table."""
        try:
            if not self._validate_repo_state():
                return
                
            status = self.get_status()
            if not status:
                console.print(Panel("No changes in repository", title="Git Status"))
                return

            table = Table(title="Git Status")
            table.add_column("Status")
            table.add_column("File")
            
            for item in status:
                if item:  # Skip empty lines
                    status_code = item[:2]
                    file_path = item[3:]
                    table.add_row(status_code, file_path)
            
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error displaying status: {e}[/red]") 