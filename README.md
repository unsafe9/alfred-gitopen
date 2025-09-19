# Git Open Alfred Workflow

> **Development Notice**: This Alfred workflow may contain bugs or unstable behavior as it was developed with AI assistance and is currently in **alpha version**. Please report any issues or suggestions.

This workflow is designed to boost your project start or help you quickly continue your work by letting you easily search and open any Git repositories with your preferred IDE.

## Prerequisites

Some commands use GitHub CLI (`gh`) to be installed and authenticated.

Install GitHub CLI: `brew install gh`  
Authenticate: `gh auth login`

## Usage

All commands will prompt you to select your preferred IDE to open the repository after completion.

### Local Git Commands
- **`gitopen {search_term}`**: Search for Git repositories within your workspace directory.
- **`gitrecent {search_term}`**: Display recent projects from your supported IDEs for quick access.
- **`gitclone`**: Find Git repository URLs from Alfred's clipboard history and clone them.
- **`gitinit {repository_name}`**: Create a new directory, initialize it as a Git repository.

### GitHub Commands
- **`ghclone {search_term}`**: Search and clone GitHub repositories by username/repository name or keywords, including private repositories.
- **`ghinit {repository_name}`**: Create a new GitHub repository and initialize it locally.
- **`ghfork {repository_url}`**: Fork and clone GitHub repositories.

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
