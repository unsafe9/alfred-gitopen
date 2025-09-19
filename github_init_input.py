#!/usr/bin/env python3
import sys
from github import check_gh_cli, is_valid_repo_name, check_repo_exists
from alfred import output, error_item, item, handle_empty_query, get_query_from_argv

def main():
    """Main execution function."""
    # Check GitHub CLI
    is_available, error_msg = check_gh_cli()
    if not is_available:
        alfred_error_item = error_item("GitHub CLI Required", error_msg)
        output([alfred_error_item])
        return
    
    # Get query from Alfred (repository name input)
    query = get_query_from_argv()
    
    if not query.strip():
        handle_empty_query("Enter GitHub repository name", "Type the name for your new GitHub repository")
        return
    
    repo_name = query.strip()
    
    # Validate repository name
    is_valid, error_message = is_valid_repo_name(repo_name)
    
    if not is_valid:
        # Show error message
        alfred_error_item = error_item("Invalid repository name", error_message)
        output([alfred_error_item])
        return
    
    # Check if repository already exists
    if check_repo_exists(repo_name):
        alfred_error_item = error_item(
            f"Repository '{repo_name}' already exists",
            "Choose a different name or use githubclone to clone the existing repository"
        )
        output([alfred_error_item])
        return
    
    # Show valid repository name ready to create
    alfred_item = item(f"Create GitHub repository '{repo_name}'", "Initialize new repository on GitHub and clone locally", repo_name)
    output([alfred_item])

if __name__ == "__main__":
    main()