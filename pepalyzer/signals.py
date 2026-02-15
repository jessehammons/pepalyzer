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

    # Detect status changes (signal_value=100: high-value editorial moments)
    status_patterns = [
        (r"status:\s*accepted", "status_accepted", "Status: Accepted"),
        (r"status:\s*final", "status_final", "Status: Final"),
        (r"status:\s*withdrawn", "status_withdrawn", "Status: Withdrawn"),
    ]

    for pattern, signal_type, description in status_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            signals.append(
                PepSignal(
                    pep_number=pep_number,
                    signal_type=signal_type,
                    description=description,
                    signal_value=100,  # High-value: status transitions
                )
            )

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
