#!/usr/bin/env python3
import os
import json
import sys
import re

def is_valid_repo_name(name):
    """Check if repository name is valid."""
    if not name or not name.strip():
        return False, "Repository name cannot be empty"
    
    name = name.strip()
    
    # Check for invalid characters (macOS filesystem)
    invalid_chars = ['/', ':']
    if any(char in name for char in invalid_chars):
        return False, f"Repository name contains invalid characters: {', '.join(invalid_chars)}"
    
    # Check if name starts or ends with dot or space
    if name.startswith('.') or name.endswith('.') or name.startswith(' ') or name.endswith(' '):
        return False, "Repository name cannot start or end with dot or space"
    
    # Check length
    if len(name) > 255:
        return False, "Repository name is too long (maximum 255 characters)"
    
    return True, ""

def create_alfred_output(items):
    """Create JSON output for Alfred."""
    alfred_json = {"items": items}
    sys.stdout.write(json.dumps(alfred_json, indent=4))

def main():
    """Main execution function."""
    # Get query from Alfred (repository name input)
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    
    if not query.strip():
        # Show instruction when no input
        item = {
            "title": "Enter repository name",
            "subtitle": "Type the name for your new Git repository",
            "valid": False,
            "icon": {"type": "default"}
        }
        create_alfred_output([item])
        sys.exit(0)
    
    repo_name = query.strip()
    
    # Validate repository name
    is_valid, error_message = is_valid_repo_name(repo_name)
    
    if not is_valid:
        # Show error message
        error_item = {
            "title": "Invalid repository name",
            "subtitle": error_message,
            "valid": False,
            "icon": {"type": "default"}
        }
        create_alfred_output([error_item])
        sys.exit(0)
    
    # Check if directory already exists in workspace
    from config import get_workspace_dir
    workspace_dir = get_workspace_dir()
    target_path = os.path.join(workspace_dir, repo_name)
    
    if os.path.exists(target_path):
        # Show error for existing directory
        error_item = {
            "title": f"Directory '{repo_name}' already exists",
            "subtitle": f"Choose a different name or remove existing directory: {target_path}",
            "valid": False,
            "icon": {"type": "default"}
        }
        create_alfred_output([error_item])
        sys.exit(0)
    
    # Show valid repository name ready to create
    item = {
        "title": f"Create Git repository '{repo_name}'",
        "subtitle": f"Initialize new Git repository in: {target_path}",
        "arg": repo_name,
        "icon": {"type": "default"}
    }
    create_alfred_output([item])

if __name__ == "__main__":
    main()
