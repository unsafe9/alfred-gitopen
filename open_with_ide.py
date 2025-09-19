#!/usr/bin/env python3
"""
Open project with selected IDE.
Usage: python3 open_with_ide.py "app_path|repo_path"
"""
import sys
from utils import open_with_ide
from alfred import print_error, get_query_from_argv

def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print_error("Usage: python3 open_with_ide.py <app_path>|<repo_path>")
        sys.exit(1)
    
    # Parse argument: "app_path|repo_path"
    arg = get_query_from_argv()
    
    # Check if argument is empty
    if not arg or not arg.strip():
        print_error("Empty argument received. Expected: app_path|repo_path")
        sys.exit(1)
    
    # Check if argument contains the pipe separator
    if '|' not in arg:
        print_error(f"Invalid argument format. Expected: app_path|repo_path, but got: '{arg}'")
        sys.exit(1)
    
    try:
        app_path, repo_path = arg.split('|', 1)
        
        # Validate that both parts are not empty
        if not app_path.strip() or not repo_path.strip():
            print_error(f"Invalid argument format. Both app_path and repo_path must be non-empty. Got: '{arg}'")
            sys.exit(1)
            
    except ValueError:
        print_error(f"Invalid argument format. Expected: app_path|repo_path, but got: '{arg}'")
        sys.exit(1)
    
    # Open project with IDE
    if open_with_ide(app_path, repo_path):
        print(f"Success: Opened {repo_path} with {app_path}")
    else:
        print_error(f"Failed to open {repo_path} with {app_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
