#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from config import get_workspace_dir
from utils import show_notification, open_with_ide, open_in_finder
from alfred import print_error
from git import get_repository_name_from_url, get_unique_directory_name
from github import clone_repository_with_method

def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Usage: python3 git_clone_handler.py <git_url>|<ide_path>", file=sys.stderr)
        sys.exit(1)
    
    # Parse arguments received from Alfred
    # Format: "git_url|is_private|ide_path" or "git_url|ide_path"
    arg = sys.argv[1]
    
    parts = arg.split('|')
    if len(parts) == 3:
        git_url, is_private_str, ide_path = parts
        is_private_meta = is_private_str.lower() == 'true'
    elif len(parts) == 2:
        git_url, ide_path = parts
        is_private_meta = None
    else:
        print("Invalid argument format", file=sys.stderr)
        sys.exit(1)
    
    # Get workspace directory
    workspace_dir = get_workspace_dir()
    if not os.path.exists(workspace_dir):
        try:
            os.makedirs(workspace_dir, exist_ok=True)
        except OSError as e:
            print(f"Failed to create workspace directory: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Extract repository name and get unique path
    repo_name = get_repository_name_from_url(git_url)
    target_path = get_unique_directory_name(workspace_dir, repo_name)
    final_repo_name = os.path.basename(target_path)
    
    # Show clone start notification
    show_notification("Git Clone", f"Starting to clone {final_repo_name}...")
    
    # Execute Git clone using GitHub-aware method
    success, message = clone_repository_with_method(git_url, target_path, is_private_meta)
    
    if success:
        # Show success notification
        show_notification("Git Clone Complete", f"{final_repo_name} has been successfully cloned")
        
        # Open with IDE
        if open_with_ide(ide_path, target_path):
            print(f"Success: {target_path} opened in {ide_path}")
        else:
            print(f"Clone successful but failed to open IDE: {target_path}")
            # Open folder in Finder as fallback
            open_in_finder(target_path)
    else:
        # Show failure notification
        show_notification("Git Clone Failed", message)
        print(f"Failed: {message}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()