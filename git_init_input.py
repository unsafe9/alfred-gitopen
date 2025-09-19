#!/usr/bin/env python3
import os
import sys
import re
from alfred import output, error_item, item, handle_empty_query, get_query_from_argv
from git import validate_local_repo_name


def main():
    """Main execution function."""
    # Get query from Alfred (repository name input)
    query = get_query_from_argv()
    
    if not query.strip():
        handle_empty_query("Enter repository name", "Type the name for your new Git repository")
    
    repo_name = query.strip()
    
    # Validate repository name
    is_valid, error_message = validate_local_repo_name(repo_name)
    
    if not is_valid:
        # Show error message
        alfred_error_item = error_item("Invalid repository name", error_message)
        output([alfred_error_item])
        sys.exit(0)
    
    # Check if directory already exists in workspace
    from config import get_workspace_dir
    workspace_dir = get_workspace_dir()
    target_path = os.path.join(workspace_dir, repo_name)
    
    if os.path.exists(target_path):
        # Show error for existing directory
        alfred_error_item = error_item(f"Directory '{repo_name}' already exists", f"Choose a different name or remove existing directory: {target_path}")
        output([alfred_error_item])
        sys.exit(0)
    
    # Show valid repository name ready to create
    alfred_item = item(f"Create Git repository '{repo_name}'", f"Initialize new Git repository in: {target_path}", repo_name)
    output([alfred_item])

if __name__ == "__main__":
    main()
