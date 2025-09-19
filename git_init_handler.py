#!/usr/bin/env python3
import os
import json
import sys
import subprocess
from pathlib import Path
from config import get_workspace_dir

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
        result = subprocess.run(
            ['git', 'init'],
            cwd=target_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Clean up directory if git init failed
            try:
                os.rmdir(target_path)
            except OSError:
                pass
            return False, f"Failed to initialize Git repository: {result.stderr}"
        
        return True, target_path
        
    except Exception as e:
        return False, f"Error creating repository: {str(e)}"

def open_with_ide(ide_path, project_path):
    """Open project with selected IDE."""
    try:
        subprocess.run(['open', '-a', ide_path, project_path], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def show_notification(title, message):
    """Show macOS notification."""
    try:
        cmd = [
            'osascript', '-e',
            f'display notification "{message}" with title "{title}"'
        ]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        pass  # Ignore notification failures

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
    if not repo_name or not repo_name.strip():
        print("Repository name cannot be empty", file=sys.stderr)
        sys.exit(1)
    
    repo_name = repo_name.strip()
    
    # Check for invalid characters in repository name (macOS filesystem)
    invalid_chars = ['/', ':']
    if any(char in repo_name for char in invalid_chars):
        print(f"Repository name contains invalid characters: {', '.join(invalid_chars)}", file=sys.stderr)
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
            subprocess.run(['open', project_path])
    else:
        error_message = result
        # Show failure notification
        show_notification("Git Init Failed", error_message)
        print(f"Failed: {error_message}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
