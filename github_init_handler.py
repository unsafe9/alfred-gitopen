#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
from config import get_workspace_dir
from github import create_github_repository, clone_github_repository, delete_github_repository
from git import get_unique_directory_name
from utils import show_notification, open_with_ide, open_in_finder

def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Usage: python3 github_init_handler.py <repo_name>|<ide_path>", file=sys.stderr)
        sys.exit(1)
    
    # Parse arguments received from Alfred
    # Format: "repo_name|ide_path"
    arg = sys.argv[1]
    
    try:
        repo_name, ide_path = arg.split('|', 1)
    except ValueError:
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
    
    # Set target path with unique name if needed
    target_path = get_unique_directory_name(workspace_dir, repo_name)
    repo_name_local = os.path.basename(target_path)
    
    # Show creation start notification
    show_notification("GitHub Init", f"Creating repository '{repo_name}' on GitHub...")
    
    # Create GitHub repository
    success, message = create_github_repository(repo_name, private=True)
    
    if not success:
        # Show failure notification
        show_notification("GitHub Init Failed", message)
        print(f"Failed: {message}", file=sys.stderr)
        sys.exit(1)
    
    # Show clone start notification
    show_notification("GitHub Clone", f"Cloning repository to local workspace...")
    
    # Clone the repository
    success, message = clone_github_repository(repo_name, target_path)
    
    if success:
        # Show success notification
        show_notification("GitHub Init Complete", f"Repository '{repo_name}' created and cloned successfully")
        
        # Open with IDE
        if open_with_ide(ide_path, target_path):
            print(f"Success: {target_path} opened in {ide_path}")
        else:
            print(f"Repository created and cloned successfully but failed to open IDE: {target_path}")
            # Open folder in Finder as fallback
            open_in_finder(target_path)
    else:
        # Clone failed, but repository was created on GitHub
        show_notification("GitHub Clone Failed", f"Repository created on GitHub but clone failed: {message}")
        print(f"Repository created on GitHub but clone failed: {message}", file=sys.stderr)
        
        # Try to delete the repository on GitHub since clone failed
        try:
            delete_github_repository(repo_name)
        except Exception:
            pass  # Ignore cleanup errors
        
        sys.exit(1)

if __name__ == "__main__":
    main()