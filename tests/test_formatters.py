"""Tests for output formatters."""

import json

from pepalyzer.formatters import format_as_json, format_as_text
from pepalyzer.models import PepActivity, PepSignal


class TestFormatAsText:
    """Test human-readable text formatter."""

    def test_format_single_pep_with_signals(self) -> None:
        """Format single PEP with signals and metadata."""
        activities = [
            PepActivity(
                pep_number=815,
                commit_count=3,
                files=["pep-0815.rst"],
                title="Test PEP",
                status="Draft",
                abstract="This is a test abstract.",
                commit_messages=[
                    "Add initial draft of PEP 815",
                    "Clarify tp_traverse requirements",
                    "Fix typos in abstract",
                ],
            )
        ]
        signals = [
            PepSignal(
                pep_number=815,
                signal_type="normative_language",
                description="Contains normative language (RFC 2119 keywords)",
                signal_value=50,
            ),
            PepSignal(
                pep_number=815,
                signal_type="deprecation",
                description="Contains deprecation or removal language",
                signal_value=50,
            ),
        ]

        output = format_as_text(activities, signals)

        assert "PEP 815" in output
        assert "Test PEP" in output
        assert "(Draft)" in output
        assert "[3 commits]" in output
        assert "Abstract: This is a test abstract." in output
        # Check commit messages are displayed
        assert "Commits:" in output
        assert "Add initial draft of PEP 815" in output
        assert "Clarify tp_traverse requirements" in output
        assert "Fix typos in abstract" in output
        assert "normative language" in output
        assert "deprecation" in output
        # Check signal values are displayed
        assert "[50]" in output  # Medium-value signal

    def test_format_multiple_peps(self) -> None:
        """Format multiple PEPs in the order provided (sorted by aggregator)."""
        # Activities should be pre-sorted by PEP number (ascending) by aggregator
        activities = [
            PepActivity(pep_number=1, commit_count=2, files=["pep-0001.rst"]),
            PepActivity(pep_number=427, commit_count=1, files=["pep-0427.rst"]),
            PepActivity(pep_number=815, commit_count=5, files=["pep-0815.rst"]),
        ]
        signals: list[PepSignal] = []

        output = format_as_text(activities, signals)

        # Should appear in order provided (PEP number ascending)
        pep_1_pos = output.find("PEP 1")
        pep_427_pos = output.find("PEP 427")
        pep_815_pos = output.find("PEP 815")

        assert pep_1_pos < pep_427_pos < pep_815_pos
        # Verify commit counts are displayed (not used for sorting)
        assert "2 commits" in output  # PEP 1
        assert "1 commit" in output  # PEP 427 (singular)
        assert "5 commits" in output  # PEP 815

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
        """Format PEP with multiple signals sorted by value."""
        activities = [
            PepActivity(pep_number=815, commit_count=1, files=["pep-0815.rst"])
        ]
        signals = [
            PepSignal(
                pep_number=815,
                signal_type="normative_language",
                description="Contains MUST/SHOULD keywords",
                signal_value=50,
            ),
            PepSignal(
                pep_number=815,
                signal_type="deprecation",
                description="Contains deprecation language",
                signal_value=50,
            ),
        ]

        output = format_as_text(activities, signals)

        # All signals should appear
        assert "MUST/SHOULD" in output
        assert "deprecation" in output
        # Both have same value, so order is by signal_type (alphabetical within same value)
        assert "[50]" in output


class TestFormatAsJson:
    """Test JSON formatter."""

    def test_format_single_pep_as_json(self) -> None:
        """Format single PEP as valid JSON with metadata."""
        activities = [
            PepActivity(
                pep_number=815,
                commit_count=3,
                files=["pep-0815.rst"],
                title="Test PEP",
                status="Draft",
                abstract="Test abstract",
                commit_messages=[
                    "Add initial draft of PEP 815",
                    "Clarify tp_traverse requirements",
                    "Fix typos in abstract",
                ],
            )
        ]
        signals = [
            PepSignal(
                pep_number=815,
                signal_type="normative_language",
                description="Contains normative language (RFC 2119 keywords)",
                signal_value=50,
            )
        ]

        output = format_as_json(activities, signals)

        # Should be valid JSON
        data = json.loads(output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["pep_number"] == 815
        assert data[0]["title"] == "Test PEP"
        assert data[0]["status"] == "Draft"
        assert data[0]["abstract"] == "Test abstract"
        assert data[0]["commit_count"] == 3
        # Check commit_messages is included
        assert "commit_messages" in data[0]
        assert len(data[0]["commit_messages"]) == 3
        assert data[0]["commit_messages"][0] == "Add initial draft of PEP 815"
        assert data[0]["commit_messages"][1] == "Clarify tp_traverse requirements"
        assert data[0]["commit_messages"][2] == "Fix typos in abstract"
        assert len(data[0]["signals"]) == 1
        # Check signal_value is included
        assert data[0]["signals"][0]["signal_value"] == 50

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
        """JSON output includes all required and metadata fields."""
        activities = [
            PepActivity(
                pep_number=815,
                commit_count=3,
                files=["pep-0815.rst", "pep-0815.md"],
                title="Disallow reference cycles",
                status="Draft",
                abstract="This PEP proposes...",
                authors=["Sam Gross <sam@example.com>"],
                pep_type="Standards Track",
                created="11-Jan-2024",
            )
        ]
        signals = [
            PepSignal(
                pep_number=815,
                signal_type="status_final",
                description="Status: Final",
                signal_value=100,
            )
        ]

        output = format_as_json(activities, signals)

        data = json.loads(output)
        pep = data[0]

        # Check all required fields
        assert "pep_number" in pep
        assert pep["pep_number"] == 815
        # Metadata fields
        assert "title" in pep
        assert pep["title"] == "Disallow reference cycles"
        assert "status" in pep
        assert pep["status"] == "Draft"
        assert "abstract" in pep
        assert "authors" in pep
        assert len(pep["authors"]) == 1
        assert "pep_type" in pep
        assert pep["pep_type"] == "Standards Track"
        assert "created" in pep
        # Auxiliary fields
        assert "commit_count" in pep
        assert "files" in pep
        assert "signals" in pep

        assert isinstance(pep["files"], list)
        assert len(pep["files"]) == 2
        assert isinstance(pep["signals"], list)
        # Check signal has signal_value
        assert "signal_value" in pep["signals"][0]
        assert pep["signals"][0]["signal_value"] == 100

    def test_json_pretty_printed(self) -> None:
        """JSON output should be pretty-printed (indented)."""
        activities = [PepActivity(pep_number=1, commit_count=1, files=["pep-0001.rst"])]
        signals: list[PepSignal] = []

        output = format_as_json(activities, signals)

        # Pretty-printed JSON should have newlines
        assert "\n" in output
        # Should have indentation
        assert "  " in output or "\t" in output
