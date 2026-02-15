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
            files=files,
        )
        assert commit.hash == "abc123"
        assert commit.timestamp == timestamp
        assert len(commit.files) == 2

    def test_commit_record_empty_files(self) -> None:
        """Test CommitRecord can have empty file list."""
        commit = CommitRecord(
            hash="abc123",
            timestamp=datetime(2024, 1, 15, 10, 30),
            files=[],
        )
        assert len(commit.files) == 0

    def test_commit_record_immutable(self) -> None:
        """Test CommitRecord is immutable."""
        commit = CommitRecord(
            hash="abc123",
            timestamp=datetime(2024, 1, 15, 10, 30),
            files=[],
        )
        try:
            commit.hash = "def456"  # type: ignore
            raise AssertionError("Should not allow mutation")
        except AttributeError:
            pass


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
