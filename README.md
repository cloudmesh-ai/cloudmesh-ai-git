# Cloudmesh AI Git Extension

The Cloudmesh AI Git extension provides a professional, curated interface for common and advanced Git operations. It simplifies complex workflows by wrapping standard `git`, the GitHub CLI (`gh`), and `git-filter-repo` into a set of intuitive commands.

## Features

- **Standard Operations**: Quick access to `status`, `log`, and `diff`.
- **History Maintenance**: Safe wrappers for destructive history rewriting.
- **GitHub Integration**: Simplified synchronization with GitHub PRs and issues.
- **Repository Management**: Streamlined merging of unrelated repositories.

## Installation

### Prerequisites

To use all features of this extension, ensure the following tools are installed on your system:

1.  **Git**: The standard version control system.
2.  **GitHub CLI (`gh`)**: Used for `sync-gh`.
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

### Basic Commands

| Command | Description | Example |
| :--- | :--- | :--- |
| `cmc git status` | Show the working tree status | `cmc git status` |
| `cmc git log` | Show recent commit logs | `cmc git log --count 10` |
| `cmc git diff` | Show current changes | `cmc git diff` |

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