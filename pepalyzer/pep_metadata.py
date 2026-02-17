"""PEP metadata extraction from file headers.

This module provides functions to read PEP files and extract structured
metadata from RFC 822-style headers.
"""

from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass(frozen=True)
class PepMetadata:
    """Extracted metadata from PEP file headers.

    All fields are optional since files may be malformed or incomplete.

    Attributes:
        title: Human-readable PEP title (from Title: field).
        status: Current status (Draft, Accepted, Final, etc.).
        abstract: First 1-3 sentences from Abstract section or first paragraph.
        authors: List of author names/emails (from Author: field).
        pep_type: Type of PEP (Standards Track, Informational, Process).
        created: PEP creation date (from Created: field, kept as string).
    """

    title: str | None = None
    status: str | None = None
    abstract: str | None = None
    authors: list[str] = field(default_factory=list)
    pep_type: str | None = None
    created: str | None = None


def extract_pep_metadata(content: str) -> PepMetadata:
    """Extract structured metadata from PEP file content.

    Parses RFC 822-style headers at the top of the file and extracts
    the abstract from the first paragraph or Abstract section.

    Args:
        content: Full text content of a PEP file.

    Returns:
        PepMetadata with extracted fields. Fields are None if not found.

    Examples:
        >>> content = '''
        ... PEP: 815
        ... Title: Test PEP
        ... Status: Draft
        ...
        ... This is the abstract.
        ... '''
        >>> meta = extract_pep_metadata(content)
        >>> meta.title
        'Test PEP'
        >>> meta.status
        'Draft'
    """
    if not content.strip():
        return PepMetadata()

    lines = content.split("\n")

    # Phase 1: Parse headers (RFC 822 format)
    headers = _parse_headers(lines)

    # Phase 2: Extract abstract from body
    abstract = _extract_abstract(lines, headers)

    # Parse authors (may be comma-separated)
    authors = []
    if "author" in headers:
        author_text = headers["author"]
        # Split by comma, strip whitespace
        authors = [a.strip() for a in author_text.split(",") if a.strip()]

    return PepMetadata(
        title=headers.get("title"),
        status=headers.get("status"),
        abstract=abstract,
        authors=authors,
        pep_type=headers.get("type"),
        created=headers.get("created"),
    )


def _parse_headers(lines: list[str]) -> dict[str, str]:
    """Parse RFC 822-style headers from lines.

    Args:
        lines: Lines of file content.

    Returns:
        Dictionary of header key -> value (lowercase keys).
    """
    headers: dict[str, str] = {}
    current_key: str | None = None
    current_value: list[str] = []

    for line in lines:
        # Blank line marks end of headers
        if not line.strip():
            # Save any accumulated header
            if current_key:
                headers[current_key] = " ".join(current_value).strip()
            break

        # Check if this is a new header (contains colon)
        if ":" in line and not line[0].isspace():
            # Save previous header
            if current_key:
                headers[current_key] = " ".join(current_value).strip()

            # Parse new header
            key, _, value = line.partition(":")
            current_key = key.strip().lower()
            current_value = [value.strip()]

        # Continuation line (starts with whitespace)
        elif line[0].isspace() and current_key:
            current_value.append(line.strip())

    # Save final header if we reached end of file
    if current_key:
        headers[current_key] = " ".join(current_value).strip()

    return headers


def _extract_abstract(lines: list[str], headers: dict[str, str]) -> str | None:
    """Extract abstract from PEP body content.

    Looks for:
    1. Explicit "Abstract" section (RST or Markdown)
    2. First paragraph after headers

    Args:
        lines: Lines of file content.
        headers: Parsed headers (to know where body starts).

    Returns:
        Abstract text (first paragraph only), or None if no content found.
    """
    body_lines = _skip_to_body(lines)
    abstract_lines = _collect_abstract_lines(body_lines)

    if not abstract_lines:
        return None

    # Join lines, preserving paragraph structure
    return "\n".join(abstract_lines)


def _skip_to_body(lines: list[str]) -> list[str]:
    """Skip header lines and return body lines starting after first blank line."""
    for i, line in enumerate(lines):
        if not line.strip():
            return lines[i + 1 :]
    return []


def _collect_abstract_lines(lines: list[str]) -> list[str]:
    """Collect lines that make up the abstract paragraph."""
    abstract_lines: list[str] = []
    in_abstract_section = False

    for line in lines:
        # Skip blank lines at start
        if not abstract_lines and not line.strip():
            continue

        # Check for explicit "Abstract" header
        if re.match(r"^(Abstract|##\s*Abstract)\s*$", line.strip(), re.IGNORECASE):
            in_abstract_section = True
            continue

        # Skip RST underlines (===, ---)
        if re.match(r"^[=\-]+\s*$", line.strip()):
            continue

        # Collect lines if in abstract section or reading first paragraph
        if in_abstract_section or (
            not abstract_lines and not line.strip().startswith(".. ")
        ):
            if _is_paragraph_end(line, abstract_lines):
                break
            abstract_lines.append(line.strip())

    return abstract_lines


def _is_paragraph_end(line: str, collected_lines: list[str]) -> bool:
    """Check if this line marks the end of the abstract paragraph."""
    # Stop at blank line (end of paragraph)
    if not line.strip():
        return True

    # Stop at next section header (but only if we have content)
    if collected_lines and re.match(r"^(#{1,6}\s+|[A-Z][\w\s]+)", line.strip()):
        return True

    return False


def read_pep_file(repo_path: str, file_path: str) -> str | None:
    """Read a PEP file from the repository.

    Args:
        repo_path: Path to the repository root directory.
        file_path: Relative path to the PEP file within the repository.

    Returns:
        File content as string, or None if file cannot be read.

    Examples:
        >>> content = read_pep_file("/path/to/peps", "pep-0001.rst")
        >>> content is not None
        True
    """
    try:
        full_path = Path(repo_path) / file_path
        return full_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        # File doesn't exist (may have been deleted)
        return None
    except PermissionError:
        # Cannot read file due to permissions
        return None
    except UnicodeDecodeError:
        # File is not valid UTF-8 text
        return None
    except OSError:
        # Other IO errors (disk issues, etc.)
        return None
