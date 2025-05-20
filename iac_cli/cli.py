import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from typing import Optional
import json
import os
import subprocess
from botocore.exceptions import ClientError

from .validator import ValidatorEngine
from .error_collector import ErrorCollector
from .bedrock_agent import BedrockAgent
from .cost_estimator import CostEstimator
from .version_control import GitManager
from .cicd import CICDManager
from .feedback import FeedbackManager
from .interactive import InteractiveMode
from .security import SecurityManager, security_decorator, validate_terraform_file

app = typer.Typer()
console = Console()
security = SecurityManager()

def validate_aws_credentials():
    """Validate AWS credentials are configured."""
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials:
            console.print("[red]AWS credentials not found. Please configure your AWS credentials.[/red]")
            return False
        return True
    except Exception as e:
        console.print(f"[red]Error validating AWS credentials: {e}[/red]")
        return False

def validate_file_path(file_path: Path) -> bool:
    """Validate file path exists and is readable."""
    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        return False
    if not os.access(file_path, os.R_OK):
        console.print(f"[red]Cannot read file: {file_path}[/red]")
        return False
    return True

def validate_write_permission(file_path: Path) -> bool:
    """Validate write permission for file."""
    if file_path.exists() and not os.access(file_path, os.W_OK):
        console.print(f"[red]Cannot write to file: {file_path}[/red]")
        return False
    if not file_path.exists():
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
            file_path.unlink()
        except Exception as e:
            console.print(f"[red]Cannot write to directory: {file_path.parent}[/red]")
            return False
    return True

@app.command()
@security_decorator
def validate(
    file_path: Path = typer.Argument(..., help="Path to the Terraform file to validate"),
    live: bool = typer.Option(False, "--live", "-l", help="Enable live feedback")
):
    """Validate a Terraform file."""
    if not security.validate_file_path(file_path):
        raise typer.Exit(1)
        
    if not validate_terraform_file(file_path):
        raise typer.Exit(1)
        
    validator = ValidatorEngine()
    error_collector = ErrorCollector()
    
    try:
        if live:
            feedback = FeedbackManager()
            feedback.display_live_validation(validator.validate_file, file_path)
        else:
            errors = validator.validate_file(file_path)
            if errors:
                error_collector.collect_errors(errors)
                error_collector.display_errors()
            else:
                console.print(Panel("[green]No validation errors found![/green]", title="Validation Results"))
    except Exception as e:
        console.print(f"[red]Error during validation: {e}[/red]")
        raise typer.Exit(1)

@app.command()
@security_decorator
def fix(
    file_path: Path = typer.Argument(..., help="Path to the Terraform file to fix"),
    live: bool = typer.Option(False, "--live", "-l", help="Enable live feedback")
):
    """Fix validation errors in a Terraform file using AI."""
    if not security.validate_file_path(file_path) or not security.validate_file_path(file_path.parent):
        raise typer.Exit(1)
        
    if not validate_terraform_file(file_path):
        raise typer.Exit(1)
        
    if not security.validate_aws_credentials():
        raise typer.Exit(1)
        
    validator = ValidatorEngine()
    error_collector = ErrorCollector()
    agent = BedrockAgent()
    
    try:
        errors = validator.validate_file(file_path)
        if errors:
            error_collector.collect_errors(errors)
            fix_plan = agent.analyze_errors(errors)
            if fix_plan:
                console.print(Panel(fix_plan, title="Fix Plan"))
                if typer.confirm("Apply fixes?"):
                    agent.apply_fixes(file_path, fix_plan)
                    if live:
                        feedback = FeedbackManager()
                        feedback.display_live_validation(validator.validate_file, file_path)
                    else:
                        errors = validator.validate_file(file_path)
                        if not errors:
                            console.print(Panel("[green]All errors fixed successfully![/green]", title="Fix Results"))
        else:
            console.print(Panel("[green]No errors to fix![/green]", title="Fix Results"))
    except Exception as e:
        console.print(f"[red]Error during fix operation: {e}[/red]")
        raise typer.Exit(1)

@app.command()
@security_decorator
def generate(
    prompt: str = typer.Argument(..., help="Natural language prompt for code generation"),
    output_file: Path = typer.Argument(..., help="Path to save the generated Terraform code")
):
    """Generate Terraform code from a natural language prompt."""
    if not security.validate_file_path(output_file.parent):
        raise typer.Exit(1)
        
    if not security.validate_aws_credentials():
        raise typer.Exit(1)
        
    agent = BedrockAgent()
    
    try:
        prompt = f"""Generate Terraform code based on the following request:
{prompt}

Please provide only the Terraform code without any explanations or markdown formatting."""
        
        generated_code = agent._get_bedrock_response(prompt)
        if generated_code:
            output_file.write_text(generated_code)
            if not validate_terraform_file(output_file):
                console.print("[yellow]Warning: Generated code may contain security issues[/yellow]")
            console.print(Panel("[green]Code generated successfully![/green]", title="Generation Results"))
        else:
            console.print(Panel("[red]Failed to generate code.[/red]", title="Generation Results"))
    except Exception as e:
        console.print(f"[red]Error during code generation: {e}[/red]")
        raise typer.Exit(1)

@app.command()
@security_decorator
def estimate_costs(
    file_path: Path = typer.Argument(..., help="Path to the Terraform file"),
    live: bool = typer.Option(False, "--live", "-l", help="Enable live feedback"),
    optimize: bool = typer.Option(False, "--optimize", "-o", help="Show cost optimization suggestions")
):
    """Estimate infrastructure costs and provide optimization suggestions."""
    if not security.validate_file_path(file_path):
        raise typer.Exit(1)
        
    if not security.validate_aws_credentials():
        raise typer.Exit(1)
        
    estimator = CostEstimator()
    feedback = FeedbackManager()
    
    try:
        # Generate Terraform plan
        plan_path = file_path.parent / "terraform.tfplan"
        try:
            subprocess.run(
                ["terraform", "plan", "-out", str(plan_path)],
                cwd=file_path.parent,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error generating Terraform plan: {e.stderr.decode()}[/red]")
            raise typer.Exit(1)
        
        if live:
            feedback.display_live_cost_estimation(estimator.estimate_costs, plan_path)
        else:
            costs = estimator.estimate_costs(plan_path)
            estimator.display_costs(costs)
            
            if optimize:
                optimizations = estimator.get_optimization_suggestions(plan_path)
                estimator.display_optimizations(optimizations)
    except Exception as e:
        console.print(f"[red]Error during cost estimation: {e}[/red]")
        raise typer.Exit(1)

@app.command()
@security_decorator
def git(
    command: str = typer.Argument(..., help="Git command to execute"),
    repo_path: Path = typer.Option(Path.cwd(), "--repo", "-r", help="Path to the git repository")
):
    """Execute git commands."""
    if not security.validate_file_path(repo_path):
        raise typer.Exit(1)
        
    git_manager = GitManager(repo_path)
    
    try:
        if command == "status":
            git_manager.display_status()
        elif command == "commit":
            message = typer.prompt("Commit message")
            git_manager.commit_changes(message)
        elif command == "push":
            git_manager.push_changes()
        elif command == "pr":
            title = typer.prompt("PR title")
            body = typer.prompt("PR description")
            git_manager.create_pull_request(title, body)
        else:
            console.print(f"[red]Unknown git command: {command}[/red]")
    except Exception as e:
        console.print(f"[red]Error during git operation: {e}[/red]")
        raise typer.Exit(1)

@app.command()
@security_decorator
def cicd(
    command: str = typer.Argument(..., help="CI/CD command to execute"),
    repo_path: Path = typer.Option(Path.cwd(), "--repo", "-r", help="Path to the repository")
):
    """Manage CI/CD workflows."""
    if not security.validate_file_path(repo_path):
        raise typer.Exit(1)
        
    cicd_manager = CICDManager(repo_path)
    
    try:
        if command == "list":
            cicd_manager.display_workflows()
        elif command == "create":
            workflow_type = typer.prompt(
                "Workflow type",
                choices=["terraform", "security", "cost"]
            )
            if workflow_type == "terraform":
                cicd_manager.create_terraform_workflow()
            elif workflow_type == "security":
                cicd_manager.create_security_workflow()
            elif workflow_type == "cost":
                cicd_manager.create_cost_workflow()
        else:
            console.print(f"[red]Unknown CI/CD command: {command}[/red]")
    except Exception as e:
        console.print(f"[red]Error during CI/CD operation: {e}[/red]")
        raise typer.Exit(1)

@app.command()
@security_decorator
def interactive():
    """Start interactive mode."""
    interactive_mode = InteractiveMode()
    interactive_mode.start()

def main():
    """Main entry point for the CLI."""
    app() 