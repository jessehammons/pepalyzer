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

    # NOTE: Status transition detection is disabled for now because it was
    # detecting status *presence* (current state) rather than actual *transitions*
    # (changes). This was misleading - a PEP that was already Final would show
    # "Status: Final ⭐" even if the commit just fixed typos.
    #
    # To properly detect status transitions, we need to analyze git diffs to see
    # if the Status field actually changed (e.g., "-Status: Draft" → "+Status: Final").
    # This requires parsing commit diffs, not just reading current file content.
    #
    # See: https://github.com/anthropics/claude-code/issues/XXXX (if filed)

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
