"""PEP number extraction from file paths.

This module provides functionality to extract PEP numbers from file paths
in the Python PEPs repository.
"""

import re
from typing import Optional


def extract_pep_number(file_path: str) -> Optional[int]:
    """Extract PEP number from a file path.

    Handles various formats:
    - pep-0001.rst → 1
    - pep-0815.md → 815
    - peps/pep-0001.rst → 1
    - PEP-0001.rst → 1 (case-insensitive)
    - pep-0001-draft.rst → 1 (with suffixes)

    Args:
        file_path: Path to a PEP file (absolute, relative, or just filename).

    Returns:
        PEP number as an integer, or None if not a valid PEP file.

    Examples:
        >>> extract_pep_number("pep-0001.rst")
        1
        >>> extract_pep_number("README.md")
        None
    """
    if not file_path:
        return None

    # Extract just the filename from the path
    # Handle both Unix (/) and Windows (\) path separators
    filename = file_path.replace("\\", "/").split("/")[-1]

    # Pattern: pep-NNNN (case-insensitive, optional suffix)
    # Captures the numeric part (with or without leading zeros)
    pattern = r"^pep-(\d+)"

    match = re.match(pattern, filename, re.IGNORECASE)
    if match:
        # Regex ensures only digits, so int() will always succeed
        return int(match.group(1))

    return None
