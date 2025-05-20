import difflib
from typing import List, Dict, Optional
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from .bedrock_agent import FixPlan

console = Console()

class PatchGenerator:
    def __init__(self):
        self.diff_context_lines = 3

    def generate_patch(self, file_path: Path, fix_plan: FixPlan) -> str:
        """Generate a patch for the given file and fix plan."""
        try:
            # Read the original file
            with open(file_path, 'r') as f:
                original_lines = f.readlines()

            # Create the new file content
            new_lines = self._apply_changes(original_lines, fix_plan.changes)

            # Generate the diff
            diff = difflib.unified_diff(
                original_lines,
                new_lines,
                fromfile=str(file_path),
                tofile=str(file_path),
                n=self.diff_context_lines
            )

            return ''.join(diff)

        except Exception as e:
            console.print(f"[red]Error generating patch: {e}[/red]")
            return ""

    def show_patch(self, patch: str) -> None:
        """Display the patch in a formatted way."""
        if not patch:
            console.print("[yellow]No changes to show[/yellow]")
            return

        console.print("\n[bold]Proposed Changes:[/bold]")
        console.print(Syntax(patch, "diff", theme="monokai"))

    def _apply_changes(self, original_lines: List[str], changes: List[Dict[str, str]]) -> List[str]:
        """Apply the changes to the original file content."""
        new_lines = original_lines.copy()
        
        # Sort changes by line number in reverse order to avoid offset issues
        sorted_changes = sorted(changes, key=lambda x: x['line'], reverse=True)
        
        for change in sorted_changes:
            line_num = change['line'] - 1  # Convert to 0-based index
            if 0 <= line_num < len(new_lines):
                new_lines[line_num] = change['content'] + '\n'
        
        return new_lines

    def apply_patch(self, file_path: Path, patch: str) -> bool:
        """Apply the patch to the file."""
        try:
            # Parse the patch
            patch_lines = patch.splitlines()
            if not patch_lines:
                return False

            # Read the original file
            with open(file_path, 'r') as f:
                original_lines = f.readlines()

            # Apply the patch
            new_lines = self._apply_patch_lines(original_lines, patch_lines)

            # Write the changes
            with open(file_path, 'w') as f:
                f.writelines(new_lines)

            return True

        except Exception as e:
            console.print(f"[red]Error applying patch: {e}[/red]")
            return False

    def _apply_patch_lines(self, original_lines: List[str], patch_lines: List[str]) -> List[str]:
        """Apply the patch lines to the original content."""
        new_lines = original_lines.copy()
        current_line = 0
        i = 0

        while i < len(patch_lines):
            line = patch_lines[i]
            
            if line.startswith('@@'):
                # Parse the line numbers from the patch header
                try:
                    current_line = int(line.split()[1].split(',')[0][1:]) - 1
                except:
                    current_line = 0
                i += 1
                continue

            if line.startswith(' '):
                # Context line, verify it matches
                if current_line < len(new_lines) and new_lines[current_line] == line[1:] + '\n':
                    current_line += 1
                i += 1
                continue

            if line.startswith('+'):
                # Add line
                new_lines.insert(current_line, line[1:] + '\n')
                current_line += 1
                i += 1
                continue

            if line.startswith('-'):
                # Remove line
                if current_line < len(new_lines):
                    new_lines.pop(current_line)
                i += 1
                continue

            i += 1

        return new_lines 