#!/usr/bin/env python3
import sys
import subprocess
from github import check_gh_cli, search_github_repos, get_user_repos, format_repo_subtitle
from alfred import output, error_item, item, handle_empty_query, get_query_from_argv

def main():
    """Main execution function."""
    # Check if GitHub CLI is available
    is_available, error_msg = check_gh_cli()
    if not is_available:
        alfred_error_item = error_item("GitHub CLI Required", error_msg)
        output([alfred_error_item])
        return
    
    # Get query from Alfred
    query = get_query_from_argv()
    
    if not query.strip():
        handle_empty_query("Search GitHub repositories to fork", "Type repository name, owner/repo, or keywords to search")
        return
    
    try:
        items = []
        
        # Search public repositories (focus on popular ones for forking)
        search_repos = search_github_repos(query, limit=20)
        
        # Filter out user's own repositories (can't fork your own repos)
        try:
            user_result = subprocess.run(['gh', 'api', 'user'], capture_output=True, text=True)
            if user_result.returncode == 0:
                import json
                user_info = json.loads(user_result.stdout)
                current_username = user_info.get('login', '')
            else:
                current_username = ''
        except Exception:
            current_username = ''
        
        # Create Alfred items for repositories that can be forked
        for repo in search_repos:
            owner = repo.get('owner', {})
            repo_name = repo.get('name', '')
            owner_login = owner.get('login', '') if isinstance(owner, dict) else str(owner)
            full_name = f"{owner_login}/{repo_name}"
            
            # Skip user's own repositories
            if owner_login == current_username:
                continue
            
            # Skip if it's already a fork (optional - you can fork forks)
            # if repo.get('isFork', False):
            #     continue
            
            clone_url = repo.get('url', '')
            is_private = repo.get('isPrivate', False)
            
            # Create subtitle with fork indication
            subtitle_parts = []
            if repo.get('isFork', False):
                subtitle_parts.append("🍴 Fork")
            
            # Add standard subtitle parts
            subtitle = format_repo_subtitle(repo)
            if subtitle_parts:
                subtitle = " • ".join(subtitle_parts) + " • " + subtitle
            
            alfred_item = item(
                f"🍴 Fork {full_name}", 
                subtitle, 
                f"{full_name}|{is_private}",
                icon_type="default"
            )
            items.append(alfred_item)
        
        if not items:
            # No repositories found
            no_results_item_result = item("No repositories found", f"No forkable repositories found for '{query}'", valid=False)
            items.append(no_results_item_result)
        
        output(items)
        
    except Exception as e:
        # Show error message
        alfred_error_item = error_item("Search failed", f"GitHub search failed: {str(e)}")
        output([alfred_error_item])

if __name__ == "__main__":
    main()
