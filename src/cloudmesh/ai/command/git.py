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
    cmc git multi <command>
    cmc git info [user|org|repo]
    cmc git version-check <package_name>
    cmc git pull
    cmc git backup get <user|all>
    cmc git backup set <dir>
    cmc git backup info
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
    info                GitHub and local contribution statistics.
    version-check       Compare local version with PyPI and GitHub.
    pull                Recursively pull all git repositories in the current tree.
    backup              Manage repository backups.
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

    Get stats for a user:
        $ cmc git info user mygithubuser

    List all organizations or get stats for one:
        $ cmc git info org
        $ cmc git info org cloudmesh

    Get stats for a repo:
        $ cmc git info repo myrepo --user mygithubuser

    Open the browser view of all stats:
        $ cmc git info view

    Backup all repos for a user:
        $ cmc git backup get mygithubuser

    Set backup directory:
        $ cmc git backup set ~/my_git_backups

    Check backup status:
        $ cmc git backup info

    Get a summary table of all configured users:
        $ cmc git summary
"""

import subprocess
import shutil
import click
import requests
import yaml
import json
import os
import time
import webbrowser
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from cloudmesh.ai.common.io import console
from cloudmesh.ai.common.github import gh, GitHubError

# Create a rich console for table formatting
rich_console = Console()


class UserConfig:
    """
    Handles storage and retrieval of GitHub usernames and settings in ~/.config/cloudmesh/git/config.yaml.
    """

    def __init__(self):
        self.config_dir = Path.home() / ".config" / "cloudmesh" / "git"
        self.config_file = self.config_dir / "config.yaml"
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """Ensures the config directory and file exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            self.save_config(
                {
                    "users": [],
                    "exclude": [],
                    "backup_dir": str(Path.home() / "git_backups"),
                    "repo_cache": {},
                }
            )

    def load_config(self):
        """Loads the configuration dictionary."""
        try:
            with open(self.config_file, "r") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    return {
                        "users": [],
                        "exclude": [],
                        "backup_dir": str(Path.home() / "git_backups"),
                        "repo_cache": {},
                    }
                # Ensure repo_cache and exclude exist in loaded config
                if "repo_cache" not in data:
                    data["repo_cache"] = {}
                if "exclude" not in data:
                    data["exclude"] = []
                return data
        except (yaml.YAMLError, IOError):
            return {
                "users": [],
                "exclude": [],
                "backup_dir": str(Path.home() / "git_backups"),
                "repo_cache": {},
            }

    def save_config(self, config):
        """Saves the configuration dictionary."""
        with open(self.config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

    def get_users(self):
        """Returns the list of configured usernames."""
        return self.load_config().get("users", [])

    def get_excludes(self):
        """Returns the list of excluded patterns."""
        return self.load_config().get("exclude", [])

    def save_users(self, users):
        """Saves the list of usernames to the config."""
        config = self.load_config()
        config["users"] = list(set(users))
        self.save_config(config)

    def add_user(self, username):
        """Adds a username to the config."""
        users = self.get_users()
        if username not in users:
            users.append(username)
            self.save_users(users)
            return True
        return False

    def remove_user(self, username):
        """Removes a username from the config."""
        users = self.get_users()
        if username in users:
            users.remove(username)
            self.save_users(users)
            return True
        return False

    def save_cached_repos(self, username, repos):
        """Saves the repositories for a user to the cache."""
        config = self.load_config()
        if "repo_cache" not in config:
            config["repo_cache"] = {}

        # Store with a timestamp to allow for expiration if needed in future
        config["repo_cache"][username] = {
            "timestamp": datetime.now().isoformat(),
            "repos": repos,
        }
        self.save_config(config)

    def get_cached_repos(self, username):
        """Returns the cached repositories for a user."""
        cache_data = self.load_config().get("repo_cache", {}).get(username)
        if isinstance(cache_data, dict) and "repos" in cache_data:
            return cache_data["repos"]
        return cache_data  # Fallback for old cache format

    def get_backup_dir(self):
        """Returns the configured backup directory."""
        return Path(self.load_config().get("backup_dir", Path.home() / "git_backups"))

    def set_backup_dir(self, path):
        """Sets the backup directory in the config."""
        config = self.load_config()
        config["backup_dir"] = str(Path(path).absolute())
        self.save_config(config)

    def clone_repo(self, repo_full_name):
        """
        Clones a repository into the configured backup directory.
        Returns (success, message).
        """
        try:
            backup_dir = self.get_backup_dir()
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            repo_name = repo_full_name.split('/')[-1].replace('.git', '')
            target_path = backup_dir / repo_name
            
            if target_path.exists():
                # If it exists, try to pull instead of clone
                result = subprocess.run(
                    ["git", "-C", str(target_path), "pull"],
                    capture_output=True, text=True, check=True
                )
                return True, f"Updated {repo_name} at {target_path}"
            
            # Clone the repo
            url = f"https://github.com/{repo_full_name}.git"
            subprocess.run(
                ["git", "clone", url, str(target_path)],
                capture_output=True, text=True, check=True
            )
            return True, f"Cloned {repo_name} to {target_path}"
            
        except subprocess.CalledProcessError as e:
            return False, f"Git error: {e.stderr or e.stdout}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"


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
        console.error(f"Required tool '{tool_name}' is not installed.")
        console.print(
            f"To install it, please follow these steps:\n{install_instructions}"
        )
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
        result = subprocess.run(
            ["git", "status"], capture_output=True, text=True, check=True
        )
        console.banner("Git Status")
        console.print(result.stdout)
    except subprocess.CalledProcessError as e:
        console.error(f"Error running git status: {e.stderr}")
    except FileNotFoundError:
        console.error("Error: 'git' command not found. Please install git.")


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
        result = subprocess.run(
            ["git", "log", f"-n {count}", "--oneline"],
            capture_output=True,
            text=True,
            check=True,
        )
        console.banner(f"Last {count} Commits")
        console.print(result.stdout)
    except subprocess.CalledProcessError as e:
        console.error(f"Error running git log: {e.stderr}")
    except FileNotFoundError:
        console.error("Error: 'git' command not found. Please install git.")


@git_group.command(name="diff")
def diff_cmd():
    """
    Show changes between commits, commit and working tree, etc.

    Usage:
        cmc git diff
    """
    try:
        result = subprocess.run(
            ["git", "diff"], capture_output=True, text=True, check=True
        )
        console.banner("Git Diff")
        console.print(result.stdout if result.stdout else "No changes found.")
    except subprocess.CalledProcessError as e:
        console.error(f"Error running git diff: {e.stderr}")
    except FileNotFoundError:
        console.error("Error: 'git' command not found. Please install git.")


@git_group.command(name="pull")
def pull_cmd():
    """
    Recursively pull all git repositories in the current tree.

    Usage:
        cmc git pull
    """
    # 1. Pull current directory if it's a repo
    if (Path(".") / ".git").exists():
        console.banner("Pulling current directory")
        try:
            subprocess.run(["git", "pull"], check=True)
        except subprocess.CalledProcessError as e:
            console.error(f"Failed to pull current directory: {e}")

    # 2. Find and pull all sub-repos
    git_dirs = []
    for item in Path(".").rglob(".git"):
        # item is the .git folder, we want the parent
        repo_dir = item.parent
        if repo_dir != Path("."):
            git_dirs.append(repo_dir)

    if not git_dirs:
        console.print("No sub-repositories found.")
        return

    console.banner(f"Recursively pulling {len(git_dirs)} repositories")
    for d in git_dirs:
        console.print(f"\n--- {d.name} ---")
        try:
            subprocess.run(["git", "-C", str(d), "pull"], check=True)
        except subprocess.CalledProcessError as e:
            console.error(f"Failed to pull {d.name}: {e}")


@git_group.command(name="multi")
@click.argument("command")
def multi_cmd(command):
    """
    Execute a git command in all subdirectories that are git repositories.

    Usage:
        cmc git multi <command>

    Example:
        $ cmc git multi "pull origin main"
    """
    git_dirs = []
    for item in Path(".").iterdir():
        if item.is_dir() and (item / ".git").exists():
            git_dirs.append(item)

    if not git_dirs:
        console.warning("No git repositories found in subdirectories.")
        return

    console.banner(f"Executing '{command}' in {len(git_dirs)} repositories")
    for d in git_dirs:
        console.print(f"\n--- {d.name} ---")
        try:
            subprocess.run(["git", "-C", str(d), "sh", "-c", command], check=True)
        except subprocess.CalledProcessError as e:
            console.error(f"Failed in {d.name}: {e}")


@git_group.command(name="version-check")
@click.argument("package_name")
def version_check_cmd(package_name):
    """
    Compare local version with PyPI and GitHub.

    Usage:
        cmc git version-check <package_name>

    Example:
        $ cmc git version-check cloudmesh-ai-common
    """
    local_version = "Unknown"
    if Path("VERSION").exists():
        local_version = Path("VERSION").read_text().strip()

    pypi_version = "Unknown"
    try:
        resp = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
        if resp.status_code == 200:
            pypi_version = resp.json()["info"]["version"]
    except Exception as e:
        pypi_version = f"Error: {e}"

    gh_version = "Unknown"
    repo_name = (
        package_name if "cloudmesh/" in package_name else f"cloudmesh/{package_name}"
    )
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{repo_name}/releases/latest", timeout=5
        )
        if resp.status_code == 200:
            gh_version = resp.json()["tag_name"]
    except Exception as e:
        gh_version = f"Error: {e}"

    console.banner(f"Version Check for {package_name}")
    console.print(f"  Local:   {local_version}")
    console.print(f"  PyPI:    {pypi_version}")
    console.print(f"  GitHub:  {gh_version}")

    if (
        local_version != "Unknown"
        and pypi_version != "Unknown"
        and local_version != pypi_version
    ):
        console.warning("Local version differs from PyPI!")


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
    if not check_dependency(
        "git-filter-repo", "Install via: pip install git-filter-repo"
    ):
        return

    if not click.confirm(
        f"WARNING: This will permanently remove '{path}' from ALL history. Continue?",
        default=False,
    ):
        console.print("Operation cancelled.")
        return

    try:
        console.print(f"Nuking {path} from history...")
        subprocess.run(
            ["git-filter-repo", "--path", path, "--invert-paths"], check=True
        )
        console.ok(f"Successfully removed {path} from history.")
    except subprocess.CalledProcessError as e:
        console.error(f"Error during nuke operation: {e}")


@git_group.command(name="clean-history")
def clean_history_cmd():
    """
    Guided workflow to clean sensitive data or rewrite history.

    Usage:
        cmc git clean-history
    """
    if not check_dependency(
        "git-filter-repo", "Install via: pip install git-filter-repo"
    ):
        return

    console.banner("History Cleaning Guide")
    console.print("1. To remove a specific file: use 'cmc git nuke <path>'")
    console.print("2. To change authors: use 'git nuke <dir_path>'")
    console.print("3. To remove a directory: use 'cmc git nuke <dir_path>'")
    console.warning("Note: Always backup your repository before rewriting history.")


@git_group.command(name="sync-gh")
def sync_gh_cmd():
    """
    Sync local state with GitHub using the gh CLI.

    Usage:
        cmc git sync-gh
    """
    if not check_dependency(
        "gh", "Install via: brew install gh (macOS) or official gh docs"
    ):
        return

    try:
        console.print("Syncing with GitHub...")
        subprocess.run(["gh", "pr", "list"], check=True)
        console.ok("Local state synced with GitHub PRs.")
    except subprocess.CalledProcessError as e:
        console.error(f"Error syncing with GitHub: {e}")


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
        console.banner(f"Merging {repo_name} into current repository")

        subprocess.run(["git", "remote", "add", repo_name, url], check=True)
        subprocess.run(["git", "fetch", repo_name], check=True)
        subprocess.run(
            ["git", "merge", f"{repo_name}/master", "--allow-unrelated-histories"],
            check=True,
        )

        console.ok(f"Successfully merged {repo_name} into current repository.")
    except subprocess.CalledProcessError as e:
        console.error(f"Error merging repositories: {e}")


@git_group.command(name="user")
@click.argument("action", required=False)
@click.argument("username", required=False)
def users_cmd(action, username):
    """
    Manage configured GitHub usernames.

    Usage:
        cmc git user
        cmc git user add <username>
        cmc git user remove <username>
    """
    config = UserConfig()

    if action == "add":
        if not username:
            console.error("Username is required for 'add' action.")
            return
        if config.add_user(username):
            console.ok(f"Added user {username}")
        else:
            console.warning(f"User {username} already exists in config.")
    elif action == "remove":
        if not username:
            console.error("Username is required for 'remove' action.")
            return
        if config.remove_user(username):
            console.ok(f"Removed user {username}")
        else:
            console.warning(f"User {username} not found in config.")
    else:
        users = config.get_users()
        if not users:
            console.warning("No users configured. Use 'cmc git user add <username>'")
        else:
            console.banner("Configured GitHub Users")
            for u in users:
                console.print(f"- {u}")


@click.group(name="info", invoke_without_command=True)
@click.pass_context
def info_group(ctx):
    """
    GitHub and local contribution statistics.
    """
    if ctx.invoked_subcommand is None:
        # Default behavior: show contribution statistics for the current repository
        try:
            cmd = 'git ls-files | xargs -n1 git blame -w -M -C -C --line-porcelain | grep "^author " | sort | uniq -c | sort -nr'
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, check=True
            )

            console.banner("Contribution Statistics (Lines of Code)")
            if not result.stdout.strip():
                console.warning("No contribution data found.")
            else:
                console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            console.error(f"Error calculating stats: {e}")


# Removed fetch_repo_details as it is now handled by GitHubRepo class in common


def fetch_all_repos_for_user(user, force, config, auth_user=None):
    """
    Helper to fetch and enrich all repositories for a user, similar to stat_user_cmd.
    """
    excludes = config.get_excludes()

    def is_excluded(repo_name):
        for pattern in excludes:
            if re.search(pattern, repo_name):
                return True
        return False

    all_repos = None
    if not force:
        all_repos = config.get_cached_repos(user)

    if all_repos is None:
        include_username = user.lower() != (auth_user.lower() if auth_user else "")

        repos_json = gh.user(user).list_repos(
            limit=1000,
            json_fields="name,nameWithOwner,description,homepageUrl,visibility,updatedAt,createdAt",
            include_username=include_username,
        )
        repos = []
        for r in repos_json:
            repo_name = r["nameWithOwner"]
            if is_excluded(repo_name):
                continue
            repos.append(
                {
                    "repo": repo_name,
                    "url": f"https://github.com/{repo_name}",
                    "description": r.get("description") or "",
                    "website": r.get("homepageUrl") or "",
                    "visibility": r["visibility"],
                    "date": r["updatedAt"],
                    "created_at": r.get("createdAt"),
                }
            )

        orgs = gh.user(user).get_orgs()
        all_repos = list(repos)
        for org in orgs:
            org_repos_json = gh.org(org).list_repos(
                limit=1000,
                json_fields="name,nameWithOwner,description,homepageUrl,visibility,updatedAt,createdAt",
            )
            for r in org_repos_json:
                repo_name = r["nameWithOwner"]
                if is_excluded(repo_name):
                    continue
                all_repos.append(
                    {
                        "repo": repo_name,
                        "url": f"https://github.com/{repo_name}",
                        "description": r.get("description") or "",
                        "website": r.get("homepageUrl") or "",
                        "visibility": r["visibility"],
                        "date": r["updatedAt"],
                        "created_at": r.get("createdAt"),
                    }
                )
        
        # Merge with existing cache to avoid deleting enriched metadata
        existing_cache = config.get_cached_repos(user) or []
        cache_map = {r["repo"]: r for r in existing_cache if isinstance(r, dict) and "repo" in r}
        
        merged_repos = []
        for repo in all_repos:
            repo_name = repo["repo"]
            if repo_name in cache_map:
                # Keep the enriched version from cache
                merged_repos.append(cache_map[repo_name])
            else:
                # Add the new basic repo info
                merged_repos.append(repo)
        
        config.save_cached_repos(user, merged_repos)
        all_repos = merged_repos

    if not all_repos:
        return []

    # Phase 2: Incremental Enrichment
    cached_data = config.get_cached_repos(user) or []
    existing_metadata = {r["repo"]: r for r in cached_data if "size" in r or "pull_requests" in r}

    enriched_repos = []
    for repo in all_repos:
        repo_name = repo["repo"]
        
        if repo_name in existing_metadata:
            enriched_repos.append(existing_metadata[repo_name])
            continue
            
        repo_result = fetch_repo_stats(user, repo)
        if "error" not in repo_result:
            cache_entry = repo_result.copy()
            cache_entry.pop("_raw_data", None)
            enriched_repos.append(cache_entry)
        else:
            enriched_repos.append(repo)
            
        time.sleep(0.1)

    config.save_cached_repos(user, enriched_repos)
    return enriched_repos


# Removed generate_info_html as it is now in GitInfoView class


def fetch_repo_stats(user, repo_data):
    """
    Fetches detailed statistics for a single repository using GraphQL to minimize API calls.
    """
    repo_full_name = repo_data["repo"]
    try:
        # Split owner and repo name for GraphQL
        if "/" not in repo_full_name:
            return {"repo": repo_full_name, "error": "Invalid repo name format (expected owner/repo)"}
        
        owner, name = repo_full_name.split("/", 1)
        repo_obj = gh.repo(repo_full_name)
        
        # Refined GraphQL query to avoid argument conflicts and missing required args
        query = """
        query($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) {
            stargazers { totalCount }
            forks { totalCount }
            pullRequests { totalCount }
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 1) {
                    nodes {
                      committedDate
                    }
                  }
                }
              }
            }
            latestRelease {
              tagName
            }
            issues(states: OPEN) {
              totalCount
            }
          }
        }
        """
        
        # Execute GraphQL query with both owner and name
        gql_res = repo_obj._run([
            "api", "graphql", 
            "-f", f"query={query}", 
            "-f", f"owner={owner}", 
            "-f", f"name={name}"
        ])
        
        # Use REST call for size, default_branch, and ref counts (more stable than GraphQL for these)
        rest_data = repo_obj.get()
        
        details = {}
        if gql_res and "data" in gql_res and gql_res["data"].get("repository"):
            repo = gql_res["data"]["repository"]
            details["pull_requests"] = repo.get("pullRequests", {}).get("totalCount", 0)
            
            # Extract last push date
            db_ref = repo.get("defaultBranchRef")
            if db_ref and db_ref.get("target"):
                history = db_ref["target"].get("history")
                if history and history.get("nodes"):
                    details["last_push"] = history["nodes"][0].get("committedDate")
            
            details["release_version"] = (repo.get("latestRelease") or {}).get("tagName")
            details["issues"] = repo.get("issues", {}).get("totalCount", 0) - details["pull_requests"]

        # Enrich with REST data
        if rest_data:
            details["size"] = rest_data.get("size")
            details["default_branch"] = rest_data.get("default_branch", "Unknown")
            # Use REST for branch/tag counts if available or just leave as N/A
            # Note: gh repo view or similar could provide these, but we'll stick to basic REST
        
        # Only keep counts > 0
        filtered_details = {
            k: v for k, v in details.items() if v != 0 and v is not None
        }

        # Merge enriched data back into repo_data
        enriched_data = repo_data.copy()
        enriched_data.update(filtered_details)
        enriched_data["_raw_data"] = rest_data if rest_data else {}

        return enriched_data
    except Exception as e:
        return {"repo": repo_full_name, "error": str(e)}


@info_group.command(name="user")
@click.argument("username", required=False)
@click.option(
    "--force", is_flag=True, help="Force refresh of repository cache from GitHub."
)
def stat_user_cmd(username, force):
    """
    Get basic statistics for a GitHub user or all configured users.

    Usage:
        cmc git stat user <username>
        cmc git stat user all
    """
    if not check_dependency("gh", "Install via: brew install gh"):
        return

    # Check authentication status to warn about rate limits
    try:
        gh.get_authenticated_user()
    except GitHubError:
        console.warning("You are not authenticated with 'gh'. You will be subject to much lower API rate limits (60/hr).")
        console.print("To increase your limit, run: gh auth login")

    config = UserConfig()
    users_to_check = []

    if username == "all":
        users_to_check = config.get_users()
        if not users_to_check:
            console.error("No users configured in ~/.config/cloudmesh/git/config.yaml")
            return
    elif username:
        users_to_check = [username]
    else:
        # Use current gh authenticated user
        user = gh.get_authenticated_user()
        if user:
            users_to_check = [user]
        else:
            console.error(
                "Could not determine current gh user. Please specify a username or use 'all'."
            )
            return

    for user in users_to_check:
        console.banner(f"Stats for {user}")

        # Show .gitconfig and .gitignore content
        for filename in [".gitconfig", ".gitignore"]:
            file_path = Path.home() / filename
            if file_path.exists():
                console.banner(f"Content of {filename}")
                try:
                    content = file_path.read_text()
                    console.print(content if content.strip() else "File is empty.")
                except Exception as e:
                    console.error(f"Could not read {filename}: {e}")

        try:
            # Check cache first unless force is requested
            all_repos = None
            # Use a local variable to track if we encountered a GitHubError
            gh_error_occurred = False
            if not force:
                all_repos = config.get_cached_repos(user)
                if all_repos:
                    console.print(f"Using cached repository list for {user}.")

            if all_repos is None:
                console.banner(f"Fetching repositories for {user}...")
                with console.status(f"Fetching repositories for {user}..."):
                    # Determine if we should include username in the gh command
                    # If the user is the authenticated user, omitting the username lists all repos (including private)
                    auth_user = gh.get_authenticated_user()
                    # Normalize usernames to lowercase for comparison
                    include_username = user.lower() != (
                        auth_user.lower() if auth_user else ""
                    )

                    # 1. Get user's own repos using JSON for better data
                    repos_json = gh.user(user).list_repos(
                        limit=1000,
                        json_fields="name,nameWithOwner,description,homepageUrl,visibility,updatedAt,createdAt",
                        include_username=include_username,
                    )
                    repos = []
                    for r in repos_json:
                        repos.append(
                            {
                                "repo": r["nameWithOwner"],
                                "url": f"https://github.com/{r['nameWithOwner']}",
                                "description": r.get("description") or "",
                                "website": r.get("homepageUrl") or "",
                                "visibility": r["visibility"],
                                "date": r["updatedAt"],
                                "created_at": r.get("createdAt"),
                            }
                        )

                    # 2. Get organizations the user belongs to
                    orgs = gh.user(user).get_orgs()

                    all_repos = list(repos)
                    for org in orgs:
                        org_repos_json = gh.org(org).list_repos(
                            limit=1000,
                            json_fields="name,nameWithOwner,description,homepageUrl,visibility,updatedAt,createdAt",
                        )
                        for r in org_repos_json:
                            all_repos.append(
                                {
                                    "repo": r["nameWithOwner"],
                                    "url": f"https://github.com/{r['nameWithOwner']}",
                                    "description": r.get("description") or "",
                                    "website": r.get("homepageUrl") or "",
                                    "visibility": r["visibility"],
                                    "date": r["updatedAt"],
                                    "created_at": r.get("createdAt"),
                                }
                            )

                    # Save to cache
                    config.save_cached_repos(user, all_repos)

            if not all_repos:
                msg = "No repositories found."
                if include_username:
                    msg = "No public repositories found."
                console.print(msg)
                continue

            console.print(
                f"Found {len(all_repos)} repositories (including organizations)."
            )

            with Progress(console=console) as progress:
                task = progress.add_task(
                    "[cyan]Fetching stats...", total=len(all_repos)
                )

                # Use the helper function which now handles incremental enrichment and sequential processing
                enriched_repos = fetch_all_repos_for_user(
                    user, force=force, config=config, auth_user=gh.get_authenticated_user()
                )

                # Since fetch_all_repos_for_user does the work, we just print the results
                # and update the progress bar.
                for repo_result in enriched_repos:
                    progress.update(task, advance=1)
                    repo_name = repo_result["repo"]

                    if "error" in repo_result:
                        progress.console.print(
                            f"- {repo_name}: Error fetching stats: {repo_result['error']}"
                        )
                        continue

                    # Extract raw data for stars/forks (if available in the cached/fetched result)
                    # Note: fetch_all_repos_for_user removes _raw_data before returning, 
                    # so we rely on the enriched fields.
                    
                    filtered_details = {
                        k: v
                        for k, v in repo_result.items()
                        if k
                        not in [
                            "repo",
                            "url",
                            "description",
                            "website",
                            "visibility",
                            "date",
                            "created_at",
                        ]
                    }

                    # We can't get stargazers_count from filtered_details because it's in _raw_data
                    # But we can use the enriched fields we have.
                    stats_line = f"- {repo_name}:"
                    
                    if "branches" in filtered_details:
                        stats_line += f", Branches: {filtered_details['branches']}"
                    if "tags" in filtered_details:
                        stats_line += f", Tags: {filtered_details['tags']}"
                    if "issues" in filtered_details:
                        stats_line += f", Issues: {filtered_details['issues']}"
                    if "pull_requests" in filtered_details:
                        stats_line += f", PRs: {filtered_details['pull_requests']}"
                    if "contributors" in filtered_details:
                        stats_line += f", Contributors: {filtered_details['contributors']}"
                    if "release_version" in filtered_details:
                        stats_line += f", Release: {filtered_details['release_version']}"
                    if "size" in filtered_details:
                        size_kb = filtered_details["size"]
                        if size_kb > 1024 * 1024:
                            size_str = f"{size_kb / (1024 * 1024):.2f} GB"
                        elif size_kb > 1024:
                            size_str = f"{size_kb / 1024:.2f} MB"
                        else:
                            size_str = f"{size_kb} KB"
                        stats_line += f", Size: {size_str}"

                    # Add metadata
                    meta = []
                    if "last_push" in filtered_details:
                        meta.append(f"Last Push: {filtered_details['last_push']}")
                    if "created_at" in repo_result:
                        meta.append(f"Created: {repo_result['created_at']}")
                    if "default_branch" in filtered_details:
                        meta.append(f"Default Branch: {filtered_details['default_branch']}")

                    if meta:
                        stats_line += f" | {' | '.join(meta)}"

                    progress.console.print(stats_line)

        except GitHubError as e:
            console.error(f"GitHub error for {user}: {e}")
            console.print("Please ensure you are authenticated with 'gh auth login'.")
        except subprocess.CalledProcessError as e:
            console.error(f"Error fetching stats for {user}: {e}")


@info_group.command(name="org")
@click.argument("org_name", required=False)
def stat_org_cmd(org_name):
    """
    Get basic statistics for a GitHub organization or list all organizations.

    Usage:
        cmc git info org [org_name]
    """
    if not check_dependency("gh", "Install via: brew install gh"):
        return

    if not org_name:
        # List all organizations the authenticated user belongs to
        auth_user = gh.get_authenticated_user()
        if not auth_user:
            console.error("Could not determine authenticated GitHub user.")
            return
        
        console.banner(f"Organizations for {auth_user}")
        orgs = gh.user(auth_user).get_orgs()
        if not orgs:
            console.print("No organizations found.")
        else:
            for org in sorted(orgs):
                console.print(f"- {org}")
        return

    console.banner(f"Stats for Organization: {org_name}")
    try:
        org_obj = gh.org(org_name)
        data = org_obj.get_info()
        if data:
            console.print(f"Description: {data.get('description')}")
            console.print(f"Location: {data.get('location')}")

        count = org_obj.get_public_repos_count()
        console.print(f"Public Repositories: {count}")

    except Exception as e:
        console.error(f"Error fetching stats for organization {org_name}: {e}")


from cloudmesh.ai.command.git_view import GitInfoView


@info_group.command(name="view")
def info_view_cmd():
    """
    Open a web-based view of repository statistics with search and links.
    This view reads only from the local cache in the YAML config.

    Usage:
        cmc git info view
    """
    config = UserConfig()
    users = config.get_users()
    if not users:
        console.error("No users configured. Use 'cmc git user add <username>'")
        return

    all_user_data = {}

    # Read only from cache
    for user in users:
        repos = config.get_cached_repos(user)
        all_user_data[user] = repos or []

    # Use GitInfoView class to generate and open the HTML
    view = GitInfoView(
        all_user_data,
        excludes=config.get_excludes(),
        backup_dir=config.get_backup_dir(),
    )
    view.open_in_browser()
    console.ok("Opening repository view in browser.")


@info_group.command(name="repo")
@click.argument("repo_name")
@click.option("--user", help="GitHub username if repo is not in a known org")
@click.option("--org", help="GitHub organization name")
def stat_repo_cmd(repo_name, user, org):
    """
    Get statistics for a specific repository.

    Usage:
        cmc git stat repo <repo> [--user=USER] [--org=ORG]
    """
    if not check_dependency("gh", "Install via: brew install gh"):
        return

    # Determine full repo name
    full_name = repo_name
    if user:
        full_name = f"{user}/{repo_name}"
    elif org:
        full_name = f"{org}/{repo_name}"
    else:
        # Try to guess from current directory if it's a git repo
        try:
            remote_url = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            # Extract owner/repo from URL
            if "github.com" in remote_url:
                parts = remote_url.split("github.com/")[-1].split(".git")[0].split("/")
                if len(parts) >= 2:
                    full_name = f"{parts[0]}/{parts[1]}"
        except Exception:
            console.error(
                "Could not determine repository owner. Please provide --user or --org."
            )
            return

    console.banner(f"Stats for Repository: {full_name}")
    try:
        repo_obj = gh.repo(full_name)
        data = repo_obj.get()
        if data:
            console.print(f"Description: {data.get('description')}")
            console.print(f"Stars: {data.get('stargazers_count')}")
            console.print(f"Forks: {data.get('forks_count')}")
            console.print(f"Open Issues: {data.get('open_issues_count')}")
            console.print(f"Language: {data.get('language')}")
            
            size_kb = data.get("size", 0)
            if size_kb > 1024 * 1024:
                size_str = f"{size_kb / (1024 * 1024):.2f} GB"
            elif size_kb > 1024:
                size_str = f"{size_kb / 1024:.2f} MB"
            else:
                size_str = f"{size_kb} KB"
            console.print(f"Size: {size_str}")
        else:
            console.warning("Could not retrieve repository data.")

    except Exception as e:
        console.error(f"Error fetching stats for repository {full_name}: {e}")


@click.group(name="backup")
def backup_group():
    """
    Manage repository backups.
    """
    pass


@backup_group.command(name="get")
@click.argument("target")
def backup_get_cmd(target):
    """
    Clone repositories for a specific user or all configured users.

    Usage:
        cmc git backup get <username>
        cmc git backup get all
    """
    if not check_dependency("gh", "Install via: brew install gh"):
        return

    config = UserConfig()
    users_to_backup = []

    if target == "all":
        users_to_backup = config.get_users()
        if not users_to_backup:
            console.error("No users configured in ~/.config/cloudmesh/git/config.yaml")
            return
    else:
        users_to_backup = [target]

    backup_root = config.get_backup_dir()
    backup_root.mkdir(parents=True, exist_ok=True)

    for user in users_to_backup:
        console.banner(f"Backing up repositories for {user}")
        user_dir = backup_root / user
        user_dir.mkdir(exist_ok=True)

        try:
            # 1. Get user's own repos
            repos = gh.user(user).list_repos(limit=1000, json_fields="sshUrl")

            # 2. Get organizations the user belongs to
            orgs = gh.user(user).get_orgs()

            all_repos_data = list(repos)
            for org in orgs:
                org_repos = gh.org(org).list_repos(limit=1000, json_fields="sshUrl")
                all_repos_data.extend(org_repos)

            for repo in all_repos_data:
                ssh_url = repo["sshUrl"]["url"]
                repo_name = ssh_url.split("/")[-1].replace(".git", "")
                repo_path = user_dir / repo_name

                if repo_path.exists():
                    console.print(f"Skipping {repo_name} (already exists)")
                    continue

                console.print(f"Cloning {repo_name}...")
                subprocess.run(["git", "clone", ssh_url, str(repo_path)], check=True)

        except subprocess.CalledProcessError as e:
            console.error(f"Error backing up user {user}: {e}")


@backup_group.command(name="set")
@click.argument("path")
def backup_set_cmd(path):
    """
    Set the backup directory location.

    Usage:
        cmc git backup set <dir>
    """
    config = UserConfig()
    config.set_backup_dir(path)
    console.ok(f"Backup directory set to: {config.get_backup_dir()}")


@backup_group.command(name="info")
def backup_info_cmd():
    """
    Information about the downloaded repos and comparing if they are the same on github.

    Usage:
        cmc git backup info
    """
    if not check_dependency("gh", "Install via: brew install gh"):
        return

    config = UserConfig()
    backup_root = config.get_backup_dir()

    if not backup_root.exists():
        console.error(f"Backup directory {backup_root} does not exist.")
        return

    console.banner("Backup Status Info")

    # Iterate through user/org directories
    for user_dir in backup_root.iterdir():
        if not user_dir.is_dir():
            continue

        console.print(f"\nUser/Org: {user_dir.name}")

        for repo_dir in user_dir.iterdir():
            if not repo_dir.is_dir() or not (repo_dir / ".git").exists():
                continue

            repo_name = repo_dir.name
            full_repo_name = f"{user_dir.name}/{repo_name}"

            try:
                # Get local HEAD hash
                local_hash = subprocess.run(
                    ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()

                # Get remote HEAD hash
                repo_obj = gh.repo(full_repo_name)
                remote_data = repo_obj.get()
                default_branch = (
                    remote_data.get("default_branch", "main") if remote_data else "main"
                )

                remote_hash = repo_obj._run(
                    ["api", f"repos/{full_repo_name}/commits/{default_branch}"]
                )
                if isinstance(remote_hash, dict):
                    remote_hash = remote_hash.get("sha")

                if local_hash == remote_hash:
                    console.print(f"  [green]✓[/green] {repo_name}: Up to date")
                else:
                    console.print(f"  [red]✗[/red] {repo_name}: Out of date")
                    console.print(f"      Local:  {local_hash[:7]}")
                    console.print(f"      Remote: {remote_hash[:7]}")

            except subprocess.CalledProcessError:
                console.print(
                    f"  [yellow]![/yellow] {repo_name}: Could not verify (remote not found or error)"
                )
            except Exception as e:
                console.print(f"  [yellow]![/yellow] {repo_name}: Error: {e}")


@git_group.command(name="summary")
def summary_cmd():
    """
    Generate a summary table of all configured GitHub users and their top repositories.

    Usage:
        cmc git summary
    """
    if not check_dependency("gh", "Install via: brew install gh"):
        return

    config = UserConfig()
    users = config.get_users()
    if not users:
        console.error("No users configured in ~/.config/cloudmesh/git/config.yaml")
        return

    table = Table(title="GitHub User Summary")
    table.add_column("Username", style="cyan")
    table.add_column("Total Repos", style="magenta")
    table.add_column("Top Repo (Stars)", style="green")

    console.banner("Fetching summary for all users...")

    for user in users:
        try:
            # 1. Get user's own repos
            repos = gh.user(user).list_repos(
                limit=100, json_fields="name,stargazersCount"
            )

            # 2. Get organizations the user belongs to
            orgs = gh.user(user).get_orgs()

            all_repos = list(repos)
            for org in orgs:
                org_repos = gh.org(org).list_repos(
                    limit=100, json_fields="name,stargazersCount"
                )
                all_repos.extend(org_repos)

            if not all_repos:
                table.add_row(user, "0", "N/A")
                continue

            # Find top repo by stars
            top_repo = max(all_repos, key=lambda x: x.get("stargazersCount", 0))
            table.add_row(
                user,
                str(len(all_repos)),
                f"{top_repo['name']} ({top_repo.get('stargazersCount', 0)})",
            )
        except subprocess.CalledProcessError:
            table.add_row(user, "Error", "Error")

    rich_console.print(table)


# Add the groups to the main git group
git_group.add_command(backup_group)
git_group.add_command(info_group)

entry_point = git_group


def register(cli):
    """
    Registers the git command group with the main CLI.

    Args:
        cli: The main click CLI object.
    """
    cli.add_command(git_group, name="git")