"""Git adapter for reading commit history.

This module provides read-only access to Git repository history.
"""

from datetime import datetime
import subprocess

from pepalyzer.models import ChangedFile, CommitRecord


def get_recent_commits(repo_path: str, since: str) -> list[CommitRecord]:
    """Get recent commits from a Git repository.

    Args:
        repo_path: Path to the Git repository.
        since: Time specification (e.g., "30d", "1 week ago", "2024-01-01").

    Returns:
        List of CommitRecord objects, in chronological order (oldest first).

    Examples:
        >>> commits = get_recent_commits("~/peps", "30d")
        >>> len(commits)
        15
    """
    try:
        # Use git log with --name-status to get changed files
        # Format: %H = commit hash, %aI = author date ISO format
        result = subprocess.run(
            [
                "git",
                "log",
                f"--since={since}",
                "--name-status",
                "--pretty=format:COMMIT:%H:%aI",
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

        commits = _parse_git_log(result.stdout)
        # Reverse to get chronological order (oldest first)
        commits.reverse()
        return commits

    except subprocess.CalledProcessError:
        # Not a git repo, or other git error
        return []
    except FileNotFoundError:
        # git command not found or path doesn't exist
        return []


def _parse_git_log(git_output: str) -> list[CommitRecord]:
    """Parse git log output into CommitRecord objects.

    Expected format:
        COMMIT:abc123:2024-01-15T10:30:00+00:00
        A       pep-0001.rst
        M       pep-0002.rst

        COMMIT:def456:2024-01-16T14:20:00+00:00
        M       pep-0001.rst

    Args:
        git_output: Raw output from git log command.

    Returns:
        List of CommitRecord objects.
    """
    commits: list[CommitRecord] = []
    current_hash: str | None = None
    current_timestamp: datetime | None = None
    current_files: list[ChangedFile] = []

    def save_commit() -> None:
        """Helper to save current commit if valid."""
        if current_hash and current_timestamp is not None:
            commits.append(
                CommitRecord(
                    hash=current_hash,
                    timestamp=current_timestamp,
                    files=current_files.copy(),
                )
            )

    for line in git_output.split("\n"):
        line = line.strip()
        if not line:
            # Empty line - skip
            continue

        if line.startswith("COMMIT:"):
            # Save previous commit before starting new one
            save_commit()

            # Parse new commit header
            parts = line.split(":")
            current_hash = parts[1]
            timestamp_str = parts[2]
            # Parse ISO format timestamp
            current_timestamp = datetime.fromisoformat(timestamp_str)
            current_files = []  # Reset files for new commit

        elif "\t" in line:
            # File change line: "M\tpep-0001.rst"
            change_type, file_path = line.split("\t", 1)
            current_files.append(ChangedFile(path=file_path, change_type=change_type))

    # Don't forget the last commit
    save_commit()

    return commits
