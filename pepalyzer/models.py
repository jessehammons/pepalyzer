"""Data models for pepalyzer.

This module defines the core data structures used throughout pepalyzer.
All models are immutable (frozen dataclasses) to ensure data integrity.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ChangedFile:
    """Represents a file changed in a Git commit.

    Attributes:
        path: File path relative to repository root.
        change_type: Type of change (A=added, M=modified, D=deleted).
    """

    path: str
    change_type: str


@dataclass(frozen=True)
class CommitRecord:
    """Represents a single Git commit.

    Attributes:
        hash: Git commit hash (short or full).
        timestamp: Commit timestamp.
        message: Commit message (explains why changes were made).
        files: List of files changed in this commit.
    """

    hash: str
    timestamp: datetime
    message: str
    files: list[ChangedFile]


@dataclass(frozen=True)
class PepActivity:
    """Represents a single PEP that changed within the analysis window.

    This is a one-row-per-PEP structure combining current metadata with
    change summary. Multiple commits to the same PEP are de-duplicated.

    Core fields:
        pep_number: PEP number (e.g., 815) - primary identity.
        commit_count: Number of commits touching this PEP (auxiliary).
        files: List of unique file paths associated with this PEP.

    Metadata fields (extracted from current PEP file):
        title: Human-readable PEP title (required for useful output).
        status: Current status (Draft, Accepted, Final, etc.).
        abstract: First paragraph or abstract section (required for context).
        authors: List of author names/emails.
        pep_type: Type of PEP (Standards Track, Informational, Process).
        created: PEP creation date (kept as string).

    Provenance fields:
        commit_messages: List of commit messages explaining changes (chronological).
    """

    pep_number: int
    commit_count: int
    files: list[str]
    # Metadata fields (optional, extracted from PEP file)
    title: str | None = None
    status: str | None = None
    abstract: str | None = None
    authors: list[str] = field(default_factory=list)
    pep_type: str | None = None
    created: str | None = None
    # Provenance fields
    commit_messages: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PepSignal:
    """Represents a detected editorial signal for a PEP.

    Signals are descriptive flags that indicate potentially interesting
    changes, not judgments about importance.

    Attributes:
        pep_number: PEP number this signal relates to.
        signal_type: Type of signal (e.g., "status_transition", "deprecation").
        description: Human-readable description of the signal.
        signal_value: Integer indicating relative editorial significance (0-100).
            100 = Status transitions (major editorial moments)
            50 = Content-based signals (normative language, deprecation)
            10 = Minor signals (legacy cleanup, formatting)
            0 = Informational only
    """

    pep_number: int
    signal_type: str
    description: str
    signal_value: int = 0
