#!/usr/bin/env python3
import sys
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
        handle_empty_query("Search GitHub repositories", "Type repository name, owner/repo, or keywords to search")
        return
    
    try:
        items = []
        
        # Search public repositories
        search_repos = search_github_repos(query, limit=15)
        
        # Get user's own repositories (including private)
        user_repos = get_user_repos(limit=10)
        
        # Combine and deduplicate repositories
        all_repos = []
        seen_urls = set()
        
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
        
        # Create Alfred items
        for repo in all_repos[:20]:  # Limit to 20 results
            owner = repo.get('owner', {})
            repo_name = repo.get('name', '')
            full_name = f"{owner.get('login', '')}/{repo_name}"
            clone_url = repo.get('url', '')
            
            # Include privacy metadata in the argument
            clone_url_with_meta = f"{clone_url}|{repo.get('isPrivate', False)}"
            
            alfred_item = item(full_name, format_repo_subtitle(repo), clone_url_with_meta)
            items.append(alfred_item)
        
        if not items:
            # No repositories found
            no_results_item_result = item("No repositories found", f"No GitHub repositories found for '{query}'", valid=False)
            items.append(no_results_item_result)
        
        output(items)
        
    except Exception as e:
        # Show error message
        alfred_error_item = error_item("Search failed", f"GitHub search failed: {str(e)}")
        output([alfred_error_item])

if __name__ == "__main__":
    main()