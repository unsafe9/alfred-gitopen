#!/usr/bin/env python3
"""
Local Git utilities for Alfred Git Open workflow.
"""
import os
import subprocess
from typing import Tuple, List, Optional

def is_git_repository(path: str) -> bool:
    """Check if path is a Git repository."""
    return os.path.isdir(os.path.join(path, '.git'))

def init_repository(path: str) -> Tuple[bool, str]:
    """Initialize a Git repository in the given path."""
    try:
        if not os.path.exists(path):
            return False, f"Path does not exist: {path}"
        
        result = subprocess.run(['git', 'init'], cwd=path, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, f"Initialized empty Git repository in {path}"
        else:
            return False, f"Git init failed: {result.stderr}"
    
    except Exception as e:
        return False, f"Error initializing repository: {str(e)}"

def clone_repository(git_url: str, target_path: str, branch: str = None) -> Tuple[bool, str]:
    """Clone a Git repository."""
    try:
        cmd = ['git', 'clone']
        
        if branch:
            cmd.extend(['-b', branch])
        
        cmd.extend([git_url, target_path])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, f"Successfully cloned to: {target_path}"
        else:
            return False, f"Clone failed: {result.stderr}"
    
    except Exception as e:
        return False, f"Error cloning repository: {str(e)}"


def get_current_branch(repo_path: str) -> str:
    """Get current branch name."""
    if not is_git_repository(repo_path):
        return ""
    
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              cwd=repo_path, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""

def get_remote_url(repo_path: str) -> str:
    """Get remote origin URL."""
    if not is_git_repository(repo_path):
        return ""
    
    try:
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              cwd=repo_path, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def get_repository_name_from_url(git_url: str) -> str:
    """Extract repository name from Git URL."""
    # Remove .git suffix if present
    if git_url.endswith('.git'):
        git_url = git_url[:-4]
    
    # Extract name from URL
    if '/' in git_url:
        repo_name = git_url.split('/')[-1]
    else:
        repo_name = git_url
    
    return repo_name

def validate_git_url(git_url: str) -> bool:
    """Validate if string is a valid Git URL."""
    if not git_url:
        return False
    
    # Common Git URL patterns
    patterns = [
        git_url.startswith('https://'),
        git_url.startswith('http://'),
        git_url.startswith('git@'),
        git_url.startswith('ssh://'),
        git_url.startswith('git://'),
        '.git' in git_url
    ]
    
    return any(patterns)

def extract_git_urls(text: str) -> List[str]:
    """Extract Git repository URLs from text."""
    import re
    
    git_urls = []
    
    # Enhanced Git URL patterns to support various hosting services
    patterns = [
        # HTTPS URLs - Generic pattern for any domain
        r'https?://[a-zA-Z0-9.-]+/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?(?:/.*)?',
        # SSH URLs - Generic pattern for any domain
        r'git@[a-zA-Z0-9.-]+:[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?',
        # SSH URLs with custom ports
        r'ssh://git@[a-zA-Z0-9.-]+(?::[0-9]+)?/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?',
        # Git protocol URLs
        r'git://[a-zA-Z0-9.-]+/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Normalize URL
            normalized_url = normalize_git_url(match)
            if normalized_url and validate_git_url(normalized_url) and normalized_url not in git_urls:
                git_urls.append(normalized_url)
    
    return git_urls

def normalize_git_url(url: str) -> Optional[str]:
    """Normalize Git URL."""
    import re
    
    if not url:
        return None
    
    # Remove trailing slashes and fragments
    url = url.rstrip('/').split('#')[0].split('?')[0]
    
    # Convert SSH URL to HTTPS
    if url.startswith('git@'):
        # git@domain:user/repo.git -> https://domain/user/repo
        ssh_pattern = r'git@([^:]+):(.+)'
        match = re.match(ssh_pattern, url)
        if match:
            domain, path = match.groups()
            # Remove .git suffix if present
            if path.endswith('.git'):
                path = path[:-4]
            url = f"https://{domain}/{path}"
    
    # Ensure .git suffix for consistency
    if not url.endswith('.git') and not url.endswith('/'):
        url += '.git'
    
    return url

def get_domain_from_git_url(url: str) -> str:
    """Extract domain from Git URL for display."""
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return "unknown"


def get_unique_directory_name(base_path: str, name: str) -> str:
    """Get unique directory name by appending counter if needed."""
    import os
    target_path = os.path.join(base_path, name)
    
    if not os.path.exists(target_path):
        return target_path
    
    counter = 1
    while os.path.exists(f"{target_path}_{counter}"):
        counter += 1
    
    return f"{target_path}_{counter}"

def validate_local_repo_name(name: str) -> Tuple[bool, str]:
    """Check if repository name is valid for local filesystem."""
    if not name or not name.strip():
        return False, "Repository name cannot be empty"
    
    name = name.strip()
    
    # Check for invalid characters (macOS filesystem)
    invalid_chars = ['/', ':']
    if any(char in name for char in invalid_chars):
        return False, f"Repository name contains invalid characters: {', '.join(invalid_chars)}"
    
    # Check if name starts or ends with dot or space
    if name.startswith('.') or name.endswith('.') or name.startswith(' ') or name.endswith(' '):
        return False, "Repository name cannot start or end with dot or space"
    
    # Check length
    if len(name) > 255:
        return False, "Repository name is too long (maximum 255 characters)"
    
    return True, ""
