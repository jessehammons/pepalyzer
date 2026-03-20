"""Signal detection for identifying notable changes in PEPs."""

import re

from pepalyzer.models import PepSignal


def detect_signals(content: str, pep_number: int) -> list[PepSignal]:
    """Detect editorial signals in PEP content.

    Uses lightweight, rule-based heuristics to identify potentially
    interesting changes. Does not perform semantic interpretation.

    Supported signal types:
    - status_accepted: Status changed to Accepted
    - status_final: Status changed to Final
    - status_withdrawn: Status changed to Withdrawn
    - deprecation: Deprecation or removal language
    - normative_language: RFC 2119 keywords (MUST, SHOULD, etc.)

    Args:
        content: Text content to analyze.
        pep_number: PEP number for this content.

    Returns:
        List of detected signals (may be empty).

    Examples:
        >>> content = "Status: Accepted"
        >>> signals = detect_signals(content, pep_number=815)
        >>> signals[0].signal_type
        'status_accepted'
    """
    signals: list[PepSignal] = []

    # NOTE: Status transition detection is now IMPLEMENTED via diff-based detection.
    # See detect_status_transition() below and aggregate_by_pep_with_signals() in
    # aggregator.py. The old status presence detection was removed because it
    # detected current state rather than transitions (the "PEP 512 problem" - showing
    # "Status: Final ⭐" for PEPs already Final when commits just fixed typos).
    #
    # The new implementation parses git diffs to find actual status changes:
    # "-Status: Draft" → "+Status: Final" (signal_value=100: high-value lifecycle event)

    # Detect deprecation language (signal_value=50: medium-value content signal)
    deprecation_patterns = [
        r"\bdeprecated\b",
        r"\bremoved\b",
        r"\bno longer\b",
    ]

    for pattern in deprecation_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            signals.append(
                PepSignal(
                    pep_number=pep_number,
                    signal_type="deprecation",
                    description="Contains deprecation or removal language",
                    signal_value=50,  # Medium-value: content-based signal
                )
            )
            break  # Only add one deprecation signal

    # Detect normative language (RFC 2119) (signal_value=50: medium-value)
    normative_patterns = [
        r"\bMUST\b",
        r"\bMUST NOT\b",
        r"\bSHOULD\b",
        r"\bSHOULD NOT\b",
        r"\bREQUIRED\b",
        r"\bSHALL\b",
        r"\bSHALL NOT\b",
    ]

    for pattern in normative_patterns:
        if re.search(pattern, content):
            signals.append(
                PepSignal(
                    pep_number=pep_number,
                    signal_type="normative_language",
                    description="Contains normative language (RFC 2119 keywords)",
                    signal_value=50,  # Medium-value: content-based signal
                )
            )
            break  # Only add one normative language signal

    return signals


def detect_status_transition(diff_text: str, pep_number: int) -> list[PepSignal]:
    r"""Detect status field changes in git diff.

    Parses unified diff format to find lines like:
        -Status: Draft
        +Status: Final

    Args:
        diff_text: Unified diff text from git
        pep_number: PEP number for the signal

    Returns:
        List containing one PepSignal if status changed, empty list otherwise

    Examples:
        >>> diff = "-Status: Draft\n+Status: Final"
        >>> signals = detect_status_transition(diff, 815)
        >>> signals[0].description
        'Status: Draft → Final'
    """
    old_status = None
    new_status = None

    for line in diff_text.split("\n"):
        # Look for removed status line
        if line.startswith("-Status:"):
            if old_status is None:  # Only capture first
                old_status = line.split(":", 1)[1].strip()
        # Look for added status line
        elif line.startswith("+Status:"):
            if new_status is None:  # Only capture first
                new_status = line.split(":", 1)[1].strip()

    # Only create signal if both exist and are different
    if old_status and new_status and old_status != new_status:
        return [
            PepSignal(
                pep_number=pep_number,
                signal_type="status_transition",
                description=f"Status: {old_status} → {new_status}",
                signal_value=100,
            )
        ]

    return []
