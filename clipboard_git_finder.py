#!/usr/bin/env python3
import sys
from alfred import output, error_item, item, get_alfred_clipboard_history, handle_empty_query
from git import get_repository_name_from_url, extract_git_urls, get_domain_from_git_url

def main():
    """Main execution function."""
    clipboard_items = get_alfred_clipboard_history(50)
    
    if not clipboard_items:
        alfred_error_item = error_item("No clipboard history available", "Unable to access Alfred's clipboard history")
        output([alfred_error_item])
        sys.exit(0)
    
    # Extract Git URLs from all clipboard items
    all_git_urls = []
    for clipboard_item in clipboard_items:
        git_urls = extract_git_urls(clipboard_item)
        all_git_urls.extend(git_urls)
    
    # Remove duplicates while preserving order
    unique_git_urls = []
    seen = set()
    for url in all_git_urls:
        if url not in seen:
            unique_git_urls.append(url)
            seen.add(url)
    
    if not unique_git_urls:
        not_found_item_result = error_item("No Git repository URLs found", f"Searched through {len(clipboard_items)} clipboard entries")
        output([not_found_item_result])
        sys.exit(0)
    
    alfred_items = []
    for url in unique_git_urls:
        repo_name = get_repository_name_from_url(url)
        domain = get_domain_from_git_url(url)
        
        alfred_item = item(repo_name, f"{domain} • {url}", url, uid=url)
        alfred_items.append(alfred_item)
    
    output(alfred_items)

if __name__ == "__main__":
    main()