"""Tests for PEP number extraction from file paths."""

from pepalyzer.pep_parser import extract_pep_number


class TestExtractPepNumber:
    """Test PEP number extraction from various file path formats."""

    def test_simple_pep_file_rst(self) -> None:
        """Extract PEP number from simple .rst file."""
        assert extract_pep_number("pep-0001.rst") == 1

    def test_simple_pep_file_md(self) -> None:
        """Extract PEP number from simple .md file."""
        assert extract_pep_number("pep-0815.md") == 815

    def test_simple_pep_file_txt(self) -> None:
        """Extract PEP number from .txt file."""
        assert extract_pep_number("pep-0020.txt") == 20

    def test_pep_with_directory_path(self) -> None:
        """Extract PEP number from file with directory prefix."""
        assert extract_pep_number("peps/pep-0001.rst") == 1

    def test_pep_with_nested_path(self) -> None:
        """Extract PEP number from nested directory path."""
        assert extract_pep_number("repo/peps/pep-0815.md") == 815

    def test_pep_uppercase(self) -> None:
        """Handle uppercase PEP prefix."""
        assert extract_pep_number("PEP-0001.rst") == 1

    def test_pep_mixed_case(self) -> None:
        """Handle mixed case PEP prefix."""
        assert extract_pep_number("Pep-0001.rst") == 1

    def test_pep_high_number(self) -> None:
        """Extract high PEP numbers (four digits)."""
        assert extract_pep_number("pep-9999.txt") == 9999

    def test_pep_no_leading_zeros(self) -> None:
        """Extract PEP number without leading zeros."""
        assert extract_pep_number("pep-1.rst") == 1

    def test_pep_with_suffix(self) -> None:
        """Handle PEP files with suffixes like -draft."""
        # The actual PEP number should still be extracted
        assert extract_pep_number("pep-0001-draft.rst") == 1

    def test_non_pep_file_readme(self) -> None:
        """Return None for non-PEP files like README."""
        assert extract_pep_number("README.md") is None

    def test_non_pep_file_index(self) -> None:
        """Return None for non-PEP files like index."""
        assert extract_pep_number("index.html") is None

    def test_non_pep_file_config(self) -> None:
        """Return None for configuration files."""
        assert extract_pep_number(".gitignore") is None

    def test_empty_string(self) -> None:
        """Return None for empty string."""
        assert extract_pep_number("") is None

    def test_invalid_pep_format(self) -> None:
        """Return None for invalid PEP format."""
        assert extract_pep_number("pep.rst") is None

    def test_pep_with_letters_in_number(self) -> None:
        """Return None for PEP with non-numeric parts."""
        assert extract_pep_number("pep-abc.rst") is None

    def test_absolute_path(self) -> None:
        """Extract PEP number from absolute path."""
        assert extract_pep_number("/home/user/peps/pep-0001.rst") == 1

    def test_windows_path(self) -> None:
        """Extract PEP number from Windows-style path."""
        assert extract_pep_number("C:\\Users\\user\\peps\\pep-0001.rst") == 1

    def test_pep_zero(self) -> None:
        """Handle PEP 0 (the index)."""
        assert extract_pep_number("pep-0000.rst") == 0
