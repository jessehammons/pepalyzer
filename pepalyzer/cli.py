"""CLI for pepalyzer."""

import click

from . import __version__


@click.command()
@click.version_option(version=__version__, prog_name="pepalyzer")
@click.help_option("--help", "-h")
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def main(files: tuple[str, ...]) -> None:
    """Pepalyzer - Text analysis CLI tool.

    A CLI tool for analyzing text files.

    Args:
        files: Tuple of file paths to process.

    Examples:
        pepalyzer file1.txt file2.txt    # Analyze multiple files
        pepalyzer *.txt                  # Analyze all text files
    """
    if not files:
        click.echo("Hello from pepalyzer!")
        click.echo("This is a text analysis CLI tool.")
        click.echo("Use --help for more information.")
        return

    # Process each file
    for file_path in files:
        click.echo(f"Processing: {file_path}")
        # TODO: Add your text analysis logic here


if __name__ == "__main__":
    main()
