#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from config import get_workspace_dir
from github import fork_and_clone_repository
from git import get_unique_directory_name
from utils import show_notification, open_with_ide, open_in_finder

def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Usage: python3 github_fork_handler.py <repo_name>|<is_private>|<ide_path>", file=sys.stderr)
        sys.exit(1)
    
    # Parse arguments received from Alfred
    # Format: "owner/repo|is_private|ide_path"
    arg = sys.argv[1]
    
    parts = arg.split('|')
    if len(parts) == 3:
        repo_name, is_private_str, ide_path = parts
        is_private = is_private_str.lower() == 'true'
    else:
        print("Invalid argument format", file=sys.stderr)
        sys.exit(1)
    
    # Validate repository name
    if not repo_name or not repo_name.strip():
        print("Repository name cannot be empty", file=sys.stderr)
        sys.exit(1)
    
    repo_name = repo_name.strip()
    
    # Get workspace directory
    workspace_dir = get_workspace_dir()
    if not os.path.exists(workspace_dir):
        try:
            os.makedirs(workspace_dir, exist_ok=True)
        except OSError as e:
            print(f"Failed to create workspace directory: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Extract repository name for local directory
    local_repo_name = repo_name.split('/')[-1] if '/' in repo_name else repo_name
    target_path = get_unique_directory_name(workspace_dir, local_repo_name)
    final_repo_name = os.path.basename(target_path)
    
    # Show fork start notification
    show_notification("GitHub Fork", f"Forking repository '{repo_name}'...")
    
    # Execute GitHub fork and clone
    success, message = fork_and_clone_repository(repo_name, target_path)
    
    if success:
        # Show success notification
        show_notification("GitHub Fork Complete", f"Repository '{repo_name}' has been forked and cloned successfully")
        
        # Open with IDE
        if open_with_ide(ide_path, target_path):
            print(f"Success: {target_path} opened in {ide_path}")
        else:
            print(f"Repository forked and cloned successfully but failed to open IDE: {target_path}")
            # Open folder in Finder as fallback
            open_in_finder(target_path)
    else:
        # Show failure notification
        show_notification("GitHub Fork Failed", message)
        print(f"Failed: {message}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
