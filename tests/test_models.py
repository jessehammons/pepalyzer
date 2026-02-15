"""Tests for pepalyzer data models."""

from datetime import datetime

from pepalyzer.models import ChangedFile, CommitRecord, PepActivity, PepSignal


class TestChangedFile:
    """Test ChangedFile data model."""

    def test_create_changed_file(self) -> None:
        """Create a ChangedFile with valid data."""
        file = ChangedFile(path="pep-0001.rst", change_type="M")
        assert file.path == "pep-0001.rst"
        assert file.change_type == "M"

    def test_changed_file_immutable(self) -> None:
        """Test ChangedFile is immutable (frozen dataclass)."""
        file = ChangedFile(path="pep-0001.rst", change_type="M")
        try:
            file.path = "pep-0002.rst"  # type: ignore
            raise AssertionError("Should not allow mutation")
        except AttributeError:
            pass  # Expected

    def test_changed_file_repr(self) -> None:
        """Test ChangedFile has useful string representation."""
        file = ChangedFile(path="pep-0001.rst", change_type="M")
        repr_str = repr(file)
        assert "pep-0001.rst" in repr_str
        assert "M" in repr_str


class TestCommitRecord:
    """Test CommitRecord data model."""

    def test_create_commit_record(self) -> None:
        """Create a CommitRecord with valid data."""
        timestamp = datetime(2024, 1, 15, 10, 30)
        files = [
            ChangedFile(path="pep-0001.rst", change_type="M"),
            ChangedFile(path="pep-0002.rst", change_type="A"),
        ]
        commit = CommitRecord(
            hash="abc123",
            timestamp=timestamp,
            message="Update PEP 1 and add PEP 2",
            files=files,
        )
        assert commit.hash == "abc123"
        assert commit.timestamp == timestamp
        assert commit.message == "Update PEP 1 and add PEP 2"
        assert len(commit.files) == 2

    def test_commit_record_empty_files(self) -> None:
        """Test CommitRecord can have empty file list."""
        commit = CommitRecord(
            hash="abc123",
            timestamp=datetime(2024, 1, 15, 10, 30),
            message="Update documentation",
            files=[],
        )
        assert commit.message == "Update documentation"
        assert len(commit.files) == 0

    def test_commit_record_immutable(self) -> None:
        """Test CommitRecord is immutable."""
        commit = CommitRecord(
            hash="abc123",
            timestamp=datetime(2024, 1, 15, 10, 30),
            message="Test commit",
            files=[],
        )
        try:
            commit.hash = "def456"  # type: ignore
            raise AssertionError("Should not allow mutation")
        except AttributeError:
            pass

    def test_commit_record_with_message(self) -> None:
        """Test CommitRecord includes commit message."""
        commit = CommitRecord(
            hash="abc123",
            timestamp=datetime(2024, 1, 15, 10, 30),
            message="Add initial draft of PEP 815",
            files=[ChangedFile(path="pep-0815.rst", change_type="A")],
        )
        assert commit.message == "Add initial draft of PEP 815"

    def test_commit_record_message_required(self) -> None:
        """Test CommitRecord requires message field."""
        # This test documents that message is a required field
        timestamp = datetime(2024, 1, 15, 10, 30)
        files = [ChangedFile(path="pep-0001.rst", change_type="M")]
        commit = CommitRecord(
            hash="abc123",
            timestamp=timestamp,
            message="Fix typo in PEP 1",
            files=files,
        )
        assert commit.message == "Fix typo in PEP 1"


class TestPepActivity:
    """Test PepActivity data model."""

    def test_create_pep_activity(self) -> None:
        """Create a PepActivity with valid data."""
        activity = PepActivity(
            pep_number=815,
            commit_count=3,
            files=["pep-0815.rst", "pep-0815.md"],
        )
        assert activity.pep_number == 815
        assert activity.commit_count == 3
        assert len(activity.files) == 2

    def test_pep_activity_single_file(self) -> None:
        """Test PepActivity with single file."""
        activity = PepActivity(
            pep_number=1,
            commit_count=1,
            files=["pep-0001.rst"],
        )
        assert activity.pep_number == 1
        assert len(activity.files) == 1

    def test_pep_activity_immutable(self) -> None:
        """Test PepActivity is immutable."""
        activity = PepActivity(
            pep_number=815,
            commit_count=3,
            files=["pep-0815.rst"],
        )
        try:
            activity.pep_number = 816  # type: ignore
            raise AssertionError("Should not allow mutation")
        except AttributeError:
            pass

    def test_pep_activity_with_metadata(self) -> None:
        """Create PepActivity with full metadata."""
        activity = PepActivity(
            pep_number=815,
            commit_count=3,
            files=["pep-0815.rst"],
            title="Disallow reference cycles in tp_traverse",
            status="Draft",
            abstract="This PEP proposes disallowing reference cycles...",
            authors=["Sam Gross <colesbury@gmail.com>"],
            pep_type="Standards Track",
            created="11-Jan-2024",
        )
        assert activity.pep_number == 815
        assert activity.title == "Disallow reference cycles in tp_traverse"
        assert activity.status == "Draft"
        assert activity.abstract is not None
        assert "reference cycles" in activity.abstract
        assert len(activity.authors) == 1
        assert activity.pep_type == "Standards Track"
        assert activity.created == "11-Jan-2024"

    def test_pep_activity_with_partial_metadata(self) -> None:
        """Create PepActivity with some metadata fields None."""
        activity = PepActivity(
            pep_number=1,
            commit_count=1,
            files=["pep-0001.rst"],
            title="PEP Purpose and Guidelines",
            status="Active",
            # abstract, authors, pep_type, created all None/empty by default
        )
        assert activity.title == "PEP Purpose and Guidelines"
        assert activity.status == "Active"
        assert activity.abstract is None
        assert activity.authors == []
        assert activity.pep_type is None
        assert activity.created is None

    def test_pep_activity_backward_compatibility(self) -> None:
        """Test PepActivity works without metadata fields (backward compatible)."""
        activity = PepActivity(
            pep_number=815,
            commit_count=3,
            files=["pep-0815.rst"],
        )
        # All metadata fields should have sensible defaults
        assert activity.pep_number == 815
        assert activity.title is None
        assert activity.status is None
        assert activity.abstract is None
        assert activity.authors == []
        assert activity.pep_type is None
        assert activity.created is None

    def test_pep_activity_with_multiple_authors(self) -> None:
        """Create PepActivity with multiple authors."""
        activity = PepActivity(
            pep_number=8,
            commit_count=10,
            files=["pep-0008.rst"],
            title="Style Guide for Python Code",
            status="Active",
            authors=[
                "Guido van Rossum <guido@python.org>",
                "Barry Warsaw <barry@python.org>",
            ],
        )
        assert len(activity.authors) == 2
        assert "Guido van Rossum" in activity.authors[0]
        assert "Barry Warsaw" in activity.authors[1]

    def test_pep_activity_with_commit_messages(self) -> None:
        """Create PepActivity with commit messages."""
        activity = PepActivity(
            pep_number=815,
            commit_count=3,
            files=["pep-0815.rst"],
            commit_messages=[
                "Add initial draft of PEP 815",
                "Clarify tp_traverse requirements",
                "Fix typos in abstract",
            ],
        )
        assert len(activity.commit_messages) == 3
        assert activity.commit_messages[0] == "Add initial draft of PEP 815"
        assert activity.commit_messages[1] == "Clarify tp_traverse requirements"
        assert activity.commit_messages[2] == "Fix typos in abstract"

    def test_pep_activity_commit_messages_default_empty(self) -> None:
        """Test PepActivity commit_messages defaults to empty list."""
        activity = PepActivity(
            pep_number=1,
            commit_count=1,
            files=["pep-0001.rst"],
        )
        assert activity.commit_messages == []

    def test_pep_activity_single_commit_message(self) -> None:
        """Test PepActivity with single commit message."""
        activity = PepActivity(
            pep_number=729,
            commit_count=1,
            files=["pep-0729.rst"],
            commit_messages=["Initial draft of PEP 729"],
        )
        assert len(activity.commit_messages) == 1
        assert activity.commit_messages[0] == "Initial draft of PEP 729"


class TestPepSignal:
    """Test PepSignal data model."""

    def test_create_pep_signal(self) -> None:
        """Create a PepSignal with valid data."""
        signal = PepSignal(
            pep_number=815,
            signal_type="status_change",
            description="Status changed from Draft to Accepted",
        )
        assert signal.pep_number == 815
        assert signal.signal_type == "status_change"
        assert "Draft to Accepted" in signal.description

    def test_pep_signal_immutable(self) -> None:
        """Test PepSignal is immutable."""
        signal = PepSignal(
            pep_number=815,
            signal_type="status_change",
            description="Status changed",
        )
        try:
            signal.pep_number = 816  # type: ignore
            raise AssertionError("Should not allow mutation")
        except AttributeError:
            pass

    def test_pep_signal_repr(self) -> None:
        """Test PepSignal has useful string representation."""
        signal = PepSignal(
            pep_number=815,
            signal_type="status_change",
            description="Status changed",
        )
        repr_str = repr(signal)
        assert "815" in repr_str
        assert "status_change" in repr_str

    def test_pep_signal_with_signal_value(self) -> None:
        """Create PepSignal with signal_value."""
        signal = PepSignal(
            pep_number=821,
            signal_type="status_transition",
            description="Status changed: Draft → Accepted",
            signal_value=100,
        )
        assert signal.pep_number == 821
        assert signal.signal_type == "status_transition"
        assert signal.signal_value == 100

    def test_pep_signal_default_signal_value(self) -> None:
        """Test PepSignal defaults to signal_value=0."""
        signal = PepSignal(
            pep_number=815,
            signal_type="informational",
            description="Some informational signal",
        )
        assert signal.signal_value == 0

    def test_pep_signal_medium_value(self) -> None:
        """Create PepSignal with medium signal_value (50)."""
        signal = PepSignal(
            pep_number=815,
            signal_type="normative_language",
            description="Contains RFC 2119 keywords",
            signal_value=50,
        )
        assert signal.signal_value == 50

    def test_pep_signal_low_value(self) -> None:
        """Create PepSignal with low signal_value (10)."""
        signal = PepSignal(
            pep_number=1,
            signal_type="legacy_cleanup",
            description="Minor formatting changes",
            signal_value=10,
        )
        assert signal.signal_value == 10
