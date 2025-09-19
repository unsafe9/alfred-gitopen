#!/usr/bin/env python3
import os
import json
import sys
import subprocess
import threading
import time
from pathlib import Path
from config import get_workspace_dir

def clone_repository(git_url, target_dir, progress_callback=None):
    """Clone a Git repository."""
    try:
        # Execute git clone command
        cmd = ['git', 'clone', git_url, target_dir]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            return True, f"Successfully cloned to: {target_dir}"
        else:
            return False, f"Clone failed: {stderr}"
    
    except Exception as e:
        return False, f"Error occurred: {str(e)}"

def get_repo_name_from_url(git_url):
    """Extract repository name from Git URL."""
    # Extract repository name from URL
    repo_name = git_url.rstrip('/').split('/')[-1]
    
    # Remove .git extension
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    
    return repo_name

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
        print("Usage: python3 git_clone_handler.py <git_url>|<ide_path>", file=sys.stderr)
        sys.exit(1)
    
    # Parse arguments received from Alfred
    # Format: "git_url|ide_path"
    arg = sys.argv[1]
    
    try:
        git_url, ide_path = arg.split('|', 1)
    except ValueError:
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
    
    # Extract repository name
    repo_name = get_repo_name_from_url(git_url)
    target_path = os.path.join(workspace_dir, repo_name)
    
    # Check if directory already exists
    if os.path.exists(target_path):
        # Generate unique name
        counter = 1
        while os.path.exists(f"{target_path}_{counter}"):
            counter += 1
        target_path = f"{target_path}_{counter}"
        repo_name = f"{repo_name}_{counter}"
    
    # Show clone start notification
    show_notification("Git Clone", f"Starting to clone {repo_name}...")
    
    # Execute Git clone
    success, message = clone_repository(git_url, target_path)
    
    if success:
        # Show success notification
        show_notification("Git Clone Complete", f"{repo_name} has been successfully cloned")
        
        # Open with IDE
        if open_with_ide(ide_path, target_path):
            print(f"Success: {target_path} opened in {ide_path}")
        else:
            print(f"Clone successful but failed to open IDE: {target_path}")
            # Open folder in Finder as fallback
            subprocess.run(['open', target_path])
    else:
        # Show failure notification
        show_notification("Git Clone Failed", message)
        print(f"Failed: {message}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

