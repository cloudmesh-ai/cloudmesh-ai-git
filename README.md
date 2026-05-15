# Cloudmesh AI Git Extension

**Quick Links:**
- [API Reference](API.md) - Full technical documentation of all modules.
## Features

- **Standard Operations**: Quick access to `status`, `log`, and `diff`.
- **Workflow Automation**: Recursive `pull` for all repositories in a directory tree.
- **Identity Management**: Manage multiple GitHub usernames and their associated repositories.
- **History Maintenance**: Safe wrappers for destructive history rewriting.
- **GitHub Integration**: Simplified synchronization and statistics retrieval via `gh`.
- **Repository Management**: Streamlined merging and bulk backup of repositories.
- **Visual Git View**: An interactive HTML dashboard for monitoring repository statistics, managing backups, and quick-accessing GitHub repositories.

## Git View Dashboard

The extension includes a visual **Git View** dashboard that provides a curated table of all configured repositories. 

**Key Dashboard Features:**
- **Visual Status**: Quick indicators for local backup status.
- **Action Icons**: 
    - <i class="fa-solid fa-rotate"></i> **Refresh**: Update repository data from GitHub.
    - <i class="fa-solid fa-download"></i> **Download**: Trigger repository backup.
    - <i class="fa-solid fa-upload"></i> **Upload**: Sync local changes.
    - <i class="fa-solid fa-circle-info"></i> **Info**: View detailed repository metadata.
    - <i class="fa-solid fa-globe"></i> **WWW**: Open the repository directly on GitHub.
- **Filtering**: Real-time search and exclusion filtering for large repository sets.

## Installation

### Prerequisites

To use all features of this extension, ensure the following tools are installed on your system:

1.  **Git**: The standard version control system.
2.  **GitHub CLI (`gh`)**: Used for `sync-gh`, `stats-user`, `backup`, and `users`.
    - macOS: `brew install gh`
    - Linux/Windows: See [official docs](https://cli.github.com/).
3.  **git-filter-repo**: Used for `nuke` and `clean-history`.
    - Install via pip: `pip install git-filter-repo`

### Install the Extension

```bash
cd cloudmesh-ai-git
pip install -e .
```

## Command Reference

### Basic & Workflow Commands

| Command | Description | Example |
| :--- | :--- | :--- |
| `cmc git status` | Show the working tree status | `cmc git status` |
| `cmc git log` | Show recent commit logs | `cmc git log --count 10` |
| `cmc git diff` | Show current changes | `cmc git diff` |
| `cmc git pull` | Recursively pull all repos in current tree | `cmc git pull` |
| `cmc git multi` | Run command in all sub-repos | `cmc git multi "pull origin main"` |
| `cmc git stats` | Show contribution statistics (local) | `cmc git stats` |
| `cmc git version-check` | Compare local vs PyPI/GH | `cmc git version-check cloudmesh-ai-common` |

### User & Repository Management

#### `cmc git user [add|remove] <username>`
Manage your list of GitHub identities stored in `~/.config/cloudmesh/git/users.yaml`.
- **List users**: `cmc git user`
- **Add user**: `cmc git user add mygithubuser`
- **Remove user**: `cmc git user remove mygithubuser`

#### `cmc git stats-user <username|all>`
Get basic statistics (repo count, stars, forks) for a specific user or all configured users.
- **Example**: `cmc git stats-user all`

#### `cmc git backup <username|all>`
Clone all public repositories for the specified user (or all configured users) into `~/git_backups`.
- **Example**: `cmc git backup mygithubuser`

#### `cmc git summary`
Generate a summary table of all configured GitHub users, their total repository count, and their most starred repository.
- **Example**: `cmc git summary`

### Power-User Commands

#### `cmc git nuke <path>`
Completely removes a file or directory from the entire Git history. This is a destructive operation.
- **Under the hood**: Uses `git-filter-repo --path <path> --invert-paths`.
- **Example**: `cmc git nuke config/secrets.json`

#### `cmc git clean-history`
Provides a guided workflow for cleaning sensitive data or rewriting history.
- **Example**: `cmc git clean-history`

#### `cmc git sync-gh`
Synchronizes local state with GitHub using the `gh` CLI.
- **Example**: `cmc git sync-gh`

#### `cmc git merge-repos <url>`
Merges another repository into the current one while preserving all history.
- **Example**: `cmc git merge-repos https://github.com/user/other-repo.git`

## Transition from `gitutil`

This extension replaces the legacy `gitutil` bash scripts with modern, safer alternatives.

| Legacy Script | New Command | Modern Tool Used |
| :--- | :--- | :--- |
| `gitNukePath` | `cmc git nuke` | `git-filter-repo` |
| `gitRemoveFileFromHistory` | `cmc git nuke` | `git-filter-repo` |
| `gitMergeRepos` | `cmc git merge-repos` | `git merge --allow-unrelated-histories` |
| `change-authors` | `cmc git clean-history` | `git-filter-repo --mailmap` |

## Safety Warning

**History Rewriting is Destructive.**
Commands like `nuke` and `merge-repos` rewrite the Git commit history. This changes commit hashes and can cause significant issues for other collaborators. 

**Always follow these steps before using power-user commands:**
1.  **Backup**: Create a fresh clone of your repository.
2.  **Coordinate**: Notify all team members that history is being rewritten.
3.  **Force Push**: Be prepared to `git push --force` to your remote.

## Full Command Documentation

```text
Cloudmesh AI Git Extension

This extension provides an interface for common and advanced git operations,
wrapping standard git, the GitHub CLI (gh), and git-filter-repo for history maintenance.

Usage:
    cmc git status
    cmc git log [--count <number>]
    cmc git diff
    cmc git nuke <path>
    cmc git clean-history
    cmc git sync-gh
    cmc git merge-repos <url>
    cmc git multi <command>
    cmc git stats
    cmc git version-check <package_name>
    cmc git pull
    cmc git backup <user|all>
    cmc git stats-user <username|all>
    cmc git user [add <username> | remove <username>]
    cmc git summary
    cmc git -h | --help

Commands:
    status              Show the working tree status.
    log                 Show commit logs.
    diff                Show changes between commits, commit and working tree, etc.
    nuke                Completely remove a path from the git history (destructive).
    clean-history       Guided workflow to clean sensitive data or rewrite history.
    sync-gh             Sync local state with GitHub using the gh CLI.
    merge-repos         Merge another repository into the current one while preserving history.
    multi               Execute a git command in all subdirectories that are git repositories.
    stats               Show contribution statistics (lines of code per author) for the current repository.
    version-check       Compare local version with PyPI and GitHub.
    pull                Recursively pull all git repositories in the current tree.
    backup              Clone repositories for a specific user or all configured users.
    stats-user          Get basic statistics for a GitHub user or all configured users.
    user                Manage configured GitHub usernames.
    summary             Generate a summary table of all configured GitHub users and their top repositories.

Arguments:
    <path>             Path to the file or directory to remove from history.
    <url>              URL of the remote repository to merge into the current one.
    <command>          Git command to run across multiple repositories.
    <package_name>     Name of the PyPI package to check version against.
    <username>         GitHub username for stats or backup.
    <user|all>         Specific username or 'all' to use configured users.

Options:
    --count <number>    Number of commits to show in the log [default: 5].
    -h, --help          Show this help message and exit.

Examples:
    Check status:
        $ cmc git status

    Recursive pull in all sub-repos:
        $ cmc git pull

    Manage GitHub users:
        $ cmc git user add mygithubuser
        $ cmc git user

    Get stats for all configured users:
        $ cmc git stats-user all

    Backup all repos for a user:
        $ cmc git backup mygithubuser

    Get a summary table of all configured users:
        $ cmc git summary
## Core Dependencies
This project depends on the following core components of the Cloudmesh AI ecosystem:
- [cloudmesh-ai-common](https://github.com/cloudmesh-ai/cloudmesh-ai-common)
- [cloudmesh-ai-cmc](https://github.com/cloudmesh-ai/cloudmesh-ai-cmc)
