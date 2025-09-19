#!/usr/bin/env python3
import os
import sys
from config import get_workspace_dir, get_max_depth
from alfred import output, error_item, item, handle_error

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



def main():
    """Main execution function."""
    # Get settings from config
    workspace_dir = get_workspace_dir()
    max_depth = get_max_depth()

    if not workspace_dir or not os.path.isdir(workspace_dir):
        handle_error("Error: WORKSPACE_DIR is not set or invalid", f"Please set the WORKSPACE_DIR environment variable. Current value: '{workspace_dir}'")

    repo_list = find_git_repos(workspace_dir, max_depth)

    if not repo_list:
        not_found_item_result = item("No Git repositories found", f"Searched in: {workspace_dir}", valid=False)
        output([not_found_item_result])
        sys.exit(0)

    alfred_items = []
    for repo_path in sorted(repo_list): # Sort alphabetically
        repo_name = os.path.basename(repo_path)
        alfred_item = item(repo_name, repo_path, repo_path, icon_type="fileicon", uid=repo_path)
        alfred_item["icon"]["path"] = repo_path
        alfred_items.append(alfred_item)

    output(alfred_items)


if __name__ == "__main__":
    main()
