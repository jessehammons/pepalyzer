"""Output formatters for pepalyzer results."""

import json

from pepalyzer.models import PepActivity, PepSignal


def format_as_text(activities: list[PepActivity], signals: list[PepSignal]) -> str:
    """Format results as human-readable text.

    Args:
        activities: List of PEP activities (should be sorted by commit count).
        signals: List of detected signals.

    Returns:
        Formatted text string.

    Examples:
        >>> activities = [PepActivity(815, 3, ["pep-0815.rst"])]
        >>> signals = [PepSignal(815, "status_final", "Status: Final")]
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

    lines: list[str] = []

    for activity in activities:
        # PEP header
        commit_word = "commit" if activity.commit_count == 1 else "commits"
        lines.append(
            f"PEP {activity.pep_number} ({activity.commit_count} {commit_word})"
        )

        # Signals for this PEP
        pep_signals = signals_by_pep.get(activity.pep_number, [])
        for signal in pep_signals:
            lines.append(f"  {signal.description}")

        # Blank line between PEPs
        lines.append("")

    return "\n".join(lines)


def format_as_json(activities: list[PepActivity], signals: list[PepSignal]) -> str:
    """Format results as JSON.

    Args:
        activities: List of PEP activities.
        signals: List of detected signals.

    Returns:
        Pretty-printed JSON string.

    Examples:
        >>> activities = [PepActivity(815, 3, ["pep-0815.rst"])]
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

        pep_data = {
            "pep_number": activity.pep_number,
            "commit_count": activity.commit_count,
            "files": activity.files,
            "signals": [
                {
                    "type": signal.signal_type,
                    "description": signal.description,
                }
                for signal in pep_signals
            ],
        }
        result.append(pep_data)

    return json.dumps(result, indent=2)
