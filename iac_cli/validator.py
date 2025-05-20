import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from rich.console import Console
import re

console = Console()

@dataclass
class ValidationError:
    file: str
    line: int
    column: int
    message: str
    code: str

class ValidatorEngine:
    def __init__(self, working_dir: Optional[Path] = None):
        self.working_dir = working_dir or Path.cwd()

    def validate(self, file_path: Path) -> List[ValidationError]:
        """Validate a Terraform configuration file."""
        try:
            # Run terraform init if needed
            self._run_terraform_init()
            
            # Run terraform validate
            result = subprocess.run(
                ["terraform", "validate"],
                cwd=self.working_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return []
            
            # Parse validation errors
            return self._parse_validation_errors(result.stderr)
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error running terraform validate: {e}[/red]")
            return []
        except Exception as e:
            console.print(f"[red]Unexpected error during validation: {e}[/red]")
            return []

    def _run_terraform_init(self) -> None:
        """Run terraform init if needed."""
        try:
            subprocess.run(
                ["terraform", "init"],
                cwd=self.working_dir,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            console.print(f"[yellow]Warning: terraform init failed: {e}[/yellow]")

    def _parse_validation_errors(self, error_output: str) -> List[ValidationError]:
        """Parse terraform validate error output into structured errors."""
        errors = []
        # Typical error line: Error: Invalid value for argument
        #   on main.tf line 7, in resource "aws_s3_bucket" "example":
        #    7:     enabled = "true"
        # We'll use regex to extract file, line, message, and code
        error_blocks = error_output.strip().split("Error:")
        for block in error_blocks:
            if not block.strip():
                continue
            # Extract message (first line)
            lines = block.strip().splitlines()
            message = lines[0].strip() if lines else "Unknown error"
            # Extract file and line
            file = "unknown"
            line = 0
            column = 0
            code = "terraform"
            for l in lines:
                m = re.search(r'on (.+) line (\d+)', l)
                if m:
                    file = m.group(1).strip()
                    line = int(m.group(2))
                # Optionally extract column if available (rare in terraform)
            errors.append(ValidationError(
                file=file,
                line=line,
                column=column,
                message=message,
                code=code
            ))
        return errors 