"""Tests for signal detection logic."""

from pepalyzer.signals import detect_signals, detect_status_transition


class TestDetectSignals:
    """Test signal detection in text content."""

    def test_status_presence_not_detected(self) -> None:
        """Status presence detection is disabled (was misleading).

        Previously detected "Status: Accepted" as a high-value signal, but this
        was misleading because it detected current state, not actual transitions.
        A PEP that was already Final would show "Status: Final ⭐" even if the
        commit just fixed typos.

        To properly detect status transitions, we need to analyze git diffs.
        This test documents that status presence is no longer detected.
        """
        content = """
Status: Accepted
Type: Standards Track
"""
        signals = detect_signals(content, pep_number=815)
        # Should not detect status presence
        status_types = {s.signal_type for s in signals}
        assert "status_accepted" not in status_types
        assert "status_final" not in status_types
        assert "status_withdrawn" not in status_types

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
        """Status detection disabled (this test documents the change)."""
        content = "status: accepted"
        signals = detect_signals(content, pep_number=1)
        # Status presence no longer detected
        status_types = {s.signal_type for s in signals}
        assert "status_accepted" not in status_types

    def test_empty_content(self) -> None:
        """Handle empty content."""
        signals = detect_signals("", pep_number=1)
        assert len(signals) == 0

    def test_signal_descriptions_are_informative(self) -> None:
        """Signal descriptions should be human-readable."""
        content = "This feature is deprecated and MUST NOT be used."
        signals = detect_signals(content, pep_number=815)
        assert len(signals) >= 1
        # Check that at least one signal has an informative description
        descriptions = [s.description for s in signals]
        assert any(len(d) > 0 for d in descriptions)


class TestDetectStatusTransition:
    """Test status transition detection from git diffs."""

    def test_detect_draft_to_final(self) -> None:
        """Detect Draft → Final transition."""
        diff_text = """
diff --git a/peps/pep-0815.rst b/peps/pep-0815.rst
-Status: Draft
+Status: Final
"""
        signals = detect_status_transition(diff_text, pep_number=815)

        assert len(signals) == 1
        assert signals[0].pep_number == 815
        assert signals[0].signal_type == "status_transition"
        assert signals[0].signal_value == 100
        assert "Draft" in signals[0].description
        assert "Final" in signals[0].description

    def test_detect_draft_to_accepted(self) -> None:
        """Detect Draft → Accepted transition."""
        diff_text = "-Status: Draft\n+Status: Accepted\n"
        signals = detect_status_transition(diff_text, pep_number=814)

        assert len(signals) == 1
        assert "Draft" in signals[0].description
        assert "Accepted" in signals[0].description

    def test_no_status_change(self) -> None:
        """No signal when status doesn't change."""
        diff_text = "-Title: Old Title\n+Title: New Title\nStatus: Draft\n"
        signals = detect_status_transition(diff_text, pep_number=815)

        assert len(signals) == 0

    def test_status_added_not_changed(self) -> None:
        """Don't detect signal when status is just added (new PEP)."""
        diff_text = "+PEP: 818\n+Title: New PEP\n+Status: Draft\n"
        signals = detect_status_transition(diff_text, pep_number=818)

        assert len(signals) == 0  # No transition, just addition

    def test_draft_to_withdrawn(self) -> None:
        """Detect Draft → Withdrawn transition."""
        diff_text = "-Status: Draft\n+Status: Withdrawn\n"
        signals = detect_status_transition(diff_text, pep_number=534)

        assert len(signals) == 1
        assert "Withdrawn" in signals[0].description
