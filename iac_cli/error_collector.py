import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import hcl2
from .validator import ValidationError

@dataclass
class NormalizedError:
    error_type: str  # syntax, logic, versioning
    location: Dict[str, int]  # file, line, column
    message: str
    context: Dict[str, str]  # surrounding code, variable definitions, etc.
    severity: str  # error, warning, info

class ErrorCollector:
    def __init__(self):
        self.error_patterns = {
            'syntax': [
                r'Error: Invalid expression',
                r'Error: Invalid block definition',
                r'Error: Invalid argument',
            ],
            'logic': [
                r'Error: Reference to undeclared resource',
                r'Error: Reference to undeclared variable',
                r'Error: Invalid reference',
            ],
            'versioning': [
                r'Error: Unsupported argument',
                r'Error: Invalid version constraint',
                r'Error: Provider version constraint',
            ]
        }

    def normalize_errors(self, errors: List[ValidationError], file_path: Path) -> List[NormalizedError]:
        """Normalize validation errors into structured format."""
        normalized_errors = []
        
        # Read the file content for context
        try:
            with open(file_path, 'r') as f:
                file_content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return normalized_errors

        # Parse HCL2 for context
        try:
            hcl_data = hcl2.loads(file_content)
        except Exception as e:
            print(f"Error parsing HCL2: {e}")
            hcl_data = {}

        for error in errors:
            normalized_error = self._normalize_error(error, file_content, hcl_data)
            if normalized_error:
                normalized_errors.append(normalized_error)

        return normalized_errors

    def _normalize_error(self, error: ValidationError, file_content: str, hcl_data: Dict) -> Optional[NormalizedError]:
        """Normalize a single validation error."""
        # Determine error type
        error_type = self._determine_error_type(error.message)
        
        # Get context
        context = self._get_error_context(error, file_content, hcl_data)
        
        # Determine severity
        severity = self._determine_severity(error_type, error.message)
        
        return NormalizedError(
            error_type=error_type,
            location={
                'file': error.file,
                'line': error.line,
                'column': error.column
            },
            message=error.message,
            context=context,
            severity=severity
        )

    def _determine_error_type(self, message: str) -> str:
        """Determine the type of error based on the message."""
        for error_type, patterns in self.error_patterns.items():
            if any(re.search(pattern, message) for pattern in patterns):
                return error_type
        return 'unknown'

    def _get_error_context(self, error: ValidationError, file_content: str, hcl_data: Dict) -> Dict[str, str]:
        """Get context around the error."""
        context = {}
        
        # Get surrounding code
        lines = file_content.split('\n')
        start_line = max(0, error.line - 3)
        end_line = min(len(lines), error.line + 3)
        context['surrounding_code'] = '\n'.join(lines[start_line:end_line])
        
        # Get variable definitions if available
        if 'variable' in hcl_data:
            context['variables'] = str(hcl_data['variable'])
        
        return context

    def _determine_severity(self, error_type: str, message: str) -> str:
        """Determine the severity of the error."""
        if 'Error:' in message:
            return 'error'
        elif 'Warning:' in message:
            return 'warning'
        return 'info' 