#!/usr/bin/env python3
import os
import json
import sys
from config import get_workspace_dir, get_max_depth

def find_git_repos(workspace_dir, max_depth):
    """Finds git repositories within a given directory."""
    repo_paths = []
    start_level = workspace_dir.count(os.sep)

    for root, dirs, _ in os.walk(workspace_dir):
        current_level = root.count(os.sep)
        if current_level - start_level >= max_depth:
            del dirs[:]  # Stop searching deeper in this path
            continue

        if ".git" in dirs:
            repo_paths.append(root)
            dirs.remove(".git") # Don't search inside the .git folder
    
    return repo_paths

def create_alfred_output(items):
    """Creates and prints the JSON output for Alfred."""
    alfred_json = {"items": items}
    sys.stdout.write(json.dumps(alfred_json, indent=4))


def main():
    """Main execution function."""
    # Get settings from config
    workspace_dir = get_workspace_dir()
    max_depth = get_max_depth()

    if not workspace_dir or not os.path.isdir(workspace_dir):
        error_item = {
            "title": "Error: WORKSPACE_DIR is not set or invalid",
            "subtitle": f"Please set the WORKSPACE_DIR environment variable. Current value: '{workspace_dir}'",
            "valid": False,
        }
        create_alfred_output([error_item])
        sys.exit(1)

    repo_list = find_git_repos(workspace_dir, max_depth)

    if not repo_list:
        not_found_item = {
            "title": "No Git repositories found",
            "subtitle": f"Searched in: {workspace_dir}",
            "valid": False,
        }
        create_alfred_output([not_found_item])
        sys.exit(0)

    alfred_items = []
    for repo_path in sorted(repo_list): # Sort alphabetically
        repo_name = os.path.basename(repo_path)
        item = {
            "uid": repo_path,
            "title": repo_name,
            "subtitle": repo_path,
            "arg": repo_path,
            "icon": {"type": "fileicon", "path": repo_path},
        }
        alfred_items.append(item)

    create_alfred_output(alfred_items)


if __name__ == "__main__":
    main()
