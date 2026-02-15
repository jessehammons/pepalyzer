"""Aggregate commit changes into PEP-centric activity summaries."""

from collections import defaultdict

from pepalyzer.models import CommitRecord, PepActivity
from pepalyzer.pep_parser import extract_pep_number


def aggregate_by_pep(commits: list[CommitRecord]) -> list[PepActivity]:
    """Aggregate commits into PEP-centric activity summaries.

    Groups all changes by PEP number, counting commits and tracking
    unique files. Non-PEP files are filtered out.

    Args:
        commits: List of commit records to aggregate.

    Returns:
        List of PepActivity objects, sorted by commit count (descending).

    Examples:
        >>> from datetime import datetime
        >>> from pepalyzer.models import CommitRecord, ChangedFile
        >>> commits = [
        ...     CommitRecord(
        ...         hash="abc",
        ...         timestamp=datetime(2024, 1, 15),
        ...         files=[ChangedFile(path="pep-0001.rst", change_type="M")]
        ...     )
        ... ]
        >>> activities = aggregate_by_pep(commits)
        >>> activities[0].pep_number
        1
    """
    # Track commits and files per PEP
    pep_commits: dict[int, int] = defaultdict(int)
    pep_files: dict[int, set[str]] = defaultdict(set)

    for commit in commits:
        for changed_file in commit.files:
            pep_number = extract_pep_number(changed_file.path)
            if pep_number is not None:
                pep_commits[pep_number] += 1
                pep_files[pep_number].add(changed_file.path)

    # Convert to PepActivity objects
    activities = [
        PepActivity(
            pep_number=pep_num,
            commit_count=pep_commits[pep_num],
            files=sorted(pep_files[pep_num]),  # Sort for deterministic output
        )
        for pep_num in pep_commits
    ]

    # Sort by commit count (descending), then by PEP number (ascending)
    activities.sort(key=lambda a: (-a.commit_count, a.pep_number))

    return activities
