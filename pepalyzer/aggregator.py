"""Aggregate commit changes into PEP-centric activity summaries."""

from collections import defaultdict
from pathlib import Path

from pepalyzer.git_adapter import get_commit_diff
from pepalyzer.models import CommitRecord, PepActivity, PepSignal
from pepalyzer.pep_metadata import extract_pep_metadata, PepMetadata, read_pep_file
from pepalyzer.pep_parser import extract_pep_number
from pepalyzer.signals import detect_signals, detect_status_transition


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


def aggregate_by_pep_with_signals(  # noqa: C901
    commits: list[CommitRecord],
    repo_path: str | None = None,
) -> tuple[list[PepActivity], list[PepSignal]]:
    """Aggregate commits by PEP and detect signals.

    Combines PEP aggregation with both content-based and diff-based
    signal detection.

    Args:
        commits: List of commit records to aggregate
        repo_path: Path to git repository (required for signal detection)

    Returns:
        Tuple of (activities, signals)

    Example:
        >>> commits = get_recent_commits("/path/to/peps", since="30d")
        >>> activities, signals = aggregate_by_pep_with_signals(commits, "/path/to/peps")
    """
    # Step 1: Standard aggregation
    activities = aggregate_by_pep(commits, repo_path)

    all_signals: list[PepSignal] = []

    if not repo_path:
        return activities, all_signals

    # Step 2: Content-based signals (existing deprecation/normative detection)
    # NOTE: For content-based signals, we only read one file per PEP since
    # we're detecting patterns in the *current state* (not diffs). The PEP's
    # main document contains all signals. Matches existing pattern in cli.py:118.
    for activity in activities:
        pep_files = sorted(activity.files)
        for file_path in pep_files:
            full_path = Path(repo_path) / file_path
            try:
                content = full_path.read_text(encoding="utf-8")
                signals = detect_signals(content, activity.pep_number)
                all_signals.extend(signals)
                break  # Only process first readable file per PEP
            except IOError:
                continue

    # Step 3: Diff-based signals (NEW - status transitions)
    # Track which commits touched which PEPs
    pep_commits: dict[int, list[CommitRecord]] = defaultdict(list)

    for commit in commits:
        for changed_file in commit.files:
            pep_number = extract_pep_number(changed_file.path)
            if pep_number is not None:
                pep_commits[pep_number].append(commit)

    # For each PEP, analyze diffs for status transitions
    for pep_number, pep_commit_list in pep_commits.items():
        seen_hashes = set()
        for commit in pep_commit_list:
            if commit.hash in seen_hashes:
                continue
            seen_hashes.add(commit.hash)

            # Get files for this PEP in this commit
            pep_files_in_commit = [
                cf.path
                for cf in commit.files
                if extract_pep_number(cf.path) == pep_number
            ]

            # Check diff for each file (unlike content-based signals above,
            # we process ALL files here because status could change in any file)
            for file_path in pep_files_in_commit:
                diff_text = get_commit_diff(repo_path, commit.hash, file_path)
                if diff_text:
                    transition_signals = detect_status_transition(diff_text, pep_number)
                    all_signals.extend(transition_signals)

    return activities, all_signals
