"""Tests for Git adapter (integration tests with real Git)."""

from datetime import datetime
from pathlib import Path
import subprocess
import tempfile

from pepalyzer.git_adapter import get_recent_commits


class TestGitAdapter:
    """Integration tests for Git adapter.

    These tests create temporary Git repositories to test
    real Git interactions.
    """

    def test_get_commits_from_simple_repo(self) -> None:
        """Get commits from a simple Git repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Initialize repo
            subprocess.run(["git", "init"], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo_path,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=repo_path,
                check=True,
            )

            # Create a PEP file and commit it
            pep_file = repo_path / "pep-0001.rst"
            pep_file.write_text("PEP: 1\nTitle: Test\n")
            subprocess.run(["git", "add", "pep-0001.rst"], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Add PEP 1"], cwd=repo_path, check=True
            )

            # Get commits
            commits = get_recent_commits(str(repo_path), since="1 year ago")

            assert len(commits) == 1
            assert len(commits[0].files) == 1
            assert commits[0].files[0].path == "pep-0001.rst"
            assert commits[0].files[0].change_type == "A"  # Added

    def test_get_commits_with_modifications(self) -> None:
        """Get commits including file modifications."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Setup repo
            subprocess.run(["git", "init"], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo_path,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=repo_path,
                check=True,
            )

            # Create and commit file
            pep_file = repo_path / "pep-0815.rst"
            pep_file.write_text("Version 1\n")
            subprocess.run(["git", "add", "pep-0815.rst"], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Add PEP 815"], cwd=repo_path, check=True
            )

            # Modify and commit again
            pep_file.write_text("Version 2\n")
            subprocess.run(["git", "add", "pep-0815.rst"], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Update PEP 815"], cwd=repo_path, check=True
            )

            # Get commits
            commits = get_recent_commits(str(repo_path), since="1 year ago")

            assert len(commits) == 2
            # First commit (chronological) should show added file
            assert commits[0].files[0].change_type == "A"
            # Second commit should show modified file
            assert commits[1].files[0].change_type == "M"

    def test_get_commits_multiple_files(self) -> None:
        """Get commits with multiple files changed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Setup repo
            subprocess.run(["git", "init"], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo_path,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=repo_path,
                check=True,
            )

            # Create multiple files and commit together
            (repo_path / "pep-0001.rst").write_text("PEP 1\n")
            (repo_path / "pep-0002.rst").write_text("PEP 2\n")
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Add multiple PEPs"],
                cwd=repo_path,
                check=True,
            )

            commits = get_recent_commits(str(repo_path), since="1 year ago")

            assert len(commits) == 1
            assert len(commits[0].files) == 2
            file_paths = {f.path for f in commits[0].files}
            assert file_paths == {"pep-0001.rst", "pep-0002.rst"}

    def test_empty_repository(self) -> None:
        """Handle empty repository with no commits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=repo_path, check=True)

            commits = get_recent_commits(str(repo_path), since="1 year ago")

            assert len(commits) == 0

    def test_invalid_repository_path(self) -> None:
        """Handle invalid repository path gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Path exists but is not a git repo
            commits = get_recent_commits(tmpdir, since="1 year ago")
            assert len(commits) == 0

    def test_commit_timestamp_parsing(self) -> None:
        """Verify commit timestamps are parsed correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            # Setup repo
            subprocess.run(["git", "init"], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo_path,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=repo_path,
                check=True,
            )

            # Create commit
            pep_file = repo_path / "pep-0001.rst"
            pep_file.write_text("Test\n")
            subprocess.run(["git", "add", "pep-0001.rst"], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Add PEP 1"], cwd=repo_path, check=True
            )

            commits = get_recent_commits(str(repo_path), since="1 year ago")

            assert len(commits) == 1
            assert isinstance(commits[0].timestamp, datetime)
            # Should be a recent timestamp (this year)
            assert commits[0].timestamp.year >= 2024
