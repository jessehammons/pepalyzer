"""Tests for change aggregation logic."""

from datetime import datetime

from pepalyzer.aggregator import aggregate_by_pep
from pepalyzer.models import ChangedFile, CommitRecord


class TestAggregateByPep:
    """Test aggregation of commits into PEP-centric activity."""

    def test_single_pep_single_commit(self) -> None:
        """Aggregate single commit touching one PEP."""
        commits = [
            CommitRecord(
                hash="abc123",
                timestamp=datetime(2024, 1, 15),
                files=[ChangedFile(path="pep-0001.rst", change_type="M")],
            )
        ]
        activities = aggregate_by_pep(commits)

        assert len(activities) == 1
        assert activities[0].pep_number == 1
        assert activities[0].commit_count == 1
        assert len(activities[0].files) == 1

    def test_single_pep_multiple_commits(self) -> None:
        """Aggregate multiple commits touching same PEP."""
        commits = [
            CommitRecord(
                hash="abc123",
                timestamp=datetime(2024, 1, 15),
                files=[ChangedFile(path="pep-0815.rst", change_type="M")],
            ),
            CommitRecord(
                hash="def456",
                timestamp=datetime(2024, 1, 16),
                files=[ChangedFile(path="pep-0815.rst", change_type="M")],
            ),
            CommitRecord(
                hash="ghi789",
                timestamp=datetime(2024, 1, 17),
                files=[ChangedFile(path="pep-0815.md", change_type="A")],
            ),
        ]
        activities = aggregate_by_pep(commits)

        assert len(activities) == 1
        assert activities[0].pep_number == 815
        assert activities[0].commit_count == 3
        assert len(activities[0].files) == 2  # Unique files

    def test_multiple_peps(self) -> None:
        """Aggregate commits touching multiple PEPs."""
        commits = [
            CommitRecord(
                hash="abc123",
                timestamp=datetime(2024, 1, 15),
                files=[
                    ChangedFile(path="pep-0001.rst", change_type="M"),
                    ChangedFile(path="pep-0815.rst", change_type="M"),
                ],
            ),
            CommitRecord(
                hash="def456",
                timestamp=datetime(2024, 1, 16),
                files=[ChangedFile(path="pep-0002.rst", change_type="A")],
            ),
        ]
        activities = aggregate_by_pep(commits)

        assert len(activities) == 3
        pep_numbers = {a.pep_number for a in activities}
        assert pep_numbers == {1, 2, 815}

    def test_sort_by_commit_count_descending(self) -> None:
        """Results should be sorted by commit count (most active first)."""
        commits = [
            CommitRecord(
                hash="abc123",
                timestamp=datetime(2024, 1, 15),
                files=[ChangedFile(path="pep-0001.rst", change_type="M")],
            ),
            CommitRecord(
                hash="def456",
                timestamp=datetime(2024, 1, 16),
                files=[ChangedFile(path="pep-0815.rst", change_type="M")],
            ),
            CommitRecord(
                hash="ghi789",
                timestamp=datetime(2024, 1, 17),
                files=[ChangedFile(path="pep-0815.rst", change_type="M")],
            ),
            CommitRecord(
                hash="jkl012",
                timestamp=datetime(2024, 1, 18),
                files=[ChangedFile(path="pep-0815.rst", change_type="M")],
            ),
        ]
        activities = aggregate_by_pep(commits)

        assert len(activities) == 2
        # PEP 815 has 3 commits, should be first
        assert activities[0].pep_number == 815
        assert activities[0].commit_count == 3
        # PEP 1 has 1 commit, should be second
        assert activities[1].pep_number == 1
        assert activities[1].commit_count == 1

    def test_filter_non_pep_files(self) -> None:
        """Non-PEP files should be filtered out."""
        commits = [
            CommitRecord(
                hash="abc123",
                timestamp=datetime(2024, 1, 15),
                files=[
                    ChangedFile(path="pep-0001.rst", change_type="M"),
                    ChangedFile(path="README.md", change_type="M"),
                    ChangedFile(path=".gitignore", change_type="M"),
                    ChangedFile(path="build/index.html", change_type="A"),
                ],
            )
        ]
        activities = aggregate_by_pep(commits)

        assert len(activities) == 1
        assert activities[0].pep_number == 1
        # Only PEP file should be counted
        assert len(activities[0].files) == 1

    def test_empty_commits(self) -> None:
        """Handle empty commit list."""
        activities = aggregate_by_pep([])
        assert len(activities) == 0

    def test_commits_with_no_pep_files(self) -> None:
        """Handle commits with no PEP files."""
        commits = [
            CommitRecord(
                hash="abc123",
                timestamp=datetime(2024, 1, 15),
                files=[
                    ChangedFile(path="README.md", change_type="M"),
                    ChangedFile(path=".gitignore", change_type="M"),
                ],
            )
        ]
        activities = aggregate_by_pep(commits)
        assert len(activities) == 0

    def test_deduplicate_files_per_pep(self) -> None:
        """Files should be deduplicated per PEP."""
        commits = [
            CommitRecord(
                hash="abc123",
                timestamp=datetime(2024, 1, 15),
                files=[ChangedFile(path="pep-0001.rst", change_type="M")],
            ),
            CommitRecord(
                hash="def456",
                timestamp=datetime(2024, 1, 16),
                files=[
                    ChangedFile(path="pep-0001.rst", change_type="M")
                ],  # Same file again
            ),
        ]
        activities = aggregate_by_pep(commits)

        assert len(activities) == 1
        assert activities[0].commit_count == 2
        assert len(activities[0].files) == 1  # Deduplicated
