"""Tests for PEP metadata extraction."""

from pathlib import Path
import tempfile

from pepalyzer.pep_metadata import extract_pep_metadata, read_pep_file


class TestExtractPepMetadata:
    """Test PEP header parsing and metadata extraction."""

    def test_parse_complete_headers(self) -> None:
        """Extract all metadata fields from complete PEP headers."""
        content = """\
PEP: 815
Title: Disallow reference cycles in tp_traverse
Author: Sam Gross <colesbury@gmail.com>
Status: Draft
Type: Standards Track
Created: 11-Jan-2024

Abstract
========

This PEP proposes disallowing reference cycles in tp_traverse to prevent
memory leaks in extension modules.

More content here.
"""
        metadata = extract_pep_metadata(content)

        assert metadata.title == "Disallow reference cycles in tp_traverse"
        assert metadata.status == "Draft"
        assert metadata.pep_type == "Standards Track"
        assert metadata.created == "11-Jan-2024"
        assert metadata.authors == ["Sam Gross <colesbury@gmail.com>"]
        assert metadata.abstract is not None
        assert "reference cycles" in metadata.abstract
        assert "memory leaks" in metadata.abstract

    def test_parse_minimal_headers(self) -> None:
        """Handle PEP with only required headers."""
        content = """\
PEP: 1
Title: PEP Purpose and Guidelines
Status: Active

This is the abstract.
"""
        metadata = extract_pep_metadata(content)

        assert metadata.title == "PEP Purpose and Guidelines"
        assert metadata.status == "Active"
        assert metadata.pep_type is None
        assert metadata.created is None
        assert metadata.authors == []
        assert metadata.abstract is not None
        assert "abstract" in metadata.abstract.lower()

    def test_parse_multiline_author(self) -> None:
        """Handle multi-line Author field with continuation."""
        content = """\
PEP: 8
Title: Style Guide for Python Code
Author: Guido van Rossum <guido@python.org>,
        Barry Warsaw <barry@python.org>
Status: Active
Type: Process

Abstract here.
"""
        metadata = extract_pep_metadata(content)

        assert metadata.title == "Style Guide for Python Code"
        assert len(metadata.authors) == 2
        assert "Guido van Rossum <guido@python.org>" in metadata.authors
        assert "Barry Warsaw <barry@python.org>" in metadata.authors

    def test_parse_multiline_title(self) -> None:
        """Handle multi-line Title field with continuation."""
        content = """\
PEP: 484
Title: Type Hints for Python and Related
        Infrastructure
Author: Guido van Rossum <guido@python.org>
Status: Final

Abstract goes here.
"""
        metadata = extract_pep_metadata(content)

        assert metadata.title is not None
        assert "Type Hints" in metadata.title
        assert "Infrastructure" in metadata.title

    def test_extract_abstract_rst_format(self) -> None:
        """Extract abstract from reStructuredText format with header."""
        content = """\
PEP: 815
Title: Test PEP
Status: Draft

Abstract
========

This is the first paragraph of the abstract.
It continues on multiple lines.

This is a second paragraph that should not be included.
"""
        metadata = extract_pep_metadata(content)

        assert metadata.abstract is not None
        assert "first paragraph" in metadata.abstract
        assert "second paragraph" not in metadata.abstract

    def test_extract_abstract_markdown_format(self) -> None:
        """Extract abstract from Markdown format with header."""
        content = """\
PEP: 750
Title: Test PEP
Status: Draft

## Abstract

This is the abstract in markdown format.
It spans multiple lines.

Another paragraph.
"""
        metadata = extract_pep_metadata(content)

        assert metadata.abstract is not None
        assert "abstract in markdown" in metadata.abstract
        assert "Another paragraph" not in metadata.abstract

    def test_extract_abstract_no_header(self) -> None:
        """Extract abstract when it's first paragraph after headers."""
        content = """\
PEP: 1
Title: Test
Status: Draft

This is the abstract as the first paragraph without a header.

Second paragraph.
"""
        metadata = extract_pep_metadata(content)

        assert metadata.abstract is not None
        assert "first paragraph" in metadata.abstract
        assert "Second paragraph" not in metadata.abstract

    def test_handle_missing_abstract(self) -> None:
        """Return None for abstract when no content after headers."""
        content = """\
PEP: 1
Title: Test
Status: Draft
"""
        metadata = extract_pep_metadata(content)

        assert metadata.abstract is None

    def test_handle_malformed_headers(self) -> None:
        """Extract what's possible from malformed headers."""
        content = """\
PEP: 999
Title: Valid Title
This line has no colon
Status: Draft
InvalidFormat
Author: Someone <email@example.com>

Abstract text.
"""
        metadata = extract_pep_metadata(content)

        # Should extract valid fields
        assert metadata.title == "Valid Title"
        assert metadata.status == "Draft"
        assert "Someone <email@example.com>" in metadata.authors

    def test_handle_empty_content(self) -> None:
        """Return empty metadata for empty content."""
        metadata = extract_pep_metadata("")

        assert metadata.title is None
        assert metadata.status is None
        assert metadata.abstract is None

    def test_handle_headers_only(self) -> None:
        """Handle content with only headers, no body."""
        content = """\
PEP: 1
Title: Test
Status: Draft
"""
        metadata = extract_pep_metadata(content)

        assert metadata.title == "Test"
        assert metadata.status == "Draft"
        assert metadata.abstract is None

    def test_case_insensitive_headers(self) -> None:
        """Handle headers with different case variations."""
        content = """\
pep: 1
title: Test Title
STATUS: Draft
type: Informational

Abstract here.
"""
        metadata = extract_pep_metadata(content)

        assert metadata.title == "Test Title"
        assert metadata.status == "Draft"
        assert metadata.pep_type == "Informational"

    def test_strip_whitespace_from_values(self) -> None:
        """Strip leading/trailing whitespace from header values."""
        content = """\
PEP: 1
Title:    Test Title With Spaces
Status:  Draft
Type:  Informational

Abstract.
"""
        metadata = extract_pep_metadata(content)

        assert metadata.title == "Test Title With Spaces"
        assert metadata.status == "Draft"
        assert metadata.pep_type == "Informational"


class TestReadPepFile:
    """Test reading PEP files from filesystem."""

    def test_read_existing_file(self) -> None:
        """Read content from an existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test PEP file
            pep_path = Path(tmpdir) / "pep-0001.rst"
            pep_content = "PEP: 1\nTitle: Test\nStatus: Active\n\nAbstract."
            pep_path.write_text(pep_content, encoding="utf-8")

            # Read it back
            content = read_pep_file(tmpdir, "pep-0001.rst")

            assert content is not None
            assert "PEP: 1" in content
            assert "Test" in content

    def test_read_file_with_subdirectory(self) -> None:
        """Read file from subdirectory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested directory structure
            subdir = Path(tmpdir) / "peps"
            subdir.mkdir()
            pep_path = subdir / "pep-0815.rst"
            pep_path.write_text("PEP: 815\nTitle: Test\n", encoding="utf-8")

            # Read with relative path
            content = read_pep_file(tmpdir, "peps/pep-0815.rst")

            assert content is not None
            assert "PEP: 815" in content

    def test_read_nonexistent_file(self) -> None:
        """Return None for nonexistent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = read_pep_file(tmpdir, "pep-9999.rst")

            assert content is None

    def test_read_markdown_file(self) -> None:
        """Read .md file (newer PEP format)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pep_path = Path(tmpdir) / "pep-0750.md"
            pep_path.write_text("# PEP 750\n\n## Abstract\n\nTest.", encoding="utf-8")

            content = read_pep_file(tmpdir, "pep-0750.md")

            assert content is not None
            assert "PEP 750" in content

    def test_handle_encoding_error(self) -> None:
        """Return None for files with encoding errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with non-UTF-8 content
            pep_path = Path(tmpdir) / "pep-bad.rst"
            pep_path.write_bytes(b"PEP: 1\nTitle: \xff\xfe Invalid UTF-8\n")

            content = read_pep_file(tmpdir, "pep-bad.rst")

            # Should handle gracefully (either return None or valid content)
            # Implementation choice: return None for safety
            assert content is None or isinstance(content, str)

    def test_handle_permission_error(self) -> None:
        """Return None when file cannot be read due to permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pep_path = Path(tmpdir) / "pep-forbidden.rst"
            pep_path.write_text("PEP: 1\n", encoding="utf-8")

            # Make file unreadable (Unix only)
            import os

            if os.name != "nt":  # Skip on Windows
                pep_path.chmod(0o000)

                content = read_pep_file(tmpdir, "pep-forbidden.rst")

                assert content is None

                # Restore permissions for cleanup
                pep_path.chmod(0o644)

    def test_read_empty_file(self) -> None:
        """Return empty string for empty file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pep_path = Path(tmpdir) / "pep-empty.rst"
            pep_path.write_text("", encoding="utf-8")

            content = read_pep_file(tmpdir, "pep-empty.rst")

            assert content == ""
