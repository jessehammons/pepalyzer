"""Tests for change aggregation logic."""

from datetime import datetime
from pathlib import Path
import tempfile

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
                message="Update PEP 1",
                files=[ChangedFile(path="pep-0001.rst", change_type="M")],
            )
        ]
        activities = aggregate_by_pep(commits)

        assert len(activities) == 1
        assert activities[0].pep_number == 1
        assert activities[0].commit_count == 1
        assert len(activities[0].files) == 1
        assert len(activities[0].commit_messages) == 1
        assert activities[0].commit_messages[0] == "Update PEP 1"

    def test_single_pep_multiple_commits(self) -> None:
        """Aggregate multiple commits touching same PEP."""
        commits = [
            CommitRecord(
                hash="abc123",
                timestamp=datetime(2024, 1, 15),
                message="Add initial draft of PEP 815",
                files=[ChangedFile(path="pep-0815.rst", change_type="M")],
            ),
            CommitRecord(
                hash="def456",
                timestamp=datetime(2024, 1, 16),
                message="Clarify tp_traverse requirements",
                files=[ChangedFile(path="pep-0815.rst", change_type="M")],
            ),
            CommitRecord(
                hash="ghi789",
                timestamp=datetime(2024, 1, 17),
                message="Add markdown version of PEP 815",
                files=[ChangedFile(path="pep-0815.md", change_type="A")],
            ),
        ]
        activities = aggregate_by_pep(commits)

        assert len(activities) == 1
        assert activities[0].pep_number == 815
        assert activities[0].commit_count == 3
        assert len(activities[0].files) == 2  # Unique files
        assert len(activities[0].commit_messages) == 3
        assert activities[0].commit_messages[0] == "Add initial draft of PEP 815"
        assert activities[0].commit_messages[1] == "Clarify tp_traverse requirements"
        assert activities[0].commit_messages[2] == "Add markdown version of PEP 815"

    def test_multiple_peps(self) -> None:
        """Aggregate commits touching multiple PEPs."""
        commits = [
            CommitRecord(
                hash="abc123",
                timestamp=datetime(2024, 1, 15),
                message="Update PEP 1 and PEP 815",
                files=[
                    ChangedFile(path="pep-0001.rst", change_type="M"),
                    ChangedFile(path="pep-0815.rst", change_type="M"),
                ],
            ),
            CommitRecord(
                hash="def456",
                timestamp=datetime(2024, 1, 16),
                message="Add PEP 2",
                files=[ChangedFile(path="pep-0002.rst", change_type="A")],
            ),
        ]
        activities = aggregate_by_pep(commits)

        assert len(activities) == 3
        pep_numbers = {a.pep_number for a in activities}
        assert pep_numbers == {1, 2, 815}

    def test_sort_by_pep_number_ascending(self) -> None:
        """Results should be sorted by PEP number (ascending)."""
        commits = [
            CommitRecord(
                hash="abc123",
                timestamp=datetime(2024, 1, 15),
                message="Update PEP 815 first time",
                files=[ChangedFile(path="pep-0815.rst", change_type="M")],
            ),
            CommitRecord(
                hash="def456",
                timestamp=datetime(2024, 1, 16),
                message="Update PEP 1",
                files=[ChangedFile(path="pep-0001.rst", change_type="M")],
            ),
            CommitRecord(
                hash="ghi789",
                timestamp=datetime(2024, 1, 17),
                message="Update PEP 815 second time",
                files=[ChangedFile(path="pep-0815.rst", change_type="M")],
            ),
            CommitRecord(
                hash="jkl012",
                timestamp=datetime(2024, 1, 18),
                message="Update PEP 100",
                files=[ChangedFile(path="pep-0100.rst", change_type="M")],
            ),
        ]
        activities = aggregate_by_pep(commits)

        assert len(activities) == 3
        # Should be sorted by PEP number (ascending), not commit count
        assert activities[0].pep_number == 1
        assert activities[1].pep_number == 100
        assert activities[2].pep_number == 815
        # Commit counts are auxiliary, not used for sorting
        assert activities[2].commit_count == 2  # PEP 815 has most commits

    def test_filter_non_pep_files(self) -> None:
        """Non-PEP files should be filtered out."""
        commits = [
            CommitRecord(
                hash="abc123",
                timestamp=datetime(2024, 1, 15),
                message="Update PEP 1 and other files",
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
                message="Update repository infrastructure",
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
                message="First update to PEP 1",
                files=[ChangedFile(path="pep-0001.rst", change_type="M")],
            ),
            CommitRecord(
                hash="def456",
                timestamp=datetime(2024, 1, 16),
                message="Second update to PEP 1",
                files=[
                    ChangedFile(path="pep-0001.rst", change_type="M")
                ],  # Same file again
            ),
        ]
        activities = aggregate_by_pep(commits)

        assert len(activities) == 1
        assert activities[0].commit_count == 2
        assert len(activities[0].files) == 1  # Deduplicated

    def test_aggregate_without_repo_path(self) -> None:
        """Backward compatibility: works without repo_path."""
        commits = [
            CommitRecord(
                hash="abc123",
                timestamp=datetime(2024, 1, 15),
                message="Update PEP 815",
                files=[ChangedFile(path="pep-0815.rst", change_type="M")],
            )
        ]
        activities = aggregate_by_pep(commits, repo_path=None)

        assert len(activities) == 1
        assert activities[0].pep_number == 815
        # Metadata fields should be None/empty without repo_path
        assert activities[0].title is None
        assert activities[0].status is None
        assert activities[0].abstract is None
        assert activities[0].authors == []

    def test_aggregate_with_metadata_extraction(self) -> None:
        """Extract metadata when repo_path is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test PEP file
            pep_path = Path(tmpdir) / "pep-0815.rst"
            pep_content = """\
PEP: 815
Title: Disallow reference cycles in tp_traverse
Author: Sam Gross <colesbury@gmail.com>
Status: Draft
Type: Standards Track
Created: 11-Jan-2024

Abstract
========

This PEP proposes disallowing reference cycles in tp_traverse.
"""
            pep_path.write_text(pep_content, encoding="utf-8")

            commits = [
                CommitRecord(
                    hash="abc123",
                    timestamp=datetime(2024, 1, 15),
                    message="Add initial draft of PEP 815",
                    files=[ChangedFile(path="pep-0815.rst", change_type="M")],
                )
            ]

            activities = aggregate_by_pep(commits, repo_path=tmpdir)

            assert len(activities) == 1
            assert activities[0].pep_number == 815
            # Metadata should be extracted
            assert activities[0].title == "Disallow reference cycles in tp_traverse"
            assert activities[0].status == "Draft"
            assert activities[0].abstract is not None
            assert "reference cycles" in activities[0].abstract
            assert "Sam Gross" in activities[0].authors[0]
            assert activities[0].pep_type == "Standards Track"
            assert activities[0].created == "11-Jan-2024"

    def test_aggregate_with_missing_file(self) -> None:
        """Handle gracefully when PEP file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't create the file - it's been deleted
            commits = [
                CommitRecord(
                    hash="abc123",
                    timestamp=datetime(2024, 1, 15),
                    message="Delete PEP 999",
                    files=[ChangedFile(path="pep-0999.rst", change_type="D")],
                )
            ]

            activities = aggregate_by_pep(commits, repo_path=tmpdir)

            assert len(activities) == 1
            assert activities[0].pep_number == 999
            # Metadata should be None when file can't be read
            assert activities[0].title is None
            assert activities[0].status is None
            assert activities[0].abstract is None

    def test_aggregate_with_multiple_files_tries_first_available(self) -> None:
        """Try multiple files, use first one that can be read."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only the .md file, not the .rst
            pep_md = Path(tmpdir) / "pep-0815.md"
            pep_md.write_text(
                "PEP: 815\nTitle: Test PEP\nStatus: Draft\n\nAbstract here.",
                encoding="utf-8",
            )

            commits = [
                CommitRecord(
                    hash="abc123",
                    timestamp=datetime(2024, 1, 15),
                    message="Convert PEP 815 from RST to Markdown",
                    files=[
                        ChangedFile(path="pep-0815.rst", change_type="D"),
                        ChangedFile(path="pep-0815.md", change_type="A"),
                    ],
                )
            ]

            activities = aggregate_by_pep(commits, repo_path=tmpdir)

            assert len(activities) == 1
            # Should extract from .md file (second in sorted order)
            assert activities[0].title == "Test PEP"
            assert activities[0].status == "Draft"

    def test_aggregate_with_partial_metadata(self) -> None:
        """Handle PEP with minimal metadata fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pep_path = Path(tmpdir) / "pep-0001.rst"
            pep_content = """\
PEP: 1
Title: PEP Purpose and Guidelines
Status: Active

This is the abstract.
"""
            pep_path.write_text(pep_content, encoding="utf-8")

            commits = [
                CommitRecord(
                    hash="abc123",
                    timestamp=datetime(2024, 1, 15),
                    message="Update PEP 1 guidelines",
                    files=[ChangedFile(path="pep-0001.rst", change_type="M")],
                )
            ]

            activities = aggregate_by_pep(commits, repo_path=tmpdir)

            assert len(activities) == 1
            assert activities[0].title == "PEP Purpose and Guidelines"
            assert activities[0].status == "Active"
            # Optional fields should be None/empty
            assert activities[0].pep_type is None
            assert activities[0].created is None
            assert activities[0].authors == []

    def test_aggregate_prioritizes_main_document_over_supplementary(self) -> None:
        """Prioritize .rst/.md files over supplementary files like examples."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Python example file (no PEP headers)
            example_path = Path(tmpdir) / "pep-0821-examples.py"
            example_path.write_text(
                "# Example code for PEP 821\nprint('hello')\n",
                encoding="utf-8",
            )

            # Create the main PEP document
            pep_path = Path(tmpdir) / "pep-0821.rst"
            pep_content = """\
PEP: 821
Title: Improve importlib security
Status: Accepted

This PEP addresses security vulnerabilities.
"""
            pep_path.write_text(pep_content, encoding="utf-8")

            commits = [
                CommitRecord(
                    hash="abc123",
                    timestamp=datetime(2024, 1, 15),
                    message="Update PEP 821 and examples",
                    files=[
                        # Note: example file is alphabetically first
                        ChangedFile(path="pep-0821-examples.py", change_type="M"),
                        ChangedFile(path="pep-0821.rst", change_type="M"),
                    ],
                )
            ]

            activities = aggregate_by_pep(commits, repo_path=tmpdir)

            assert len(activities) == 1
            # Should extract from .rst file, NOT from -examples.py
            assert activities[0].title == "Improve importlib security"
            assert activities[0].status == "Accepted"
            assert activities[0].abstract is not None

    def test_aggregate_prefers_rst_over_md(self) -> None:
        """Prefer .rst over .md if both exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create both .rst and .md versions
            rst_path = Path(tmpdir) / "pep-0815.rst"
            rst_path.write_text(
                "PEP: 815\nTitle: RST Version\nStatus: Draft\n\nRST abstract.",
                encoding="utf-8",
            )

            md_path = Path(tmpdir) / "pep-0815.md"
            md_path.write_text(
                "PEP: 815\nTitle: MD Version\nStatus: Draft\n\nMD abstract.",
                encoding="utf-8",
            )

            commits = [
                CommitRecord(
                    hash="abc123",
                    timestamp=datetime(2024, 1, 15),
                    message="Update PEP 815 in both formats",
                    files=[
                        ChangedFile(path="pep-0815.md", change_type="A"),
                        ChangedFile(path="pep-0815.rst", change_type="M"),
                    ],
                )
            ]

            activities = aggregate_by_pep(commits, repo_path=tmpdir)

            assert len(activities) == 1
            # Should prefer .rst over .md
            assert activities[0].title == "RST Version"
