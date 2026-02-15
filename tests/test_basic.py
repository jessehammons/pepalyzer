"""Basic tests for pepalyzer."""

import pepalyzer


def test_version() -> None:
    """Test that version is defined."""
    assert pepalyzer.__version__ == "0.1.0"


def test_import() -> None:
    """Test that pepalyzer can be imported."""
    assert pepalyzer is not None
