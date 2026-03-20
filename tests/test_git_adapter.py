"""Tests for Git adapter (integration tests with real Git)."""

from datetime import datetime
from pathlib import Path
import subprocess
import tempfile

from pepalyzer.git_adapter import get_commit_diff, get_recent_commits


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

    def test_get_commit_diff_single_file(self) -> None:
        """Get diff for a specific file in a commit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            # Setup: Initialize git repo
            subprocess.run(["git", "init"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"], cwd=repo, check=True
            )

            # Setup: Create PEP with Draft status
            pep_file = repo / "pep-0815.rst"
            pep_file.write_text("PEP: 815\nStatus: Draft\n")
            subprocess.run(["git", "add", "pep-0815.rst"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial draft"], cwd=repo, check=True
            )

            # Setup: Change status to Final
            pep_file.write_text("PEP: 815\nStatus: Final\n")
            subprocess.run(["git", "add", "pep-0815.rst"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Mark as Final"], cwd=repo, check=True
            )

            # Get commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            commit_hash = result.stdout.strip()

            # TEST: Get the diff
            diff_text = get_commit_diff(str(repo), commit_hash, "pep-0815.rst")

            # ASSERT: Verify diff contains status change
            assert "-Status: Draft" in diff_text
            assert "+Status: Final" in diff_text

    def test_get_commit_diff_nonexistent_file(self) -> None:
        """Handle diff for file that doesn't exist in commit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            # Setup: Initialize git repo
            subprocess.run(["git", "init"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"], cwd=repo, check=True
            )

            # Create and commit one file
            pep_file = repo / "pep-0815.rst"
            pep_file.write_text("PEP: 815\n")
            subprocess.run(["git", "add", "pep-0815.rst"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "Add PEP"], cwd=repo, check=True)

            # Get commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            commit_hash = result.stdout.strip()

            # TEST: Request diff for a file that wasn't in this commit
            diff_text = get_commit_diff(str(repo), commit_hash, "pep-9999.rst")

            # ASSERT: Should return empty string
            assert diff_text == ""

    def test_get_commit_diff_invalid_commit(self) -> None:
        """Handle diff for invalid commit hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            # Setup: Initialize git repo with one commit
            subprocess.run(["git", "init"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"], cwd=repo, check=True
            )

            pep_file = repo / "pep-0815.rst"
            pep_file.write_text("PEP: 815\n")
            subprocess.run(["git", "add", "pep-0815.rst"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "Add PEP"], cwd=repo, check=True)

            # TEST: Request diff for invalid commit hash
            diff_text = get_commit_diff(str(repo), "0000000000", "pep-0815.rst")

            # ASSERT: Should return empty string
            assert diff_text == ""
