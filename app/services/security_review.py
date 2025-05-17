import asyncio
from typing import Dict, List, Optional
import subprocess
import tempfile
import os
import json
from dataclasses import dataclass, asdict

@dataclass
class SecurityIssue:
    file_path: str
    line_number: Optional[int]
    severity: str
    check_id: str
    description: str
    fixed: bool = False
    fix_suggestion: Optional[str] = None

class SecurityReviewService:
    def __init__(self, github_service, ai_service):
        self.github = github_service
        self.ai = ai_service
        self.review_results = {}
    
    async def review_pull_request(self, pull_request: Dict) -> None:
        """Perform a security review on a pull request."""
        repo_name = pull_request['head']['repo']['full_name']
        pr_number = pull_request['number']
        commit_sha = pull_request['head']['sha']
        
        # Set status to pending
        await self.github.create_status_check(
            repo_name,
            commit_sha,
            'pending',
            'Security review in progress',
            'security-review'
        )
        
        try:
            # Download and analyze files
            infra_files = await self.github.download_pr_files(repo_name, pr_number)
            
            # Store results for this PR
            self.review_results[pr_number] = {
                'issues': [],
                'fixes': [],
                'status': 'in_progress'
            }
            
            # Analyze each file
            for file_path, content in infra_files.items():
                # Run Checkov analysis
                issues = await self._run_checkov_analysis(content, file_path)
                
                # Get AI analysis for each issue
                for issue in issues:
                    analysis = await self.ai.analyze_security_issue(
                        issue.description,
                        content,
                        file_path.split('.')[-1]
                    )
                    
                    issue.fix_suggestion = analysis.get('fix_suggestion')
                    
                    # Add inline comment
                    if issue.line_number:
                        comment = f"""🔒 **Security Issue Detected**
Severity: {issue.severity}
Check: {issue.check_id}

{analysis.get('explanation')}

**Impact:**
{analysis.get('impact')}

**Suggested Fix:**
```
{analysis.get('fix_suggestion')}
```

**Best Practices:**
{chr(10).join(f'- {practice}' for practice in analysis.get('best_practices', []))}
"""
                        await self.github.create_review_comment(
                            repo_name,
                            pr_number,
                            comment,
                            commit_sha,
                            file_path,
                            issue.line_number
                        )
                    
                    self.review_results[pr_number]['issues'].append(asdict(issue))
            
            # Generate fixes if enabled
            if self.github.settings.auto_fix_enabled:
                await self._generate_and_apply_fixes(
                    repo_name,
                    pr_number,
                    pull_request['head']['ref'],
                    infra_files
                )
            
            # Generate summary report
            summary = await self.ai.generate_pr_summary(
                self.review_results[pr_number]['issues'],
                self.review_results[pr_number]['fixes']
            )
            
            await self.github.create_review_comment(
                repo_name,
                pr_number,
                summary,
                commit_sha,
                None
            )
            
            # Update final status
            has_critical = any(i['severity'] == 'CRITICAL' 
                             for i in self.review_results[pr_number]['issues'])
            
            status = 'failure' if has_critical else 'success'
            description = ('Critical security issues found!' 
                         if has_critical 
                         else 'Security review passed')
            
            await self.github.create_status_check(
                repo_name,
                commit_sha,
                status,
                description,
                'security-review'
            )
            
            self.review_results[pr_number]['status'] = 'completed'
            
        except Exception as e:
            await self.github.create_status_check(
                repo_name,
                commit_sha,
                'error',
                f'Security review failed: {str(e)}',
                'security-review'
            )
            self.review_results[pr_number]['status'] = 'error'
    
    async def _run_checkov_analysis(self, 
                                  content: str, 
                                  file_path: str) -> List[SecurityIssue]:
        """Run Checkov analysis on a file."""
        issues = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=os.path.splitext(file_path)[1]) as tmp:
            tmp.write(content)
            tmp.flush()
            
            try:
                # Run Checkov
                result = subprocess.run(
                    ['checkov', '-f', tmp.name, '--output', 'json'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    
                    for check in data.get('results', {}).get('failed_checks', []):
                        issue = SecurityIssue(
                            file_path=file_path,
                            line_number=check.get('file_line_range', [None])[0],
                            severity=check.get('severity', 'UNKNOWN'),
                            check_id=check.get('check_id', 'UNKNOWN'),
                            description=check.get('check_name', '')
                        )
                        issues.append(issue)
            
            except Exception as e:
                print(f"Error running Checkov: {str(e)}")
        
        return issues
    
    async def _generate_and_apply_fixes(self,
                                      repo_name: str,
                                      pr_number: int,
                                      base_branch: str,
                                      files: Dict[str, str]) -> None:
        """Generate and apply fixes for security issues."""
        fixes = {}
        
        for file_path, content in files.items():
            file_issues = [i for i in self.review_results[pr_number]['issues'] 
                         if i['file_path'] == file_path]
            
            if file_issues:
                fixed_content, summary = await self.ai.generate_fix(
                    content,
                    file_issues,
                    file_path.split('.')[-1]
                )
                
                if fixed_content:
                    fixes[file_path] = fixed_content
                    self.review_results[pr_number]['fixes'].append({
                        'file_path': file_path,
                        'summary': summary
                    })
        
        if fixes:
            await self.github.create_fix_pr(
                repo_name,
                base_branch,
                fixes,
                "🔒 Security fixes suggested by AI review",
                "This PR contains automated security fixes suggested by the AI security review."
            )
    
    async def get_review_status(self, pr_number: int) -> Dict:
        """Get the status of a security review."""
        if pr_number not in self.review_results:
            return {'status': 'not_found'}
        return self.review_results[pr_number] 