"""Data models for pepalyzer.

This module defines the core data structures used throughout pepalyzer.
All models are immutable (frozen dataclasses) to ensure data integrity.
"""

from dataclasses import dataclass
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
        files: List of files changed in this commit.
    """

    hash: str
    timestamp: datetime
    files: list[ChangedFile]


@dataclass(frozen=True)
class PepActivity:
    """Aggregates activity for a single PEP across multiple commits.

    Attributes:
        pep_number: PEP number (e.g., 815).
        commit_count: Number of commits touching this PEP.
        files: List of unique file paths associated with this PEP.
    """

    pep_number: int
    commit_count: int
    files: list[str]


@dataclass(frozen=True)
class PepSignal:
    """Represents a detected editorial signal for a PEP.

    Signals are descriptive flags that indicate potentially interesting
    changes, not judgments about importance.

    Attributes:
        pep_number: PEP number this signal relates to.
        signal_type: Type of signal (e.g., "status_change", "deprecation").
        description: Human-readable description of the signal.
    """

    pep_number: int
    signal_type: str
    description: str
