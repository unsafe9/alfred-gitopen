#!/usr/bin/env python3
import os
import json
import sys
import re
import sqlite3
from urllib.parse import urlparse
from pathlib import Path

def get_alfred_clipboard_history():
    """Get clipboard history from Alfred's database."""
    try:
        # Path to Alfred's clipboard history database
        db_path = Path.home() / "Library/Application Support/Alfred/Databases/clipboard.alfdb"
        
        if not db_path.exists():
            return []
        
        # Connect to the database and query clipboard history
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Query to get the most recent 50 text entries
        query = "SELECT item FROM clipboard WHERE dataType = 0 ORDER BY ts DESC LIMIT 50"
        cursor.execute(query)
        
        clipboard_items = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return clipboard_items
    
    except Exception as e:
        print(f"Error accessing clipboard history: {e}", file=sys.stderr)
        return []

def extract_git_urls(text):
    """Extract Git repository URLs from text."""
    git_urls = []
    
    # Enhanced Git URL patterns to support various hosting services
    patterns = [
        # HTTPS URLs - Generic pattern for any domain
        r'https?://[a-zA-Z0-9.-]+/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?(?:/.*)?',
        # SSH URLs - Generic pattern for any domain
        r'git@[a-zA-Z0-9.-]+:[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?',
        # SSH URLs with custom ports
        r'ssh://git@[a-zA-Z0-9.-]+(?::[0-9]+)?/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?',
        # Git protocol URLs
        r'git://[a-zA-Z0-9.-]+/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Normalize URL
            normalized_url = normalize_git_url(match)
            if normalized_url and is_valid_git_url(normalized_url) and normalized_url not in git_urls:
                git_urls.append(normalized_url)
    
    return git_urls

def normalize_git_url(url):
    """Normalize Git URL."""
    if not url:
        return None
    
    # Remove trailing slashes and fragments
    url = url.rstrip('/').split('#')[0].split('?')[0]
    
    # Convert SSH URL to HTTPS
    if url.startswith('git@'):
        # git@domain:user/repo.git -> https://domain/user/repo
        ssh_pattern = r'git@([^:]+):(.+)'
        match = re.match(ssh_pattern, url)
        if match:
            host, path = match.groups()
            # Remove .git extension
            if path.endswith('.git'):
                path = path[:-4]
            url = f'https://{host}/{path}'
    
    # Handle SSH URLs with ssh:// prefix
    elif url.startswith('ssh://git@'):
        # ssh://git@domain:port/user/repo.git -> https://domain/user/repo
        ssh_pattern = r'ssh://git@([^:/]+)(?::[0-9]+)?/(.+)'
        match = re.match(ssh_pattern, url)
        if match:
            host, path = match.groups()
            if path.endswith('.git'):
                path = path[:-4]
            url = f'https://{host}/{path}'
    
    # Handle git:// URLs
    elif url.startswith('git://'):
        # git://domain/user/repo.git -> https://domain/user/repo
        url = url.replace('git://', 'https://')
        if url.endswith('.git'):
            url = url[:-4]
    
    # Remove .git extension from HTTPS URLs
    elif url.startswith(('http://', 'https://')) and url.endswith('.git'):
        url = url[:-4]
    
    return url

def is_valid_git_url(url):
    """Check if URL is a valid Git repository URL."""
    try:
        parsed = urlparse(url)
        if not (parsed.scheme and parsed.netloc and parsed.path):
            return False
        
        # Check if path has at least user/repo structure
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 2:
            return False
        
        # Exclude common non-repository URLs
        excluded_patterns = [
            r'/issues/',
            r'/pull/',
            r'/releases/',
            r'/wiki/',
            r'/settings/',
            r'/actions/',
            r'/projects/',
            r'/security/',
            r'/pulse/',
            r'/graphs/',
        ]
        
        for pattern in excluded_patterns:
            if re.search(pattern, parsed.path):
                return False
        
        return True
    except Exception:
        return False

def get_repo_name_from_url(url):
    """Extract repository name from Git URL."""
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2:
            return path_parts[-1]  # Last part is repository name
    except Exception:
        pass
    
    # Fallback: use last part of URL
    return url.split('/')[-1] if '/' in url else url

def get_domain_from_url(url):
    """Extract domain from Git URL for display."""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return "unknown"

def create_alfred_output(items):
    """Create JSON output for Alfred."""
    alfred_json = {"items": items}
    sys.stdout.write(json.dumps(alfred_json, indent=4))

def main():
    """Main execution function."""
    clipboard_items = get_alfred_clipboard_history()
    
    if not clipboard_items:
        error_item = {
            "title": "No clipboard history available",
            "subtitle": "Unable to access Alfred's clipboard history",
            "valid": False,
        }
        create_alfred_output([error_item])
        sys.exit(0)
    
    # Extract Git URLs from all clipboard items
    all_git_urls = []
    for item in clipboard_items:
        git_urls = extract_git_urls(item)
        all_git_urls.extend(git_urls)
    
    # Remove duplicates while preserving order
    unique_git_urls = []
    seen = set()
    for url in all_git_urls:
        if url not in seen:
            unique_git_urls.append(url)
            seen.add(url)
    
    if not unique_git_urls:
        not_found_item = {
            "title": "No Git repository URLs found",
            "subtitle": f"Searched through {len(clipboard_items)} clipboard entries",
            "valid": False,
        }
        create_alfred_output([not_found_item])
        sys.exit(0)
    
    alfred_items = []
    for url in unique_git_urls:
        repo_name = get_repo_name_from_url(url)
        domain = get_domain_from_url(url)
        
        item = {
            "uid": url,
            "title": repo_name,
            "subtitle": f"{domain} • {url}",
            "arg": url,
            "icon": {"type": "default"},
        }
        alfred_items.append(item)
    
    create_alfred_output(alfred_items)

if __name__ == "__main__":
    main()

