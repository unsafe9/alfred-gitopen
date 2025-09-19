#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
from config import get_workspace_dir
from utils import show_notification, open_with_ide, open_in_finder
from alfred import print_error
from git import init_repository, validate_local_repo_name

def create_and_init_repository(repo_name, workspace_dir):
    """Create a new directory and initialize it as a Git repository."""
    try:
        # Create target directory path
        target_path = os.path.join(workspace_dir, repo_name)
        
        # Check if directory already exists
        if os.path.exists(target_path):
            return False, f"Directory '{repo_name}' already exists in workspace"
        
        # Create the directory
        os.makedirs(target_path, exist_ok=True)
        
        # Initialize Git repository
        success, message = init_repository(target_path)
        
        if not success:
            # Clean up directory if git init failed
            try:
                os.rmdir(target_path)
            except OSError:
                pass
            return False, message
        
        return True, target_path
        
    except Exception as e:
        return False, f"Error creating repository: {str(e)}"


def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Usage: python3 git_init_handler.py <repo_name>|<ide_path>", file=sys.stderr)
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
    is_valid, error_message = validate_local_repo_name(repo_name)
    if not is_valid:
        print(error_message, file=sys.stderr)
        sys.exit(1)
    
    # Get workspace directory
    workspace_dir = get_workspace_dir()
    if not os.path.exists(workspace_dir):
        try:
            os.makedirs(workspace_dir, exist_ok=True)
        except OSError as e:
            print(f"Failed to create workspace directory: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Show initialization start notification
    show_notification("Git Init", f"Creating new repository '{repo_name}'...")
    
    # Create and initialize Git repository
    success, result = create_and_init_repository(repo_name, workspace_dir)
    
    if success:
        project_path = result
        # Show success notification
        show_notification("Git Init Complete", f"Repository '{repo_name}' has been created and initialized")
        
        # Open with IDE
        if open_with_ide(ide_path, project_path):
            print(f"Success: {project_path} opened in {ide_path}")
        else:
            print(f"Repository created successfully but failed to open IDE: {project_path}")
            # Open folder in Finder as fallback
            open_in_finder(project_path)
    else:
        error_message = result
        # Show failure notification
        show_notification("Git Init Failed", error_message)
        print(f"Failed: {error_message}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
