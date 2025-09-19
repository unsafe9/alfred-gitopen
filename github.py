#!/usr/bin/env python3
"""
GitHub API and CLI utilities for Alfred Git Open workflow.
"""
import json
import subprocess
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, List, Dict, Optional, Callable, Any
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

def search_github_repos(query: str, limit: int = 15, exclude_user_repos: bool = False) -> List[Dict]:
    """Search GitHub repositories using GitHub CLI."""
    try:
        # Build search query
        search_query = query
        
        # Add exclusion for user repositories if requested
        if exclude_user_repos:
            current_username = get_current_username()
            if current_username:
                search_query = f"{query} -user:{current_username}"
        
        # Search repositories using gh search repos
        cmd = [
            'gh', 'search', 'repos', search_query,
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

def get_current_username() -> str:
    """Get the current GitHub username."""
    try:
        user_result = subprocess.run(['gh', 'api', 'user'], capture_output=True, text=True)
        if user_result.returncode == 0:
            user_info = json.loads(user_result.stdout)
            return user_info.get('login', '')
    except Exception:
        pass
    return ''

def get_user_repos(limit: int = 10, query: str = None) -> List[Dict]:
    """Get user's own repositories using search with owner filter."""
    try:
        # Use gh search repos with owner filter
        search_query = query.strip() if query and query.strip() else "*"
        cmd = [
            'gh', 'search', 'repos', search_query,
            '--owner', '@me',
            '--limit', str(limit),
            '--json', 'name,owner,description,url,isPrivate,stargazersCount,updatedAt'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Failed to search user repositories: {result.stderr}")
        
        repos = json.loads(result.stdout)
        
        # Normalize field names (search uses stargazersCount, list uses stargazerCount)
        for repo in repos:
            if 'stargazersCount' in repo and 'stargazerCount' not in repo:
                repo['stargazerCount'] = repo['stargazersCount']
        
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

def fork_github_repository(repo_name: str, organization: str = None) -> Tuple[bool, str]:
    """Fork a GitHub repository."""
    try:
        cmd = ['gh', 'repo', 'fork', repo_name]
        
        if organization:
            cmd.extend(['--org', organization])
        
        # Don't clone automatically, we'll handle that separately
        cmd.append('--remote=false')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, f"Successfully forked repository: {repo_name}"
        else:
            return False, f"Failed to fork repository: {result.stderr}"
    
    except Exception as e:
        return False, f"Error forking repository: {str(e)}"

def fork_and_clone_repository(repo_name: str, target_dir: str, organization: str = None) -> Tuple[bool, str]:
    """Fork a GitHub repository and clone it locally."""
    try:
        # First, fork the repository
        success, message = fork_github_repository(repo_name, organization)
        if not success:
            return False, message
        
        # Get the current user's username for the forked repo URL
        result = subprocess.run(['gh', 'api', 'user'], capture_output=True, text=True)
        if result.returncode != 0:
            return False, "Failed to get current user information"
        
        user_info = json.loads(result.stdout)
        username = user_info.get('login', '')
        
        if not username:
            return False, "Failed to get username from GitHub"
        
        # Construct the forked repository name
        original_repo = repo_name.split('/')[-1] if '/' in repo_name else repo_name
        forked_repo_name = f"{username}/{original_repo}"
        
        # Clone the forked repository
        clone_success, clone_message = clone_github_repository(forked_repo_name, target_dir)
        
        if clone_success:
            return True, f"Successfully forked and cloned to: {target_dir}"
        else:
            return False, f"Forked successfully but clone failed: {clone_message}"
    
    except Exception as e:
        return False, f"Error in fork and clone process: {str(e)}"

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


# =============================================================================
# GitHub Search Base Functions
# =============================================================================

def github_search_base(
    empty_query_title: str,
    empty_query_subtitle: str,
    no_results_message: str,
    repo_filter_func: Optional[Callable[[Dict[str, Any], str], bool]] = None,
    item_formatter_func: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    search_limit: int = 15,
    include_user_repos: bool = False
) -> None:
    """
    Base function for GitHub repository search workflows.
    
    Args:
        empty_query_title: Title to show when query is empty
        empty_query_subtitle: Subtitle to show when query is empty
        no_results_message: Message to show when no results found
        repo_filter_func: Function to filter repositories (repo, username) -> bool
        item_formatter_func: Function to format Alfred items from repo data
        search_limit: Maximum number of search results
        include_user_repos: Whether to include user's own repositories
    """
    from alfred import output, error_item, item, handle_empty_query, get_query_from_argv
    
    # Check if GitHub CLI is available
    is_available, error_msg = check_gh_cli()
    if not is_available:
        alfred_error_item = error_item("GitHub CLI Required", error_msg)
        output([alfred_error_item])
        return
    
    # Get query from Alfred
    query = get_query_from_argv()
    
    if not query.strip():
        handle_empty_query(empty_query_title, empty_query_subtitle)
        return
    
    try:
        items = []
        current_username = get_current_username()
        
        # Get repositories using parallel execution
        all_repos = []
        seen_urls = set()
        
        # Execute searches in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            
            # Submit user repos search if requested
            if include_user_repos:
                user_repos_future = executor.submit(get_user_repos, 10, query)
                futures.append(('user_repos', user_repos_future))
            
            # Submit public repos search (exclude user repos if we're including them separately)
            search_repos_future = executor.submit(search_github_repos, query, search_limit, include_user_repos)
            futures.append(('search_repos', search_repos_future))
            
            # Collect results as they complete
            user_repos = []
            search_repos = []
            
            for future_type, future in futures:
                try:
                    result = future.result(timeout=30)
                    if future_type == 'user_repos':
                        user_repos = result
                    elif future_type == 'search_repos':
                        search_repos = result
                except Exception as e:
                    # Log error but continue with other results
                    pass  # Silently handle errors from individual searches
                    if future_type == 'user_repos':
                        user_repos = []
                    elif future_type == 'search_repos':
                        search_repos = []
        
        # Add user repos first (higher priority)
        for repo in user_repos:
            url = repo.get('url', '')
            if url not in seen_urls:
                all_repos.append(repo)
                seen_urls.add(url)
        
        # Add search results
        for repo in search_repos:
            url = repo.get('url', '')
            if url not in seen_urls:
                all_repos.append(repo)
                seen_urls.add(url)
        
        # Filter and format repositories
        for repo in all_repos[:search_limit]:
            # Apply filter if provided
            if repo_filter_func and not repo_filter_func(repo, current_username):
                continue
            
            # Format item
            if item_formatter_func:
                alfred_item = item_formatter_func(repo)
                if alfred_item:
                    items.append(alfred_item)
            else:
                # Default formatting
                owner = repo.get('owner', {})
                repo_name = repo.get('name', '')
                owner_login = owner.get('login', '') if isinstance(owner, dict) else str(owner)
                full_name = f"{owner_login}/{repo_name}"
                clone_url = repo.get('url', '')
                is_private = repo.get('isPrivate', False)
                
                alfred_item = item(
                    full_name,
                    format_repo_subtitle(repo),
                    f"{clone_url}|{is_private}"
                )
                items.append(alfred_item)
        
        if not items:
            no_results_item_result = item("No repositories found", no_results_message.format(query=query), valid=False)
            items.append(no_results_item_result)
        
        output(items)
        
    except Exception as e:
        alfred_error_item = error_item("Search failed", f"GitHub search failed: {str(e)}")
        output([alfred_error_item])


def clone_repo_filter(repo: Dict[str, Any], username: str) -> bool:
    """Filter function for clone workflow - includes all repositories."""
    return True


def fork_repo_filter(repo: Dict[str, Any], username: str) -> bool:
    """Filter function for fork workflow - excludes user's own repositories."""
    owner = repo.get('owner', {})
    owner_login = owner.get('login', '') if isinstance(owner, dict) else str(owner)
    return owner_login != username


def clone_item_formatter(repo: Dict[str, Any]) -> Dict[str, Any]:
    """Format Alfred item for clone workflow."""
    from alfred import item
    
    owner = repo.get('owner', {})
    repo_name = repo.get('name', '')
    owner_login = owner.get('login', '') if isinstance(owner, dict) else str(owner)
    full_name = f"{owner_login}/{repo_name}"
    clone_url = repo.get('url', '')
    is_private = repo.get('isPrivate', False)
    
    return item(
        full_name,
        format_repo_subtitle(repo),
        f"{clone_url}|{is_private}"
    )


def fork_item_formatter(repo: Dict[str, Any]) -> Dict[str, Any]:
    """Format Alfred item for fork workflow."""
    from alfred import item
    
    owner = repo.get('owner', {})
    repo_name = repo.get('name', '')
    owner_login = owner.get('login', '') if isinstance(owner, dict) else str(owner)
    full_name = f"{owner_login}/{repo_name}"
    is_private = repo.get('isPrivate', False)
    
    # Create subtitle with fork indication
    subtitle_parts = []
    if repo.get('isFork', False):
        subtitle_parts.append("🍴 Fork")
    
    subtitle = format_repo_subtitle(repo)
    if subtitle_parts:
        subtitle = " • ".join(subtitle_parts) + " • " + subtitle
    
    return item(
        f"🍴 Fork {full_name}",
        subtitle,
        f"{full_name}|{is_private}",
        icon_type="default"
    )

