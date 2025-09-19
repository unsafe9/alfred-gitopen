#!/usr/bin/env python3
import os
import json
import sys
import subprocess
import threading
import time
import re
from pathlib import Path
from config import get_workspace_dir

def is_private_repo(git_url, is_private_meta=None):
    """Check if repository is private."""
    # If metadata is provided, use it
    if is_private_meta is not None:
        return is_private_meta
    
    # Fallback: check if it's from user's account
    try:
        result = subprocess.run(['gh', 'api', 'user'], capture_output=True, text=True)
        if result.returncode == 0:
            user_info = json.loads(result.stdout)
            username = user_info.get('login', '')
            
            # Check if URL contains the user's username
            if username and f'/{username}/' in git_url:
                return True
    except Exception:
        pass
    
    return False

def convert_to_ssh_url(git_url):
    """Convert HTTPS GitHub URL to SSH format."""
    # Pattern: https://github.com/owner/repo.git -> git@github.com:owner/repo.git
    https_pattern = r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
    match = re.match(https_pattern, git_url)
    
    if match:
        owner, repo = match.groups()
        return f"git@github.com:{owner}/{repo}.git"
    
    return git_url

def get_clone_method(git_url, is_private_meta=None):
    """Determine the best clone method based on repository type and user settings."""
    is_private = is_private_repo(git_url, is_private_meta)
    
    if is_private:
        method = os.environ.get('CLONE_METHOD_PRIVATE', 'ssh').lower()
    else:
        method = os.environ.get('CLONE_METHOD_PUBLIC', 'https').lower()
    
    return method

def clone_repository(git_url, target_dir, is_private_meta=None, progress_callback=None):
    """Clone a Git repository using the appropriate method."""
    try:
        clone_method = get_clone_method(git_url, is_private_meta)
        
        if clone_method == 'gh':
            # Use GitHub CLI to clone (handles authentication automatically)
            cmd = ['gh', 'repo', 'clone', git_url, target_dir]
        else:
            # Use git clone with URL conversion if needed
            if clone_method == 'ssh' and git_url.startswith('https://github.com/'):
                git_url = convert_to_ssh_url(git_url)
            elif clone_method == 'https' and git_url.startswith('git@github.com:'):
                # Convert SSH to HTTPS (reverse conversion)
                ssh_pattern = r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$'
                match = re.match(ssh_pattern, git_url)
                if match:
                    owner, repo = match.groups()
                    git_url = f"https://github.com/{owner}/{repo}.git"
            
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
            # If SSH fails, try HTTPS as fallback for public repos
            if clone_method == 'ssh' and not is_private_repo(git_url, is_private_meta):
                https_url = git_url
                if git_url.startswith('git@github.com:'):
                    ssh_pattern = r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$'
                    match = re.match(ssh_pattern, git_url)
                    if match:
                        owner, repo = match.groups()
                        https_url = f"https://github.com/{owner}/{repo}.git"
                
                # Try HTTPS fallback
                cmd = ['git', 'clone', https_url, target_dir]
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    return True, f"Successfully cloned to: {target_dir} (using HTTPS fallback)"
            
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
    # Format: "git_url|is_private|ide_path" or "git_url|ide_path"
    arg = sys.argv[1]
    
    try:
        parts = arg.split('|')
        if len(parts) == 3:
            # New format with privacy metadata
            git_url, is_private_str, ide_path = parts
            is_private_meta = is_private_str.lower() == 'true'
        elif len(parts) == 2:
            # Old format or direct URL
            git_url, ide_path = parts
            is_private_meta = None
        else:
            print("Invalid argument format", file=sys.stderr)
            sys.exit(1)
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
    success, message = clone_repository(git_url, target_path, is_private_meta)
    
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

