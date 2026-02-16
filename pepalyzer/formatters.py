"""Output formatters for pepalyzer results."""

import json

from pepalyzer.models import PepActivity, PepSignal


def _format_activity_header(activity: PepActivity) -> str:
    """Format the header line for a PEP activity.

    Args:
        activity: The PEP activity to format.

    Returns:
        Formatted header string.
    """
    header = f"PEP {activity.pep_number}"
    if activity.title:
        header += f" — {activity.title}"
    if activity.status:
        header += f" ({activity.status})"
    commit_word = "commit" if activity.commit_count == 1 else "commits"
    header += f" [{activity.commit_count} {commit_word}]"
    return header


def _format_activity_signals(
    pep_signals: list[PepSignal],
) -> list[str]:
    """Format signals for display.

    Args:
        pep_signals: List of signals for this PEP.

    Returns:
        List of formatted signal lines.
    """
    if not pep_signals:
        return []

    # Sort by value (high to low) for display
    sorted_signals = sorted(pep_signals, key=lambda s: (-s.signal_value, s.signal_type))

    lines = ["  Signals:"]
    for signal in sorted_signals:
        # Mark high-value signals (100) with ⭐
        marker = " ⭐" if signal.signal_value == 100 else ""
        lines.append(f"    - [{signal.signal_value}] {signal.description}{marker}")

    return lines


def _format_single_activity_text(
    activity: PepActivity, signals_by_pep: dict[int, list[PepSignal]]
) -> list[str]:
    """Format a single PEP activity into a list of output lines."""
    lines = [_format_activity_header(activity)]

    # Link
    lines.append(f"  https://peps.python.org/pep-{activity.pep_number:04d}/")

    # Abstract
    if activity.abstract:
        abstract_lines = activity.abstract.split("\n")
        if len(abstract_lines) > 8:
            display_lines = abstract_lines[:8]
            display_lines.append("...")
        else:
            display_lines = abstract_lines

        if display_lines:
            lines.append(f"  Abstract: {display_lines[0]}")
            for line in display_lines[1:]:
                lines.append(f"            {line}")

    # Files
    if activity.files:
        files_str = ", ".join(activity.files)
        lines.append(f"  Files: {files_str}")

    # Commit messages (chronological order)
    if activity.commit_messages:
        lines.append("  Commits:")
        for message in activity.commit_messages:
            lines.append(f"    - {message}")

    # Signals (sorted by signal_value descending, then by type)
    pep_signals = signals_by_pep.get(activity.pep_number, [])
    lines.extend(_format_activity_signals(pep_signals))

    # Blank line for separation
    lines.append("")

    return lines


def format_as_text(activities: list[PepActivity], signals: list[PepSignal]) -> str:
    """Format results as human-readable text with metadata.

    Args:
        activities: List of PEP activities (sorted by PEP number).
        signals: List of detected signals.

    Returns:
        Formatted text string with title, status, abstract, and signals.

    Examples:
        >>> activities = [PepActivity(815, 3, ["pep-0815.rst"], title="Test")]
        >>> signals = [PepSignal(815, "status_final", "Status: Final", 100)]
        >>> text = format_as_text(activities, signals)
        >>> "PEP 815" in text
        True
    """
    if not activities:
        return "No PEP changes found in the specified time period.\n"

    # Group signals by PEP number
    signals_by_pep: dict[int, list[PepSignal]] = {}
    for signal in signals:
        if signal.pep_number not in signals_by_pep:
            signals_by_pep[signal.pep_number] = []
        signals_by_pep[signal.pep_number].append(signal)

    all_lines: list[str] = []
    for activity in activities:
        all_lines.extend(_format_single_activity_text(activity, signals_by_pep))

    return "\n".join(all_lines)


def format_as_json(activities: list[PepActivity], signals: list[PepSignal]) -> str:
    """Format results as JSON with full metadata.

    Args:
        activities: List of PEP activities.
        signals: List of detected signals.

    Returns:
        Pretty-printed JSON string with all metadata and signal values.

    Examples:
        >>> activities = [PepActivity(815, 3, ["pep-0815.rst"], title="Test")]
        >>> signals = []
        >>> json_str = format_as_json(activities, signals)
        >>> "815" in json_str
        True
    """
    # Group signals by PEP number
    signals_by_pep: dict[int, list[PepSignal]] = {}
    for signal in signals:
        if signal.pep_number not in signals_by_pep:
            signals_by_pep[signal.pep_number] = []
        signals_by_pep[signal.pep_number].append(signal)

    result = []
    for activity in activities:
        pep_signals = signals_by_pep.get(activity.pep_number, [])
        # Sort signals by value (descending) for display
        sorted_signals = sorted(
            pep_signals, key=lambda s: (-s.signal_value, s.signal_type)
        )

        pep_data = {
            "pep_number": activity.pep_number,
            # Required metadata fields
            "title": activity.title,
            "status": activity.status,
            "abstract": activity.abstract,
            # Optional metadata fields
            "authors": activity.authors,
            "pep_type": activity.pep_type,
            "created": activity.created,
            # Auxiliary fields
            "commit_count": activity.commit_count,
            "commit_messages": activity.commit_messages,
            "files": activity.files,
            # Signals with signal_value
            "signals": [
                {
                    "type": signal.signal_type,
                    "description": signal.description,
                    "signal_value": signal.signal_value,
                }
                for signal in sorted_signals
            ],
        }
        result.append(pep_data)

    return json.dumps(result, indent=2)
