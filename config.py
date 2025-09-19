#!/usr/bin/env python3
"""
Configuration file for Alfred Open Git Repo workflow.
All settings and constants are centralized here.
"""

import os
from pathlib import Path

# -----------------------------------------------------------------------------
# Application Search Paths
# -----------------------------------------------------------------------------

DEFAULT_APP_SEARCH_PATHS = [
    "/Applications",
    "~/Applications"
]

def get_app_search_paths():
    """Get application search paths from environment variable or defaults."""
    paths_str = os.environ.get("APP_SEARCH_PATHS", "")
    
    if paths_str:
        paths = []
        for path_str in paths_str.split(','):
            path_str = path_str.strip()
            if path_str:
                # Expand ~ to home directory
                expanded_path = os.path.expanduser(path_str)
                paths.append(Path(expanded_path))
        return paths
    else:
        # Use defaults
        return [Path(os.path.expanduser(path)) for path in DEFAULT_APP_SEARCH_PATHS]

# -----------------------------------------------------------------------------
# IDEs Configuration
# -----------------------------------------------------------------------------

# Default IDEs to check
DEFAULT_IDES_TO_CHECK = [
    "Visual Studio Code",
    "Cursor", 
    "GoLand",
    "Rider",
    "WebStorm",
    "IntelliJ IDEA"
]

def get_ides_to_check():
    """Get the list of IDEs to check from environment variable or defaults."""
    ides_str = os.environ.get("IDES_TO_CHECK", "")
    
    if ides_str:
        # Convert string to list of tuples (id, display_name)
        ides = []
        for ide_name in ides_str.split(','):
            ide_name = ide_name.strip()
            if ide_name:
                # Convert display name to id (lowercase, no spaces)
                ide_id = ide_name.lower().replace(' ', '').replace('.', '')
                ides.append((ide_id, ide_name))
        return ides
    else:
        # Use defaults
        ides = []
        for ide_name in DEFAULT_IDES_TO_CHECK:
            ide_id = ide_name.lower().replace(' ', '').replace('.', '')
            ides.append((ide_id, ide_name))
        return ides

# -----------------------------------------------------------------------------
# JetBrains IDEs Configuration
# -----------------------------------------------------------------------------

JETBRAINS_IDES = {
    'goland': 'GoLand.app',
    'rider': 'Rider.app', 
    'webstorm': 'WebStorm.app',
    'intellij idea': 'IntelliJ IDEA.app',
    'pycharm': 'PyCharm.app',
    'phpstorm': 'PhpStorm.app',
    'rubymine': 'RubyMine.app',
    'clion': 'CLion.app',
    'datagrip': 'DataGrip.app',
    'appcode': 'AppCode.app'
}

# -----------------------------------------------------------------------------
# VSCode-like IDEs Configuration  
# -----------------------------------------------------------------------------

VSCODE_IDES = {
    'visual studio code': {
        'app_name': 'Visual Studio Code.app',
        'config_path': 'Library/Application Support/Code/User/globalStorage/state.vscdb'
    },
    'vscode': {
        'app_name': 'Visual Studio Code.app', 
        'config_path': 'Library/Application Support/Code/User/globalStorage/state.vscdb'
    },
    'cursor': {
        'app_name': 'Cursor.app',
        'config_path': 'Library/Application Support/Cursor/User/globalStorage/state.vscdb'
    },
    'code - insiders': {
        'app_name': 'Visual Studio Code - Insiders.app',
        'config_path': 'Library/Application Support/Code - Insiders/User/globalStorage/state.vscdb'
    }
}

# -----------------------------------------------------------------------------
# Git Repository Settings
# -----------------------------------------------------------------------------

DEFAULT_WORKSPACE_DIR = "~/workspace"
DEFAULT_MAX_DEPTH = 3

def get_workspace_dir():
    """Get workspace directory from environment variable or default."""
    workspace_dir = os.environ.get("WORKSPACE_DIR", "")
    if workspace_dir:
        return os.path.expanduser(workspace_dir)
    else:
        return os.path.expanduser(DEFAULT_WORKSPACE_DIR)

def get_max_depth():
    """Get max search depth from environment variable or default."""
    try:
        return int(os.environ.get("MAX_DEPTH", str(DEFAULT_MAX_DEPTH)))
    except (ValueError, TypeError):
        return DEFAULT_MAX_DEPTH

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def get_ide_app_name(ide_name):
    """Get the app name for a given IDE."""
    ide_name_lower = ide_name.lower()
    
    # Check JetBrains IDEs
    for jetbrains_name, app_name in JETBRAINS_IDES.items():
        if jetbrains_name in ide_name_lower:
            return app_name
    
    # Check VSCode-like IDEs
    for vscode_name, config in VSCODE_IDES.items():
        if vscode_name in ide_name_lower:
            return config['app_name']
    
    return None

def is_jetbrains_ide(ide_name):
    """Check if the IDE is a JetBrains IDE."""
    ide_name_lower = ide_name.lower()
    return any(jetbrains_name in ide_name_lower for jetbrains_name in JETBRAINS_IDES.keys())

def is_vscode_ide(ide_name):
    """Check if the IDE is a VSCode-like IDE.""" 
    ide_name_lower = ide_name.lower()
    return any(vscode_name in ide_name_lower for vscode_name in VSCODE_IDES.keys())

def get_vscode_config_path(ide_name):
    """Get VSCode IDE configuration path."""
    ide_name_lower = ide_name.lower()
    
    for vscode_name, config in VSCODE_IDES.items():
        if vscode_name in ide_name_lower:
            return config['config_path']
    
    return None
