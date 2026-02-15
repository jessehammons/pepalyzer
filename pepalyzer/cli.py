"""CLI for pepalyzer."""

import re
import sys

import click

from . import __version__
from .aggregator import aggregate_by_pep
from .formatters import format_as_json, format_as_text
from .git_adapter import get_recent_commits
from .models import PepSignal
from .pep_metadata import read_pep_file
from .signals import detect_signals


def normalize_since_format(since: str) -> str:
    """Convert shorthand date formats to git-compatible formats.

    Args:
        since: Date specification (e.g., "30d", "1w", "2024-01-01").

    Returns:
        Git-compatible date string.

    Examples:
        >>> normalize_since_format("30d")
        '30 days ago'
        >>> normalize_since_format("1w")
        '1 week ago'
        >>> normalize_since_format("2024-01-01")
        '2024-01-01'
    """
    # Check if it's already a full format (has spaces or is a date)
    if " " in since or "-" in since:
        return since

    # Parse shorthand formats like "30d", "1w", "2m"
    match = re.match(r"(\d+)([dwmy])", since.lower())
    if match:
        number, unit = match.groups()
        unit_map = {
            "d": "days",
            "w": "weeks",
            "m": "months",
            "y": "years",
        }
        unit_word = unit_map.get(unit, "days")
        # Singularize if number is 1
        if number == "1":
            unit_word = unit_word.rstrip("s")
        return f"{number} {unit_word} ago"

    # If we can't parse it, return as-is and let git handle it
    return since


@click.group()
@click.version_option(version=__version__, prog_name="pepalyzer")
def main() -> None:
    """Pepalyzer - Analyze recent PEP changes.

    A CLI tool for analyzing Git commit history in the Python PEPs repository.
    """


@main.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.option(
    "--since",
    default="30d",
    help="Time window for commits (e.g., '30d', '1 week ago', '2024-01-01')",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (text or json)",
)
def scan(repo_path: str, since: str, output_format: str) -> None:
    """Scan a PEPs repository for recent changes.

    REPO_PATH: Path to the local PEPs Git repository.

    Examples::

        pepalyzer scan ~/src/peps --since 30d
        pepalyzer scan ~/src/peps --since "1 week ago" --format json
    """
    # Normalize date format for git
    since_normalized = normalize_since_format(since)

    # Get recent commits
    commits = get_recent_commits(repo_path, since_normalized)

    if not commits:
        click.echo("No commits found in the specified time period.", err=True)
        sys.exit(0)

    # Aggregate by PEP with metadata extraction
    activities = aggregate_by_pep(commits, repo_path=repo_path)

    if not activities:
        click.echo("No PEP changes found in the specified time period.", err=True)
        sys.exit(0)

    # Detect signals from file content
    signals: list[PepSignal] = []
    for activity in activities:
        # Try to read the first available file for this PEP
        for file_path in activity.files:
            content = read_pep_file(repo_path, file_path)
            if content:
                # Detect signals (signal_value already assigned in detect_signals)
                pep_signals = detect_signals(content, activity.pep_number)
                signals.extend(pep_signals)
                break  # Only analyze first readable file per PEP

    # Format and output
    if output_format == "json":
        output = format_as_json(activities, signals)
    else:
        output = format_as_text(activities, signals)

    click.echo(output)


if __name__ == "__main__":
    main()
