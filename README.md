# Git Open Alfred Workflow

A simple Alfred workflow to quickly find and open local Git repositories and recent projects with your favorite IDE.

## Prerequisites

Some commands use GitHub CLI (`gh`) to be installed and authenticated.

Install GitHub CLI: `brew install gh`  
Authenticate: `gh auth login`

## Usage

- **`gitopen {search_term}`**: Searches for Git repositories within your workspace directory. Select a repository to open it in your chosen IDE.
- **`gitrecent {search_term}`**: Displays a list of recent projects from your supported IDEs for quick access.
- **`gitclone`**: Finds Git repository URLs from Alfred's clipboard history, allows you to select one to clone and open in your chosen IDE.
- **`gitinit {repository_name}`**: Creates a new directory with the specified name, initializes it as a Git repository, and opens it in your chosen IDE.
- **`githubclone {search_term}`**: Search and clone GitHub repositories by username/repository name or keywords, including private repositories for authenticated users.
- **`githubinit {repository_name}`**: Create a new GitHub repository, initialize it locally, and open it in your chosen IDE.
- **`githubfork {repository_url}`**: Fork and clone GitHub repositories.

## Installation

Download the latest version from the Releases page.
Open the downloaded `.alfredworkflow` file to install it in Alfred.

## Configuration

You can customize the workflow by setting variables in Alfred's workflow configuration panel (`[x]`).

- `WORKSPACE_DIR`: The base directory path to search for Git repositories. (Default: `~/workspace`)
- `MAX_DEPTH`: The maximum depth of subdirectories to search. (Default: `3`)

### Supported IDEs

This workflow supports VSCode-like IDEs (e.g., Visual Studio Code, Cursor) and JetBrains IDEs. For a detailed list or to add new IDEs, please refer to the `config.py` file.

## License

MIT License
