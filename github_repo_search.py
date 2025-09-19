#!/usr/bin/env python3
import os
import json
import sys
import subprocess
import re

def check_gh_cli():
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

def search_github_repos(query, limit=20):
    """Search GitHub repositories using GitHub CLI."""
    try:
        # Search repositories with various filters
        cmd = [
            'gh', 'repo', 'list', 
            '--limit', str(limit),
            '--json', 'name,owner,description,url,isPrivate,stargazersCount,updatedAt'
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
            return [], f"GitHub search failed: {result.stderr}"
        
        repos = json.loads(result.stdout)
        return repos, ""
        
    except Exception as e:
        return [], f"Error searching repositories: {str(e)}"

def get_user_repos(limit=50):
    """Get user's own repositories (including private ones)."""
    try:
        cmd = [
            'gh', 'repo', 'list',
            '--limit', str(limit),
            '--json', 'name,owner,description,url,isPrivate,stargazersCount,updatedAt'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return [], f"Failed to get user repositories: {result.stderr}"
        
        repos = json.loads(result.stdout)
        return repos, ""
        
    except Exception as e:
        return [], f"Error getting user repositories: {str(e)}"

def format_repo_subtitle(repo):
    """Format repository subtitle with useful information."""
    parts = []
    
    # Add privacy indicator
    if repo.get('isPrivate'):
        parts.append("🔒 Private")
    else:
        parts.append("🌐 Public")
    
    # Add star count
    stars = repo.get('stargazersCount', 0)
    if stars > 0:
        if stars >= 1000:
            parts.append(f"⭐ {stars/1000:.1f}k")
        else:
            parts.append(f"⭐ {stars}")
    
    # Add description if available
    description = repo.get('description', '').strip()
    if description:
        # Limit description length
        if len(description) > 60:
            description = description[:57] + "..."
        parts.append(description)
    
    return " • ".join(parts)

def create_alfred_output(items):
    """Create JSON output for Alfred."""
    alfred_json = {"items": items}
    sys.stdout.write(json.dumps(alfred_json, indent=4))

def main():
    """Main execution function."""
    # Get query from Alfred
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    
    # Check GitHub CLI
    is_available, error_msg = check_gh_cli()
    if not is_available:
        error_item = {
            "title": "GitHub CLI Required",
            "subtitle": error_msg,
            "valid": False,
            "icon": {"type": "default"}
        }
        create_alfred_output([error_item])
        sys.exit(0)
    
    if not query.strip():
        # Show instruction when no input
        item = {
            "title": "Search GitHub repositories",
            "subtitle": "Type repository name, owner/repo, or keywords to search",
            "valid": False,
            "icon": {"type": "default"}
        }
        create_alfred_output([item])
        sys.exit(0)
    
    query = query.strip()
    
    # Search repositories
    repos, error_msg = search_github_repos(query)
    
    if error_msg:
        error_item = {
            "title": "Search failed",
            "subtitle": error_msg,
            "valid": False,
            "icon": {"type": "default"}
        }
        create_alfred_output([error_item])
        sys.exit(0)
    
    if not repos:
        # If no results from search, try getting user's repos if query matches
        user_repos, user_error = get_user_repos()
        if not user_error:
            # Filter user repos by query
            filtered_repos = []
            for repo in user_repos:
                repo_name = repo.get('name', '').lower()
                repo_full = f"{repo.get('owner', {}).get('login', '')}/{repo_name}".lower()
                if (query.lower() in repo_name or 
                    query.lower() in repo_full or 
                    query.lower() in repo.get('description', '').lower()):
                    filtered_repos.append(repo)
            repos = filtered_repos
    
    if not repos:
        not_found_item = {
            "title": "No repositories found",
            "subtitle": f"No GitHub repositories found for '{query}'",
            "valid": False,
            "icon": {"type": "default"}
        }
        create_alfred_output([not_found_item])
        sys.exit(0)
    
    alfred_items = []
    for repo in repos:
        owner = repo.get('owner', {}).get('login', 'unknown')
        name = repo.get('name', 'unknown')
        url = repo.get('url', '')
        
        # Use HTTPS URL for cloning
        # Prepare clone URL
        clone_url = url
        if url.startswith('https://github.com/') and not url.endswith('.git'):
            clone_url = url + '.git'
        
        # Add repository metadata for clone method determination
        clone_url_with_meta = f"{clone_url}|{repo.get('isPrivate', False)}"
        
        subtitle = format_repo_subtitle(repo)
        
        item = {
            "uid": url,
            "title": f"{owner}/{name}",
            "subtitle": subtitle,
            "arg": clone_url_with_meta,
            "icon": {"type": "default"},
            "mods": {
                "cmd": {
                    "subtitle": f"Open {url} in browser",
                    "arg": url
                }
            }
        }
        alfred_items.append(item)
    
    create_alfred_output(alfred_items)

if __name__ == "__main__":
    main()
