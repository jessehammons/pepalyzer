"""Aggregate commit changes into PEP-centric activity summaries."""

from collections import defaultdict

from pepalyzer.models import CommitRecord, PepActivity
from pepalyzer.pep_metadata import extract_pep_metadata, PepMetadata, read_pep_file
from pepalyzer.pep_parser import extract_pep_number


def aggregate_by_pep(
    commits: list[CommitRecord], repo_path: str | None = None
) -> list[PepActivity]:
    """Aggregate commits into PEP-centric activity summaries.

    Groups all changes by PEP number, counting commits and tracking
    unique files. Non-PEP files are filtered out.

    If repo_path is provided, extracts metadata (title, status, abstract, etc.)
    from the current version of each PEP file.

    Args:
        commits: List of commit records to aggregate.
        repo_path: Optional path to repository root for metadata extraction.

    Returns:
        List of PepActivity objects, sorted by PEP number (ascending).

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
    # Track commits, files, and messages per PEP
    pep_commits: dict[int, int] = defaultdict(int)
    pep_files: dict[int, set[str]] = defaultdict(set)
    pep_messages: dict[int, list[str]] = defaultdict(list)

    for commit in commits:
        pep_numbers_in_commit = set()
        # First pass: identify which PEPs this commit touches
        for changed_file in commit.files:
            pep_number = extract_pep_number(changed_file.path)
            if pep_number is not None:
                pep_numbers_in_commit.add(pep_number)
                pep_files[pep_number].add(changed_file.path)

        # Second pass: increment count and add message for each PEP
        for pep_number in pep_numbers_in_commit:
            pep_commits[pep_number] += 1
            pep_messages[pep_number].append(commit.message)

    # Convert to PepActivity objects with metadata
    activities = []
    for pep_num in pep_commits:
        files = sorted(pep_files[pep_num])

        # Extract metadata if repo_path provided
        metadata = None
        if repo_path:
            metadata = _extract_metadata_for_pep(repo_path, files)

        activity = PepActivity(
            pep_number=pep_num,
            commit_count=pep_commits[pep_num],
            files=files,
            # Populate metadata fields (None if not extracted)
            title=metadata.title if metadata else None,
            status=metadata.status if metadata else None,
            abstract=metadata.abstract if metadata else None,
            authors=metadata.authors if metadata else [],
            pep_type=metadata.pep_type if metadata else None,
            created=metadata.created if metadata else None,
            # Populate commit messages (chronological order)
            commit_messages=pep_messages[pep_num],
        )
        activities.append(activity)

    # Sort by PEP number (ascending) for consistent output
    activities.sort(key=lambda a: a.pep_number)

    return activities


def _extract_metadata_for_pep(repo_path: str, files: list[str]) -> PepMetadata | None:
    """Extract metadata for a PEP by reading its main document.

    Prioritizes .rst and .md files (main PEP documents) over supplementary
    files like examples or diagrams.

    Args:
        repo_path: Path to repository root.
        files: List of file paths associated with this PEP.

    Returns:
        PepMetadata object, or None if no main PEP document could be read.
    """
    # Priority 1: Try .rst files first (traditional PEP format)
    for file_path in files:
        if file_path.endswith(".rst"):
            content = read_pep_file(repo_path, file_path)
            if content:
                return extract_pep_metadata(content)

    # Priority 2: Try .md files (newer PEP format)
    for file_path in files:
        if file_path.endswith(".md"):
            content = read_pep_file(repo_path, file_path)
            if content:
                return extract_pep_metadata(content)

    # Priority 3: Try .txt files (legacy format, if any)
    for file_path in files:
        if file_path.endswith(".txt"):
            content = read_pep_file(repo_path, file_path)
            if content:
                return extract_pep_metadata(content)

    # No main PEP document found
    return None
