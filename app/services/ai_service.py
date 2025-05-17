from openai import OpenAI
from typing import Dict, List, Optional, Tuple
import json

class AIService:
    def __init__(self, settings):
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key)
        
    async def analyze_security_issue(self, 
                                   issue_description: str,
                                   file_content: str,
                                   file_type: str) -> Dict:
        """Analyze a security issue and generate a fix suggestion."""
        prompt = f"""You are a security expert reviewing infrastructure code.
Please analyze this security issue and provide a detailed response:

Issue Description:
{issue_description}

File Type: {file_type}
File Content:
```
{file_content}
```

Please provide:
1. A clear explanation of the security risk
2. The potential impact of this vulnerability
3. A specific fix suggestion
4. Best practices to prevent similar issues

Format your response as JSON with the following structure:
{{
    "explanation": "Clear explanation of the security risk",
    "impact": "Potential impact of the vulnerability",
    "fix_suggestion": "Specific code fix",
    "best_practices": ["List", "of", "best", "practices"]
}}
"""
        
        response = await self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a security expert AI assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.settings.openai_temperature
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            return {
                "explanation": "Error parsing AI response",
                "impact": "Unknown",
                "fix_suggestion": None,
                "best_practices": []
            }
    
    async def generate_fix(self, 
                          file_content: str,
                          issues: List[Dict],
                          file_type: str) -> Tuple[str, str]:
        """Generate a fix for multiple security issues in a file."""
        prompt = f"""As a security expert, please generate a fix for the following security issues in this {file_type} file.

Original File Content:
```
{file_content}
```

Security Issues:
{json.dumps(issues, indent=2)}

Please provide:
1. The complete fixed file content
2. A summary of all changes made

Format your response as JSON:
{{
    "fixed_content": "Complete fixed file content",
    "changes_summary": "Summary of all changes made"
}}

Ensure the fix:
1. Addresses all security issues
2. Maintains existing functionality
3. Follows best practices
4. Includes necessary comments explaining changes
"""
        
        response = await self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a security expert AI assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.settings.openai_temperature
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return result["fixed_content"], result["changes_summary"]
        except:
            return None, "Error generating fix"
    
    async def generate_pr_summary(self, 
                                security_issues: List[Dict],
                                fixes_applied: List[Dict]) -> str:
        """Generate a summary for the security review pull request."""
        prompt = f"""Please generate a clear and professional pull request summary for these security review results:

Security Issues Found:
{json.dumps(security_issues, indent=2)}

Fixes Applied:
{json.dumps(fixes_applied, indent=2)}

Generate a markdown-formatted summary that includes:
1. Overview of findings
2. Critical issues that were fixed
3. Remaining issues that need attention
4. Best practices recommendations

Use appropriate emojis and formatting to make the report clear and engaging."""
        
        response = await self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a security expert AI assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.settings.openai_temperature
        )
        
        return response.choices[0].message.content 