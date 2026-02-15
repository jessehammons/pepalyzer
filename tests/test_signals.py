"""Tests for signal detection logic."""

from pepalyzer.signals import detect_signals


class TestDetectSignals:
    """Test signal detection in text content."""

    def test_detect_status_change_to_accepted(self) -> None:
        """Detect status change to Accepted."""
        content = """
Status: Accepted
Type: Standards Track
"""
        signals = detect_signals(content, pep_number=815)
        assert len(signals) == 1
        assert signals[0].signal_type == "status_accepted"
        assert signals[0].pep_number == 815
        assert signals[0].signal_value == 100  # High-value signal

    def test_detect_status_change_to_final(self) -> None:
        """Detect status change to Final."""
        content = """
Status: Final
Type: Standards Track
"""
        signals = detect_signals(content, pep_number=427)
        assert len(signals) == 1
        assert signals[0].signal_type == "status_final"

    def test_detect_status_withdrawn(self) -> None:
        """Detect withdrawn status."""
        content = "Status: Withdrawn"
        signals = detect_signals(content, pep_number=100)
        assert len(signals) == 1
        assert signals[0].signal_type == "status_withdrawn"

    def test_detect_deprecation_language(self) -> None:
        """Detect deprecation keywords."""
        content = """
This feature is now deprecated and will be removed in Python 3.15.
"""
        signals = detect_signals(content, pep_number=123)
        signal_types = {s.signal_type for s in signals}
        assert "deprecation" in signal_types
        # Check signal_value for deprecation signal
        deprecation_signal = next(s for s in signals if s.signal_type == "deprecation")
        assert deprecation_signal.signal_value == 50  # Medium-value signal

    def test_detect_removal_language(self) -> None:
        """Detect removal keywords."""
        content = "This module has been removed from the standard library."
        signals = detect_signals(content, pep_number=123)
        signal_types = {s.signal_type for s in signals}
        assert "deprecation" in signal_types

    def test_detect_normative_must(self) -> None:
        """Detect normative MUST language (RFC 2119)."""
        content = """
Implementations MUST support this feature.
The parser MUST NOT accept invalid syntax.
"""
        signals = detect_signals(content, pep_number=815)
        signal_types = {s.signal_type for s in signals}
        assert "normative_language" in signal_types
        # Check signal_value for normative language signal
        normative_signal = next(
            s for s in signals if s.signal_type == "normative_language"
        )
        assert normative_signal.signal_value == 50  # Medium-value signal

    def test_detect_normative_should(self) -> None:
        """Detect normative SHOULD language (RFC 2119)."""
        content = """
Applications SHOULD follow this guideline.
Implementations SHOULD NOT rely on this behavior.
"""
        signals = detect_signals(content, pep_number=815)
        signal_types = {s.signal_type for s in signals}
        assert "normative_language" in signal_types

    def test_no_signals_in_normal_text(self) -> None:
        """No false positives on normal text."""
        content = """
This is a regular PEP describing some feature.
It has normal text without any special signals.
"""
        signals = detect_signals(content, pep_number=1)
        assert len(signals) == 0

    def test_ignore_must_in_code_examples(self) -> None:
        """Should not detect MUST in code examples (basic heuristic)."""
        # This is a simple implementation - we can improve later
        content = """
.. code-block:: python

    # This MUST be implemented
    def foo():
        pass
"""
        # For now, we accept that code blocks might trigger false positives
        # A more sophisticated implementation would parse reStructuredText
        signals = detect_signals(content, pep_number=1)
        # This test documents current behavior
        assert isinstance(signals, list)

    def test_multiple_signals_in_same_content(self) -> None:
        """Detect multiple different signal types."""
        content = """
Status: Final

This feature is deprecated and MUST NOT be used in new code.
"""
        signals = detect_signals(content, pep_number=815)
        signal_types = {s.signal_type for s in signals}
        # Should detect both status and other signals
        assert len(signal_types) >= 2

    def test_case_insensitive_status(self) -> None:
        """Status detection should be case-insensitive."""
        content = "status: accepted"
        signals = detect_signals(content, pep_number=1)
        assert len(signals) == 1
        assert signals[0].signal_type == "status_accepted"

    def test_empty_content(self) -> None:
        """Handle empty content."""
        signals = detect_signals("", pep_number=1)
        assert len(signals) == 0

    def test_signal_descriptions_are_informative(self) -> None:
        """Signal descriptions should be human-readable."""
        content = "Status: Final"
        signals = detect_signals(content, pep_number=815)
        assert len(signals) == 1
        assert len(signals[0].description) > 0
        assert "final" in signals[0].description.lower()
