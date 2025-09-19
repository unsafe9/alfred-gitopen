#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
from urllib.parse import unquote

from config import (
    get_app_search_paths, 
    get_ides_to_check,
    get_ide_app_name,
    is_jetbrains_ide,
    is_vscode_ide, 
    get_vscode_config_path,
    JETBRAINS_IDES,
    VSCODE_IDES
)

def get_jetbrains_recent_projects(ide_name, app_path):
    """Get recent projects for JetBrains IDEs."""
    if not is_jetbrains_ide(ide_name):
        return []
    
    home = Path.home()
    config_pattern = f'Library/Application Support/JetBrains/{ide_name}*'
    paths = sorted(home.glob(config_pattern), reverse=True)
    
    if not paths:
        return []
    
    return get_jetbrains_projects(paths[0], ide_name, app_path)

def get_vscode_recent_projects(ide_name, app_path):
    """Get recent projects for VSCode-like IDEs."""
    config_path = get_vscode_config_path(ide_name)
    if not config_path:
        return []
    
    home = Path.home()
    state_db_path = home / config_path
    
    return get_vscode_projects(state_db_path, ide_name, app_path)

# -----------------------------------------------------------------------------

def find_application(app_name):
    """Finds the full path of an application from the search paths."""
    app_search_paths = get_app_search_paths()
    for search_path in app_search_paths:
        if (search_path / app_name).exists():
            return str(search_path / app_name)
    return None

def get_jetbrains_projects(config_path, ide_name, app_path):
    """Parses recent projects for JetBrains IDEs."""
    projects = []
    xml_file_name = "recentSolutions.xml" if ide_name == "Rider" else "recentProjects.xml"
    xml_file_path = config_path / "options" / xml_file_name

    if not xml_file_path.exists():
        return []

    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        path_macros = {'$USER_HOME$': str(Path.home())}
        
        for component in root.iter('component'):
            if component.get('name') == 'PathMacros':
                for macro in component.iter('macro'):
                    name, value = macro.get('name'), macro.get('value')
                    if name and value: path_macros[f'${name}$'] = value
                break

        recent_projects_manager = root.find(".//component[@name='RecentProjectsManager']")
        if not recent_projects_manager:
            return []

        for entry in recent_projects_manager.findall(".//option[@name='additionalInfo']/map/entry"):
            path = entry.get('key')
            if not path: continue

            real_path_str = path
            for macro, value in path_macros.items():
                real_path_str = real_path_str.replace(macro, value)
            
            if '$' in real_path_str: continue
            
            real_path = Path(real_path_str).resolve()
            
            project_info = entry.find('.//RecentProjectMetaInfo')
            if project_info is not None:
                project_name = real_path.name
                timestamp = None
                for option in project_info.iter('option'):
                    if option.get('name') == 'activationTimestamp':
                        timestamp = option.get('value')
                        break

                if project_name and timestamp:
                    projects.append({
                        'name': project_name,
                        'path': str(real_path),
                        'timestamp': int(timestamp),
                        'ide_name': ide_name,
                        'app_path': app_path
                    })
    except (ET.ParseError, FileNotFoundError):
        return []
    
    return projects


def get_vscode_projects(state_db_path, ide_name, app_path):
    """Parses recent projects for VSCode-like IDEs from state.vscdb."""
    projects = []
    if not state_db_path.exists():
        return []
        
    try:
        # Connect to the SQLite database (read-only)
        con = sqlite3.connect(f'file:{state_db_path}?mode=ro', uri=True)
        cur = con.cursor()
        
        # Query for the specific key
        res = cur.execute("SELECT value FROM ItemTable WHERE key = 'history.recentlyOpenedPathsList'")
        data = res.fetchone()
        
        con.close()
        
        if data:
            # The value is a JSON string - check if it's bytes or string
            json_data = data[0]
            if isinstance(json_data, bytes):
                json_data = json_data.decode('utf-8')
            
            recent_data = json.loads(json_data)
            
            # Get workspace storage path for timestamp lookup
            user_data_path = state_db_path.parent.parent
            workspace_storage_path = user_data_path / "workspaceStorage"
            
            # Create a mapping of folder URIs to workspace storage timestamps
            workspace_timestamps = {}
            if workspace_storage_path.exists():
                for workspace_dir in workspace_storage_path.iterdir():
                    if workspace_dir.is_dir():
                        workspace_json = workspace_dir / "workspace.json"
                        if workspace_json.exists():
                            try:
                                with open(workspace_json, 'r') as f:
                                    workspace_data = json.load(f)
                                    folder_uri = workspace_data.get('folder')
                                    if folder_uri:
                                        # Get the last modified time of the workspace directory
                                        timestamp = int(workspace_dir.stat().st_mtime * 1000)  # Convert to milliseconds
                                        workspace_timestamps[folder_uri] = timestamp
                            except (json.JSONDecodeError, OSError):
                                continue
            
            # Process entries and match with workspace timestamps
            for index, entry in enumerate(recent_data.get('entries', [])):
                uri = entry.get('folderUri') or entry.get('fileUri')
                if uri and uri.startswith('file:///'):
                    path_str = unquote(uri[7:])  # Remove 'file://' prefix
                    path = Path(path_str)
                    
                    # Check if path still exists
                    if path.exists():
                        # Get timestamp from workspace storage if available
                        timestamp = workspace_timestamps.get(uri, 0)
                        
                        projects.append({
                            'name': path.name,
                            'path': path_str,
                            'timestamp': timestamp,  # Use actual workspace timestamp
                            'ide_name': ide_name,
                            'app_path': app_path
                        })
    except (sqlite3.Error, json.JSONDecodeError) as e:
        # Debug: print error for troubleshooting
        print(f"Error reading VSCode projects: {e}", file=sys.stderr)
        return []
    
    return projects


def main():
    all_projects = []
    
    # Get IDE list from config
    ides_to_check = get_ides_to_check()
    
    for ide_id, ide_name in ides_to_check:
        # Get app name for this IDE
        app_name = get_ide_app_name(ide_name)
        if not app_name:
            continue
        
        # Find the application path
        app_path = find_application(app_name)
        if not app_path:
            continue
        
        # Get recent projects based on IDE type
        if is_jetbrains_ide(ide_name):
            projects = get_jetbrains_recent_projects(ide_name, app_path)
            all_projects.extend(projects)
        elif is_vscode_ide(ide_name):
            projects = get_vscode_recent_projects(ide_name, app_path)
            all_projects.extend(projects)
    
    # Sort projects by timestamp (most recent first)
    sorted_projects = sorted(all_projects, key=lambda x: x.get('timestamp', 0), reverse=True)
    
    alfred_items = []
    if not sorted_projects:
        alfred_items.append({
            "title": "No recent projects found",
            "subtitle": "Check your app paths and config patterns in the script.",
            "valid": False
        })

    for proj in sorted_projects:
        # Format timestamp if available
        timestamp = proj.get('timestamp')
        if timestamp:
            last_opened_str = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
            subtitle = f"Last Used: {last_opened_str} - {proj['path']}"
        else:
            subtitle = proj['path']

        alfred_items.append({
            "title": f"{proj['name']} ({proj['ide_name']})",
            "subtitle": subtitle,
            "arg": f"{proj['app_path']}|{proj['path']}",
            "icon": {"type": "fileicon", "path": proj['app_path']}
        })
        
    print(json.dumps({"items": alfred_items}))


if __name__ == "__main__":
    main()
