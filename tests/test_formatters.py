"""Tests for output formatters."""

import json

from pepalyzer.formatters import format_as_json, format_as_text
from pepalyzer.models import PepActivity, PepSignal


class TestFormatAsText:
    """Test human-readable text formatter."""

    def test_format_single_pep_with_signals(self) -> None:
        """Format single PEP with signals."""
        activities = [
            PepActivity(pep_number=815, commit_count=3, files=["pep-0815.rst"])
        ]
        signals = [
            PepSignal(
                pep_number=815,
                signal_type="status_final",
                description="Status: Final",
            ),
            PepSignal(
                pep_number=815,
                signal_type="deprecation",
                description="Contains deprecation language",
            ),
        ]

        output = format_as_text(activities, signals)

        assert "PEP 815" in output
        assert "3 commits" in output
        assert "Status: Final" in output
        assert "deprecation" in output

    def test_format_multiple_peps(self) -> None:
        """Format multiple PEPs sorted by activity."""
        activities = [
            PepActivity(pep_number=815, commit_count=5, files=["pep-0815.rst"]),
            PepActivity(pep_number=1, commit_count=2, files=["pep-0001.rst"]),
            PepActivity(pep_number=427, commit_count=1, files=["pep-0427.rst"]),
        ]
        signals: list[PepSignal] = []

        output = format_as_text(activities, signals)

        # Should appear in order of commit count
        pep_815_pos = output.find("PEP 815")
        pep_1_pos = output.find("PEP 1")
        pep_427_pos = output.find("PEP 427")

        assert pep_815_pos < pep_1_pos < pep_427_pos

    def test_format_pep_without_signals(self) -> None:
        """Format PEP with no signals (just commit count)."""
        activities = [
            PepActivity(pep_number=100, commit_count=2, files=["pep-0100.rst"])
        ]
        signals: list[PepSignal] = []

        output = format_as_text(activities, signals)

        assert "PEP 100" in output
        assert "2 commits" in output

    def test_format_empty_results(self) -> None:
        """Handle empty results gracefully."""
        output = format_as_text([], [])

        output_lower = output.lower()
        assert "no pep" in output_lower or "no changes" in output_lower

    def test_format_multiple_signals_per_pep(self) -> None:
        """Format PEP with multiple signals."""
        activities = [
            PepActivity(pep_number=815, commit_count=1, files=["pep-0815.rst"])
        ]
        signals = [
            PepSignal(
                pep_number=815,
                signal_type="status_final",
                description="Status: Final",
            ),
            PepSignal(
                pep_number=815,
                signal_type="normative_language",
                description="Contains MUST/SHOULD keywords",
            ),
            PepSignal(
                pep_number=815,
                signal_type="deprecation",
                description="Contains deprecation language",
            ),
        ]

        output = format_as_text(activities, signals)

        # All signals should appear
        assert "Status: Final" in output
        assert "MUST/SHOULD" in output
        assert "deprecation" in output


class TestFormatAsJson:
    """Test JSON formatter."""

    def test_format_single_pep_as_json(self) -> None:
        """Format single PEP as valid JSON."""
        activities = [
            PepActivity(pep_number=815, commit_count=3, files=["pep-0815.rst"])
        ]
        signals = [
            PepSignal(
                pep_number=815,
                signal_type="status_final",
                description="Status: Final",
            )
        ]

        output = format_as_json(activities, signals)

        # Should be valid JSON
        data = json.loads(output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["pep_number"] == 815
        assert data[0]["commit_count"] == 3
        assert len(data[0]["signals"]) == 1

    def test_format_multiple_peps_as_json(self) -> None:
        """Format multiple PEPs as JSON array."""
        activities = [
            PepActivity(pep_number=815, commit_count=5, files=["pep-0815.rst"]),
            PepActivity(pep_number=1, commit_count=2, files=["pep-0001.rst"]),
        ]
        signals: list[PepSignal] = []

        output = format_as_json(activities, signals)

        data = json.loads(output)
        assert len(data) == 2
        assert data[0]["pep_number"] == 815
        assert data[1]["pep_number"] == 1

    def test_format_empty_as_json(self) -> None:
        """Format empty results as empty JSON array."""
        output = format_as_json([], [])

        data = json.loads(output)
        assert data == []

    def test_json_includes_all_fields(self) -> None:
        """JSON output includes all required fields."""
        activities = [
            PepActivity(
                pep_number=815,
                commit_count=3,
                files=["pep-0815.rst", "pep-0815.md"],
            )
        ]
        signals = [
            PepSignal(
                pep_number=815,
                signal_type="status_final",
                description="Status: Final",
            )
        ]

        output = format_as_json(activities, signals)

        data = json.loads(output)
        pep = data[0]

        # Check all required fields
        assert "pep_number" in pep
        assert "commit_count" in pep
        assert "files" in pep
        assert "signals" in pep

        assert isinstance(pep["files"], list)
        assert len(pep["files"]) == 2
        assert isinstance(pep["signals"], list)

    def test_json_pretty_printed(self) -> None:
        """JSON output should be pretty-printed (indented)."""
        activities = [PepActivity(pep_number=1, commit_count=1, files=["pep-0001.rst"])]
        signals: list[PepSignal] = []

        output = format_as_json(activities, signals)

        # Pretty-printed JSON should have newlines
        assert "\n" in output
        # Should have indentation
        assert "  " in output or "\t" in output
