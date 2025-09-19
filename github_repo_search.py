#!/usr/bin/env python3
from github import github_search_base, clone_repo_filter, clone_item_formatter

def main():
    """Main execution function."""
    github_search_base(
        empty_query_title="Search GitHub repositories",
        empty_query_subtitle="Type repository name, owner/repo, or keywords to search",
        no_results_message="No GitHub repositories found for '{query}'",
        repo_filter_func=clone_repo_filter,
        item_formatter_func=clone_item_formatter,
        search_limit=15,
        include_user_repos=True
    )

if __name__ == "__main__":
    main()