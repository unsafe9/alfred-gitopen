#!/usr/bin/env python3
"""
Alfred-specific utilities for Alfred Git Open workflow.
"""
import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

def output(items: List[Dict[str, Any]]) -> None:
    """Create JSON output for Alfred."""
    alfred_json = {"items": items}
    sys.stdout.write(json.dumps(alfred_json, indent=4))

def error_item(title: str, subtitle: str) -> Dict[str, Any]:
    """Create an error item for Alfred output."""
    return {
        "title": title,
        "subtitle": subtitle,
        "valid": False,
        "icon": {"type": "default"}
    }

def item(title: str, subtitle: str, arg: str = "", valid: bool = True, 
         icon_type: str = "default", autocomplete: str = None, 
         uid: str = None) -> Dict[str, Any]:
    """Create a standard Alfred item."""
    item_dict = {
        "title": title,
        "subtitle": subtitle,
        "arg": arg,
        "valid": valid,
        "icon": {"type": icon_type}
    }
    
    if autocomplete:
        item_dict["autocomplete"] = autocomplete
    
    if uid:
        item_dict["uid"] = uid
    
    return item_dict

def get_alfred_clipboard_history(limit: int = 50) -> List[str]:
    """Get clipboard history from Alfred's database."""
    try:
        # Path to Alfred's clipboard history database
        db_path = Path.home() / "Library/Application Support/Alfred/Databases/clipboard.alfdb"
        
        if not db_path.exists():
            return []
        
        # Connect to the database and query clipboard history
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Query to get the most recent text entries
        query = f"SELECT item FROM clipboard WHERE dataType = 0 ORDER BY ts DESC LIMIT {limit}"
        cursor.execute(query)
        
        clipboard_items = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return clipboard_items
    
    except Exception as e:
        print_debug(f"Error accessing clipboard history: {e}")
        return []

def get_alfred_preferences_path() -> Path:
    """Get Alfred preferences path."""
    # Check for custom preferences location
    prefs_path = os.environ.get('ALFRED_PREFERENCES_PATH')
    if prefs_path:
        return Path(prefs_path)
    
    # Default location
    return Path.home() / "Library/Application Support/Alfred"

def get_alfred_workflow_data_path() -> Path:
    """Get Alfred workflow data directory."""
    workflow_uid = os.environ.get('alfred_workflow_uid', 'unknown')
    return get_alfred_preferences_path() / "Workflow Data" / workflow_uid

def get_alfred_workflow_cache_path() -> Path:
    """Get Alfred workflow cache directory."""
    workflow_uid = os.environ.get('alfred_workflow_uid', 'unknown')
    return get_alfred_preferences_path() / "Workflow Cache" / workflow_uid

def ensure_alfred_directories() -> None:
    """Ensure Alfred workflow directories exist."""
    data_path = get_alfred_workflow_data_path()
    cache_path = get_alfred_workflow_cache_path()
    
    data_path.mkdir(parents=True, exist_ok=True)
    cache_path.mkdir(parents=True, exist_ok=True)

def get_alfred_variable(key: str, default: str = "") -> str:
    """Get Alfred workflow variable."""
    return os.environ.get(key, default)

def set_alfred_variable(key: str, value: str) -> None:
    """Set Alfred workflow variable for next action."""
    # Alfred reads variables from stdout in specific format
    print(f'{{\"alfredworkflow\": {{\"variables\": {{\"{key}\": \"{value}\"}}}}}}')

def log_to_alfred(message: str, level: str = "INFO") -> None:
    """Log message to Alfred's debug console."""
    timestamp = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] {message}", file=sys.stderr)

def print_debug(message: str) -> None:
    """Print debug message to stderr if DEBUG is set."""
    if os.environ.get('DEBUG') or os.environ.get('alfred_debug'):
        log_to_alfred(message, "DEBUG")

def print_error(message: str) -> None:
    """Print error message to stderr."""
    log_to_alfred(f"Error: {message}", "ERROR")

def print_info(message: str) -> None:
    """Print info message to stderr."""
    log_to_alfred(message, "INFO")

def get_query_from_argv() -> str:
    """Get query from command line arguments (Alfred input)."""
    return sys.argv[1] if len(sys.argv) > 1 else ""

def handle_empty_query(title: str, subtitle: str) -> None:
    """Handle empty query by showing instruction item."""
    alfred_item = item(title, subtitle, valid=False)
    output([alfred_item])
    sys.exit(0)

def handle_error(title: str, subtitle: str, exit_code: int = 1) -> None:
    """Handle error by showing error item and exiting."""
    alfred_item = error_item(title, subtitle)
    output([alfred_item])
    sys.exit(exit_code)

def filter_items_by_query(items: List[Dict[str, Any]], query: str, 
                         search_fields: List[str] = None) -> List[Dict[str, Any]]:
    """Filter Alfred items by query string."""
    if not query.strip():
        return items
    
    if search_fields is None:
        search_fields = ["title", "subtitle"]
    
    query_lower = query.lower()
    filtered_items = []
    
    for item in items:
        # Search in specified fields
        match_found = False
        for field in search_fields:
            if field in item and query_lower in item[field].lower():
                match_found = True
                break
        
        if match_found:
            filtered_items.append(item)
    
    return filtered_items

def sort_items_by_relevance(items: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """Sort items by relevance to query (title matches first, then subtitle)."""
    if not query.strip():
        return items
    
    query_lower = query.lower()
    
    def relevance_score(item):
        title = item.get('title', '').lower()
        subtitle = item.get('subtitle', '').lower()
        
        # Exact title match gets highest score
        if title == query_lower:
            return 1000
        
        # Title starts with query
        if title.startswith(query_lower):
            return 900
        
        # Title contains query
        if query_lower in title:
            return 800
        
        # Subtitle starts with query
        if subtitle.startswith(query_lower):
            return 700
        
        # Subtitle contains query
        if query_lower in subtitle:
            return 600
        
        return 0
    
    return sorted(items, key=relevance_score, reverse=True)

def no_results_item(query: str, context: str = "items") -> Dict[str, Any]:
    """Create a standard 'no results found' item."""
    return item(
        f"No {context} found",
        f"No {context} found for '{query}'",
        valid=False
    )

def truncate_for_alfred(text: str, max_length: int = 100) -> str:
    """Truncate text for Alfred display with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def format_alfred_subtitle(*parts: str, separator: str = " • ") -> str:
    """Format subtitle with separator, filtering out empty parts."""
    return separator.join(filter(None, parts))

def item_with_mods(title: str, subtitle: str, arg: str = "", 
                   mods: Dict[str, Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    """Create Alfred item with modifier key actions."""
    alfred_item = item(title, subtitle, arg, **kwargs)
    
    if mods:
        alfred_item["mods"] = mods
    
    return alfred_item

def add_alfred_modifier(item: Dict[str, Any], mod_key: str, subtitle: str, 
                       arg: str = None, valid: bool = True) -> None:
    """Add modifier key action to existing Alfred item."""
    if "mods" not in item:
        item["mods"] = {}
    
    mod_data = {
        "subtitle": subtitle,
        "valid": valid
    }
    
    if arg is not None:
        mod_data["arg"] = arg
    
    item["mods"][mod_key] = mod_data

def get_alfred_theme_background() -> str:
    """Get Alfred theme background color (light/dark)."""
    # Alfred sets this environment variable
    theme = os.environ.get('alfred_theme_background', 'rgba(255,255,255,0.98)')
    
    # Simple heuristic to detect dark theme
    if 'rgba(0,0,0' in theme or 'rgba(40,40,40' in theme or 'rgba(20,20,20' in theme:
        return 'dark'
    else:
        return 'light'

def is_alfred_dark_mode() -> bool:
    """Check if Alfred is using dark mode."""
    return get_alfred_theme_background() == 'dark'

def script_filter_output(items: List[Dict[str, Any]], 
                         variables: Dict[str, str] = None) -> None:
    """Create script filter output with optional variables."""
    output_dict = {"items": items}
    
    if variables:
        output_dict["variables"] = variables
    
    sys.stdout.write(json.dumps(output_dict, indent=4))

def get_alfred_workflow_version() -> str:
    """Get current workflow version."""
    return os.environ.get('alfred_workflow_version', '1.0.0')

def get_alfred_workflow_name() -> str:
    """Get current workflow name."""
    return os.environ.get('alfred_workflow_name', 'Unknown Workflow')

def get_alfred_workflow_bundleid() -> str:
    """Get current workflow bundle ID."""
    return os.environ.get('alfred_workflow_bundleid', 'unknown.workflow')

def is_alfred_workflow_development() -> bool:
    """Check if workflow is running in development mode."""
    return os.environ.get('alfred_debug') == '1'
