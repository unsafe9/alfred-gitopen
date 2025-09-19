#!/usr/bin/env python3
"""
GitHub API and CLI utilities for Alfred Git Open workflow.
"""
import json
import subprocess
import re
from typing import Tuple, List, Dict, Optional
from utils import run_command_with_success

def check_gh_cli() -> Tuple[bool, str]:
    """Check if GitHub CLI is installed and authenticated."""
    try:
        # Check if gh is installed
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            return False, "GitHub CLI (gh) is not installed. Please install it via: brew install gh"
        
        # Check if user is authenticated
        result = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True)
        if result.returncode != 0:
            return False, "GitHub CLI is not authenticated. Please run: gh auth login"
        
        return True, ""
    except FileNotFoundError:
        return False, "GitHub CLI (gh) is not installed. Please install it via: brew install gh"

def is_valid_repo_name(name: str) -> Tuple[bool, str]:
    """Check if repository name is valid for GitHub."""
    if not name or not name.strip():
        return False, "Repository name cannot be empty"
    
    name = name.strip()
    
    # GitHub repository name rules
    if len(name) > 100:
        return False, "Repository name cannot be longer than 100 characters"
    
    # Must start and end with alphanumeric characters
    if not re.match(r'^[a-zA-Z0-9].*[a-zA-Z0-9]$', name) and len(name) > 1:
        return False, "Repository name must start and end with alphanumeric characters"
    
    if len(name) == 1 and not re.match(r'^[a-zA-Z0-9]$', name):
        return False, "Single character repository name must be alphanumeric"
    
    # Can contain alphanumeric characters, hyphens, underscores, and periods
    if not re.match(r'^[a-zA-Z0-9._-]+$', name):
        return False, "Repository name can only contain alphanumeric characters, hyphens, underscores, and periods"
    
    # Cannot contain consecutive periods
    if '..' in name:
        return False, "Repository name cannot contain consecutive periods"
    
    # Cannot be just periods
    if name.replace('.', '') == '':
        return False, "Repository name cannot consist only of periods"
    
    return True, ""

def check_repo_exists(repo_name: str) -> bool:
    """Check if repository already exists in user's GitHub account."""
    try:
        result = subprocess.run(['gh', 'repo', 'view', repo_name], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def search_github_repos(query: str, limit: int = 20) -> List[Dict]:
    """Search GitHub repositories using GitHub CLI."""
    try:
        # Search repositories with various filters
        cmd = [
            'gh', 'repo', 'list', 
            '--limit', str(limit),
            '--json', 'name,owner,description,url,isPrivate,stargazerCount,updatedAt'
        ]
        
        # If query contains '/', treat it as owner/repo search
        if '/' in query:
            owner, repo = query.split('/', 1)
            cmd.extend(['--search', f'{owner}/{repo}'])
        else:
            # Search in repository names and descriptions
            cmd.extend(['--search', query])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Try alternative search method
            cmd = [
                'gh', 'search', 'repos', query,
                '--limit', str(limit),
                '--json', 'name,owner,description,url,isPrivate,stargazersCount,updatedAt'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"GitHub search failed: {result.stderr}")
        
        repos = json.loads(result.stdout)
        return repos
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse GitHub search results: {e}")
    except Exception as e:
        raise Exception(f"GitHub search failed: {str(e)}")

def get_user_repos(limit: int = 50) -> List[Dict]:
    """Get user's own repositories."""
    try:
        cmd = [
            'gh', 'repo', 'list',
            '--limit', str(limit),
            '--json', 'name,owner,description,url,isPrivate,stargazerCount,updatedAt'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Failed to get user repositories: {result.stderr}")
        
        repos = json.loads(result.stdout)
        return repos
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse user repositories: {e}")
    except Exception as e:
        raise Exception(f"Failed to get user repositories: {str(e)}")

def format_repo_subtitle(repo: Dict) -> str:
    """Format repository subtitle for Alfred display."""
    parts = []
    
    # Privacy status
    if repo.get('isPrivate'):
        parts.append("🔒 Private")
    else:
        parts.append("🌐 Public")
    
    # Star count (handle both field names from different gh commands)
    stars = repo.get('stargazerCount', 0) or repo.get('stargazersCount', 0)
    if stars > 0:
        if stars >= 1000:
            star_text = f"⭐ {stars/1000:.1f}k"
        else:
            star_text = f"⭐ {stars}"
        parts.append(star_text)
    
    # Description
    description = repo.get('description', '').strip()
    if description:
        # Limit description length
        if len(description) > 60:
            description = description[:57] + "..."
        parts.append(description)
    
    return " • ".join(parts)

def create_github_repository(repo_name: str, private: bool = True, description: str = None) -> Tuple[bool, str]:
    """Create a new GitHub repository."""
    try:
        # Create repository using GitHub CLI
        cmd = ['gh', 'repo', 'create', repo_name]
        
        if private:
            cmd.append('--private')
        else:
            cmd.append('--public')
        
        if description:
            cmd.extend(['--description', description])
        #else:
        #    cmd.extend(['--description', 'Repository created via Alfred Git Open workflow'])
        
        cmd.append('--add-readme')  # Initialize with README
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, f"Successfully created GitHub repository: {repo_name}"
        else:
            return False, f"Failed to create repository: {result.stderr}"
    
    except Exception as e:
        return False, f"Error creating repository: {str(e)}"

def clone_github_repository(repo_name: str, target_dir: str) -> Tuple[bool, str]:
    """Clone a GitHub repository."""
    try:
        # Use GitHub CLI to clone (handles authentication automatically)
        cmd = ['gh', 'repo', 'clone', repo_name, target_dir]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, f"Successfully cloned to: {target_dir}"
        else:
            return False, f"Clone failed: {result.stderr}"
    
    except Exception as e:
        return False, f"Error cloning repository: {str(e)}"

def delete_github_repository(repo_name: str) -> Tuple[bool, str]:
    """Delete a GitHub repository."""
    try:
        cmd = ['gh', 'repo', 'delete', repo_name, '--yes']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, f"Successfully deleted repository: {repo_name}"
        else:
            return False, f"Failed to delete repository: {result.stderr}"
    
    except Exception as e:
        return False, f"Error deleting repository: {str(e)}"

def is_private_repo(git_url: str, is_private_meta: Optional[bool] = None) -> bool:
    """Check if repository is private."""
    # If metadata is provided, use it
    if is_private_meta is not None:
        return is_private_meta
    
    # Fallback: check if it's from user's account
    try:
        result = subprocess.run(['gh', 'api', 'user'], capture_output=True, text=True)
        if result.returncode == 0:
            user_info = json.loads(result.stdout)
            username = user_info.get('login', '')
            
            # Check if URL contains the user's username
            if username and f'/{username}/' in git_url:
                return True
    except Exception:
        pass
    
    return False

def convert_to_ssh_url(git_url: str) -> str:
    """Convert HTTPS GitHub URL to SSH format."""
    import re
    
    # Pattern: https://github.com/owner/repo.git -> git@github.com:owner/repo.git
    https_pattern = r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
    match = re.match(https_pattern, git_url)
    
    if match:
        owner, repo = match.groups()
        return f"git@github.com:{owner}/{repo}.git"
    
    return git_url

def get_clone_method(git_url: str, is_private_meta: Optional[bool] = None) -> str:
    """Determine the best clone method based on repository type and user settings."""
    import os
    
    is_private = is_private_repo(git_url, is_private_meta)
    
    if is_private:
        method = os.environ.get('CLONE_METHOD_PRIVATE', 'ssh').lower()
    else:
        method = os.environ.get('CLONE_METHOD_PUBLIC', 'https').lower()
    
    return method

def clone_repository_with_method(git_url: str, target_dir: str, is_private_meta: Optional[bool] = None) -> Tuple[bool, str]:
    """Clone a Git repository using the appropriate method."""
    from git import clone_repository
    
    clone_method = get_clone_method(git_url, is_private_meta)
    
    try:
        if clone_method == 'gh':
            # Use GitHub CLI
            cmd = ['gh', 'repo', 'clone', git_url, target_dir]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, f"Successfully cloned to: {target_dir}"
            else:
                return False, f"Clone failed: {result.stderr}"
        else:
            # Use git clone with URL conversion if needed
            clone_url = git_url
            if clone_method == 'ssh' and git_url.startswith('https://github.com/'):
                clone_url = convert_to_ssh_url(git_url)
            
            # Use git.py clone function with fallback
            success, message = clone_repository(clone_url, target_dir)
            
            if not success and clone_method == 'ssh' and not is_private_repo(git_url, is_private_meta):
                # Fallback to HTTPS for public repos
                success, message = clone_repository(git_url, target_dir)
                if success:
                    message += " (fallback to HTTPS)"
            
            return success, message
    
    except Exception as e:
        return False, f"Error occurred: {str(e)}"

