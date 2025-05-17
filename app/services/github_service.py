from github import Github
from github.PullRequest import PullRequest
from typing import List, Dict, Optional
import base64
import os
import tempfile

class GithubService:
    def __init__(self, settings):
        self.settings = settings
        self.github = Github(settings.github_token)
    
    async def get_pull_request_files(self, repo_name: str, pr_number: int) -> List[Dict]:
        """Get all files changed in a pull request."""
        repo = self.github.get_repo(repo_name)
        pull_request = repo.get_pull(pr_number)
        return list(pull_request.get_files())
    
    async def download_file(self, repo_name: str, file_path: str, ref: str) -> str:
        """Download a file from GitHub and return its contents."""
        repo = self.github.get_repo(repo_name)
        try:
            content = repo.get_contents(file_path, ref=ref)
            if isinstance(content, list):
                raise ValueError(f"Path {file_path} points to a directory")
            return base64.b64decode(content.content).decode('utf-8')
        except Exception as e:
            return None
    
    async def create_review_comment(self, repo_name: str, pr_number: int, 
                                  body: str, commit_id: str, path: str, 
                                  line: Optional[int] = None) -> None:
        """Create a review comment on a specific line in a pull request."""
        repo = self.github.get_repo(repo_name)
        pull_request = repo.get_pull(pr_number)
        
        if line:
            pull_request.create_review_comment(
                body=body,
                commit_id=commit_id,
                path=path,
                line=line
            )
        else:
            pull_request.create_issue_comment(body)
    
    async def create_status_check(self, repo_name: str, commit_sha: str, 
                                state: str, description: str, context: str) -> None:
        """Create a status check on a commit."""
        repo = self.github.get_repo(repo_name)
        repo.get_commit(commit_sha).create_status(
            state=state,
            description=description,
            context=context
        )
    
    async def download_pr_files(self, repo_name: str, pr_number: int) -> Dict[str, str]:
        """Download all infrastructure files from a pull request."""
        repo = self.github.get_repo(repo_name)
        pull_request = repo.get_pull(pr_number)
        files = pull_request.get_files()
        
        infra_files = {}
        for file in files:
            if file.filename.endswith(('.tf', '.yaml', '.yml')):
                content = await self.download_file(
                    repo_name, 
                    file.filename, 
                    pull_request.head.sha
                )
                if content:
                    infra_files[file.filename] = content
        
        return infra_files
    
    async def create_fix_pr(self, repo_name: str, base_branch: str, 
                           changes: Dict[str, str], title: str, 
                           body: str) -> None:
        """Create a new pull request with fixes."""
        repo = self.github.get_repo(repo_name)
        base = repo.get_branch(base_branch)
        
        # Create a new branch
        branch_name = f"security-fixes-{base.commit.sha[:7]}"
        try:
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base.commit.sha
            )
        except:
            # Branch might already exist
            pass
        
        # Create commits with fixes
        for file_path, content in changes.items():
            try:
                current_file = repo.get_contents(
                    file_path, 
                    ref=branch_name
                )
                repo.update_file(
                    file_path,
                    f"fix: Security improvements for {file_path}",
                    content,
                    current_file.sha,
                    branch=branch_name
                )
            except:
                repo.create_file(
                    file_path,
                    f"fix: Security improvements for {file_path}",
                    content,
                    branch=branch_name
                )
        
        # Create pull request
        repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base=base_branch
        ) 