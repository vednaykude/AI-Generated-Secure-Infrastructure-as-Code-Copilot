import yaml
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
import os
import subprocess
import json

console = Console()

class CICDManager:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.workflows_dir = repo_path / '.github' / 'workflows'
        self._validate_setup()

    def _validate_setup(self) -> bool:
        """Validate CI/CD setup."""
        try:
            # Check if .github/workflows directory exists
            if not self.workflows_dir.exists():
                self.workflows_dir.mkdir(parents=True, exist_ok=True)
                console.print(f"[yellow]Created workflows directory: {self.workflows_dir}[/yellow]")

            # Check if GitHub CLI is installed
            try:
                subprocess.run(['gh', '--version'], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                console.print("[yellow]Warning: GitHub CLI (gh) is not installed. Some features may be limited.[/yellow]")

            # Check GitHub authentication
            try:
                subprocess.run(['gh', 'auth', 'status'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                console.print("[yellow]Warning: GitHub CLI is not authenticated. Some features may be limited.[/yellow]")

            return True
        except Exception as e:
            console.print(f"[red]Error validating CI/CD setup: {e}[/red]")
            return False

    def _validate_workflow_syntax(self, workflow_content: Dict) -> bool:
        """Validate workflow YAML syntax."""
        try:
            # Basic validation of required fields
            required_fields = ['name', 'on', 'jobs']
            for field in required_fields:
                if field not in workflow_content:
                    console.print(f"[red]Missing required field in workflow: {field}[/red]")
                    return False

            # Validate job structure
            for job_name, job in workflow_content['jobs'].items():
                if 'runs-on' not in job:
                    console.print(f"[red]Missing 'runs-on' in job: {job_name}[/red]")
                    return False
                if 'steps' not in job:
                    console.print(f"[red]Missing 'steps' in job: {job_name}[/red]")
                    return False

            return True
        except Exception as e:
            console.print(f"[red]Error validating workflow syntax: {e}[/red]")
            return False

    def create_workflow(self, name: str, content: Dict) -> bool:
        """Create a GitHub Actions workflow file."""
        try:
            if not self._validate_setup():
                return False

            if not self._validate_workflow_syntax(content):
                return False

            workflow_file = self.workflows_dir / f"{name}.yml"
            
            # Check if workflow already exists
            if workflow_file.exists():
                if not typer.confirm(f"Workflow {name} already exists. Overwrite?"):
                    return False

            # Write workflow file
            with open(workflow_file, 'w') as f:
                yaml.dump(content, f, default_flow_style=False)

            console.print(f"[green]Created workflow: {workflow_file}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error creating workflow: {e}[/red]")
            return False

    def create_terraform_workflow(self) -> bool:
        """Create a standard Terraform workflow."""
        workflow = {
            'name': 'Terraform',
            'on': {
                'push': {
                    'paths': ['**/*.tf']
                },
                'pull_request': {
                    'paths': ['**/*.tf']
                }
            },
            'jobs': {
                'terraform': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [
                        {
                            'name': 'Checkout',
                            'uses': 'actions/checkout@v2'
                        },
                        {
                            'name': 'Setup Terraform',
                            'uses': 'hashicorp/setup-terraform@v1'
                        },
                        {
                            'name': 'Terraform Init',
                            'run': 'terraform init'
                        },
                        {
                            'name': 'Terraform Validate',
                            'run': 'terraform validate'
                        },
                        {
                            'name': 'Terraform Plan',
                            'run': 'terraform plan'
                        }
                    ]
                }
            }
        }
        return self.create_workflow('terraform', workflow)

    def create_security_workflow(self) -> bool:
        """Create a security scanning workflow."""
        workflow = {
            'name': 'Security Scan',
            'on': {
                'push': {
                    'branches': ['main']
                },
                'pull_request': {
                    'branches': ['main']
                }
            },
            'jobs': {
                'security': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [
                        {
                            'name': 'Checkout',
                            'uses': 'actions/checkout@v2'
                        },
                        {
                            'name': 'Run tfsec',
                            'uses': 'aquasecurity/tfsec-action@v1.0.0'
                        },
                        {
                            'name': 'Run Checkov',
                            'uses': 'bridgecrewio/checkov-action@master'
                        }
                    ]
                }
            }
        }
        return self.create_workflow('security', workflow)

    def create_cost_workflow(self) -> bool:
        """Create a cost estimation workflow."""
        workflow = {
            'name': 'Cost Estimation',
            'on': {
                'pull_request': {
                    'paths': ['**/*.tf']
                }
            },
            'jobs': {
                'cost': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [
                        {
                            'name': 'Checkout',
                            'uses': 'actions/checkout@v2'
                        },
                        {
                            'name': 'Setup Python',
                            'uses': 'actions/setup-python@v2',
                            'with': {
                                'python-version': '3.8'
                            }
                        },
                        {
                            'name': 'Install Dependencies',
                            'run': 'pip install iac-cli'
                        },
                        {
                            'name': 'Estimate Costs',
                            'run': 'iac-cli estimate-costs . --optimize'
                        }
                    ]
                }
            }
        }
        return self.create_workflow('cost', workflow)

    def list_workflows(self) -> List[Path]:
        """List all available workflows."""
        try:
            if not self._validate_setup():
                return []

            if not self.workflows_dir.exists():
                return []

            return list(self.workflows_dir.glob('*.yml'))
        except Exception as e:
            console.print(f"[red]Error listing workflows: {e}[/red]")
            return []

    def display_workflows(self) -> None:
        """Display all workflows in a formatted table."""
        try:
            workflows = self.list_workflows()
            if not workflows:
                console.print(Panel("No workflows found", title="CI/CD Workflows"))
                return

            table = Table(title="CI/CD Workflows")
            table.add_column("Workflow")
            table.add_column("Status")
            
            for workflow in workflows:
                status = "✅" if self._validate_workflow_syntax(yaml.safe_load(workflow.read_text())) else "❌"
                table.add_row(workflow.stem, status)
            
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error displaying workflows: {e}[/red]") 