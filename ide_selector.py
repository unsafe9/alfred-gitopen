#!/usr/bin/env python3
import os
import sys
from config import get_ides_to_check, get_app_search_paths
from alfred import output, error_item, item, handle_error

def find_app_path(app_name):
    """Checks for an app in standard macOS application directories."""
    app_name = app_name + ".app"
    
    # Get search paths from config
    search_paths = get_app_search_paths()
    
    # Return the first path that exists
    for search_path in search_paths:
        full_path = search_path / app_name
        if full_path.exists():
            return str(full_path)
    return None


def main():
    """Main execution function."""
    # The repository path or git URL is expected as a command-line argument from Alfred
    if len(sys.argv) < 2:
        handle_error("Error: No repository path or Git URL provided", "This script expects a repository path or Git URL as an argument.")
        
    input_arg = sys.argv[1]
    
    # Check if input is a Git URL (starts with http, https, git@ or contains .git)
    is_git_url = (input_arg.startswith(('http://', 'https://', 'git@')) or 
                  '.git' in input_arg)
    
    # Check if input is an existing directory path
    is_existing_path = os.path.isdir(input_arg)
    
    if is_git_url:
        # For Git URLs, prepare for clone operation and IDE selection
        git_url = input_arg
        title_prefix = "Clone & Open with"
        arg_format = f"{git_url}|{{app_path}}"
    elif is_existing_path:
        # For existing local paths
        repo_path = input_arg
        title_prefix = "Open with"
        arg_format = f"{{app_path}}|{repo_path}"
    else:
        # For repository names (gitinit workflow)
        repo_name = input_arg
        title_prefix = "Init & Open with"
        arg_format = f"{repo_name}|{{app_path}}"

    found_ides = []
    # Get IDEs to check from config
    ides_to_check = get_ides_to_check()
    
    # Iterate through the list of IDEs to check
    for ide_id, app_name in ides_to_check:
        app_path = find_app_path(app_name)
        if app_path:
            # If an IDE is found, create an Alfred item for it
            alfred_item = item(f"{title_prefix} {app_name}", app_path, arg_format.format(app_path=app_path), icon_type="fileicon")
            alfred_item["icon"]["path"] = app_path
            found_ides.append(alfred_item)

    # Output the results in Alfred's JSON format
    if not found_ides:
        not_found_item_result = item("No supported IDEs found.", "Checked paths from APP_SEARCH_PATHS", valid=False)
        output([not_found_item_result])
    else:
        output(found_ides)

if __name__ == "__main__":
    main()
