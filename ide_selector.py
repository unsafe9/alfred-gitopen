#!/usr/bin/env python3
import os
import json
import sys
from config import get_ides_to_check, get_app_search_paths

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

def create_alfred_output(items):
    """Creates and prints the JSON output for Alfred."""
    alfred_json = {"items": items}
    sys.stdout.write(json.dumps(alfred_json, indent=4))

def main():
    """Main execution function."""
    # The repository path is expected as a command-line argument from Alfred
    if len(sys.argv) < 2:
        error_item = {
            "title": "Error: No repository path provided",
            "subtitle": "This script expects a repository path as an argument.",
            "valid": False,
        }
        create_alfred_output([error_item])
        sys.exit(1)
        
    repo_path = sys.argv[1]

    found_ides = []
    # Get IDEs to check from config
    ides_to_check = get_ides_to_check()
    
    # Iterate through the list of IDEs to check
    for ide_id, app_name in ides_to_check:
        app_path = find_app_path(app_name)
        if app_path:
            # If an IDE is found, create an Alfred item for it
            item = {
                "title": app_name,
                "subtitle": f"{app_path}",
                "arg": f"{app_path}|{repo_path}",
                "icon": {"type": "fileicon", "path": app_path},
            }
            found_ides.append(item)

    # Output the results in Alfred's JSON format
    if not found_ides:
        not_found_item = {
            "title": "No supported IDEs found.",
            "subtitle": "Checked paths from APP_SEARCH_PATHS",
            "valid": False,
        }
        create_alfred_output([not_found_item])
    else:
        create_alfred_output(found_ides)

if __name__ == "__main__":
    main()
