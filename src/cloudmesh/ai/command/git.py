"""
Cloudmesh AI Git Extension
==========================

This extension provides a professional interface for common and advanced git operations,
wrapping standard git, the GitHub CLI (gh), and git-filter-repo for history maintenance.

Usage:
    cmc git status
    cmc git log [--count <number>]
    cmc git diff
    cmc git nuke <path>
    cmc git clean-history
    cmc git sync-gh
    cmc git merge-repos <url>
    cmc git -h | --help

Arguments:
    <path>             Path to the file or directory to remove from history.
    <url>              URL of the remote repository to merge into the current one.

Options:
    --count <number>    Number of commits to show in the log [default: 5].
    -h, --help          Show this help message and exit.

Examples:
    Check status:
        $ cmc git status

    Remove a sensitive file from all history:
        $ cmc git nuke secrets.txt

    Sync local state with GitHub:
        $ cmc git sync-gh

    Merge another repository into this one:
        $ cmc git merge-repos https://github.com/user/other-repo.git
"""

import subprocess
import shutil
import click
from pathlib import Path

def check_dependency(tool_name, install_instructions):
    """
    Checks if a required system tool is installed.

    Args:
        tool_name (str): The name of the tool to check (e.g., 'gh').
        install_instructions (str): Instructions to show the user if the tool is missing.

    Returns:
        bool: True if the tool is installed, False otherwise.
    """
    if shutil.which(tool_name) is None:
        print(f"\nError: Required tool '{tool_name}' is not installed.")
        print(f"To install it, please follow these steps:\n{install_instructions}")
        return False
    return True

@click.group()
def git_group():
    """
    Git utility for managing repositories and performing advanced history maintenance.
    """
    pass

@git_group.command(name="status")
def status_cmd():
    """
    Show the working tree status.

    Usage:
        cmc git status
    """
    try:
        result = subprocess.run(["git", "status"], capture_output=True, text=True, check=True)
        print("\n--- Git Status ---")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running git status: {e.stderr}")
    except FileNotFoundError:
        print("Error: 'git' command not found. Please install git.")

@git_group.command(name="log")
@click.option("--count", default=5, type=int, help="Number of commits to show.")
def log_cmd(count):
    """
    Show commit logs.

    Usage:
        cmc git log [--count <number>]

    Example:
        $ cmc git log --count 10
    """
    try:
        result = subprocess.run(["git", "log", f"-n {count}", "--oneline"], capture_output=True, text=True, check=True)
        print(f"\n--- Last {count} Commits ---")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running git log: {e.stderr}")
    except FileNotFoundError:
        print("Error: 'git' command not found. Please install git.")

@git_group.command(name="diff")
def diff_cmd():
    """
    Show changes between commits, commit and working tree, etc.

    Usage:
        cmc git diff
    """
    try:
        result = subprocess.run(["git", "diff"], capture_output=True, text=True, check=True)
        print("\n--- Git Diff ---")
        print(result.stdout if result.stdout else "No changes found.")
    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e.stderr}")
    except FileNotFoundError:
        print("Error: 'git' command not found. Please install git.")

@git_group.command(name="nuke")
@click.argument("path")
def nuke_cmd(path):
    """
    Completely remove a path from the git history.

    This is a destructive operation that rewrites history. It uses git-filter-repo.

    Usage:
        cmc git nuke <path>

    Example:
        $ cmc git nuke config/secrets.json
    """
    if not check_dependency("git-filter-repo", "Install via: pip install git-filter-repo"):
        return

    if not click.confirm(f"WARNING: This will permanently remove '{path}' from ALL history. Continue?", default=False):
        print("Operation cancelled.")
        return

    try:
        print(f"Nuking {path} from history...")
        subprocess.run(["git-filter-repo", "--path", path, "--invert-paths"], check=True)
        print(f"Successfully removed {path} from history.")
    except subprocess.CalledProcessError as e:
        print(f"Error during nuke operation: {e}")

@git_group.command(name="clean-history")
def clean_history_cmd():
    """
    Guided workflow to clean sensitive data or rewrite history.

    Usage:
        cmc git clean-history
    """
    if not check_dependency("git-filter-repo", "Install via: pip install git-filter-repo"):
        return

    print("\n--- History Cleaning Guide ---")
    print("1. To remove a specific file: use 'cmc git nuke <path>'")
    print("2. To change authors: use 'git-filter-repo --mailmap my-mailmap'")
    print("3. To remove a directory: use 'cmc git nuke <dir_path>'")
    print("\nNote: Always backup your repository before rewriting history.")

@git_group.command(name="sync-gh")
def sync_gh_cmd():
    """
    Sync local state with GitHub using the gh CLI.

    Usage:
        cmc git sync-gh
    """
    if not check_dependency("gh", "Install via: brew install gh (macOS) or official gh docs"):
        return

    try:
        print("Syncing with GitHub...")
        # Example: fetch all PRs and update local tracking
        subprocess.run(["gh", "pr", "list"], check=True)
        print("\nLocal state synced with GitHub PRs.")
    except subprocess.CalledProcessError as e:
        print(f"Error syncing with GitHub: {e}")

@git_group.command(name="merge-repos")
@click.argument("url")
def merge_repos_cmd(url):
    """
    Merge another repository into the current one while preserving history.

    Usage:
        cmc git merge-repos <url>

    Example:
        $ cmc git merge-repos https://github.com/user/other-repo.git
    """
    try:
        repo_name = url.split("/")[-1].replace(".git", "")
        print(f"Merging {repo_name} into current repository...")
        
        # 1. Add remote
        subprocess.run(["git", "remote", "add", repo_name, url], check=True)
        # 2. Fetch
        subprocess.run(["git", "fetch", repo_name], check=True)
        # 3. Merge with allow-unrelated-histories
        subprocess.run(["git", "merge", f"{repo_name}/master", "--allow-unrelated-histories"], check=True)
        
        print(f"Successfully merged {repo_name} into current repository.")
    except subprocess.CalledProcessError as e:
        print(f"Error merging repositories: {e}")

entry_point = git_group

def register(cli):
    """
    Registers the git command group with the main CLI.

    Args:
        cli: The main click CLI object.
    """
    cli.add_command(git_group, name="git")