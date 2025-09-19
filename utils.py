#!/usr/bin/env python3
"""
Common utilities for Alfred Git Open workflow.
"""
import os
import json
import sys
import subprocess
from typing import List, Dict, Any, Optional

def show_notification(title: str, message: str) -> None:
    """Show macOS notification."""
    try:
        cmd = [
            'osascript', '-e',
            f'display notification "{message}" with title "{title}"'
        ]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        pass  # Ignore notification failures

def open_with_ide(ide_path: str, project_path: str) -> bool:
    """Open project with selected IDE."""
    try:
        subprocess.run(['open', '-a', ide_path, project_path], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def open_in_finder(path: str) -> bool:
    """Open path in Finder."""
    try:
        subprocess.run(['open', path], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def open_in_terminal(path: str) -> bool:
    """Open path in Terminal."""
    try:
        subprocess.run(['open', '-a', 'Terminal', path], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def ensure_directory_exists(directory: str) -> bool:
    """Ensure directory exists, create if it doesn't."""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except OSError:
        return False


def run_command(cmd: List[str], capture_output: bool = True, text: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    return subprocess.run(cmd, capture_output=capture_output, text=text)

def run_command_with_success(cmd: List[str]) -> tuple[bool, str]:
    """Run a command and return success status and output/error message."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)

def parse_alfred_argument(arg: str, separator: str = '|') -> List[str]:
    """Parse Alfred argument string by separator."""
    return arg.split(separator) if arg else []

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to max length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def validate_path(path: str) -> bool:
    """Validate if path exists and is accessible."""
    return os.path.exists(path) and os.access(path, os.R_OK)


def get_directory_name(path: str) -> str:
    """Get directory name from path."""
    return os.path.basename(os.path.normpath(path))

def join_with_separator(items: List[str], separator: str = " • ") -> str:
    """Join list items with separator, filtering out empty items."""
    return separator.join(filter(None, items))

def safe_json_loads(json_str: str) -> Optional[Any]:
    """Safely load JSON string, return None on error."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None

def get_environment_variable(key: str, default: str = "") -> str:
    """Get environment variable with default value."""
    return os.environ.get(key, default)

