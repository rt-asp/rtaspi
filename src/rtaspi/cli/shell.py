"""
Main CLI entry point for the rtaspi library.

This module provides the RTASPIShell class which handles all CLI operations
and serves as the main entry point for the command-line interface.
"""

import os
import sys
import click
import logging
from typing import Optional
from pathlib import Path

from rtaspi.core.logging import setup_logging
from rtaspi.core.config import load_config


class RTASPIShell:
    """Main shell class for handling CLI operations."""

    def __init__(self):
        self.config = None
        self.logger = logging.getLogger(__name__)

    def setup(self, config_path: Optional[str] = None, verbose: bool = False):
        """Set up the shell environment."""
        # Configure logging
        log_level = logging.DEBUG if verbose else logging.INFO
        setup_logging(level=log_level)

        # Load configuration
        if config_path:
            if not os.path.exists(config_path):
                self.logger.error(f"Config file not found: {config_path}")
                sys.exit(1)
            self.config = load_config(config_path)
        else:
            # Try default locations
            default_paths = [
                "rtaspi.config.yaml",
                "~/.config/rtaspi/config.yaml",
                "/etc/rtaspi/config.yaml",
            ]
            for path in default_paths:
                expanded_path = os.path.expanduser(path)
                if os.path.exists(expanded_path):
                    self.config = load_config(expanded_path)
                    break

            if not self.config:
                self.logger.warning("No configuration file found, using defaults")
                self.config = {}


# Create shell instance
shell = RTASPIShell()


# Common options
def common_options(f):
    """Common CLI options decorator."""
    f = click.option(
        "--config",
        "-c",
        help="Path to configuration file",
        type=click.Path(exists=True, dir_okay=False),
    )(f)
    f = click.option(
        "--verbose",
        "-v",
        is_flag=True,
        help="Enable verbose logging",
    )(f)
    return f


@click.group()
@common_options
def cli(config: Optional[str], verbose: bool):
    """RT-ASP: Real-Time Audio/Video Stream Processing.

    This tool provides a command-line interface for managing audio/video devices,
    configuring streams, and controlling processing pipelines.
    """
    shell.setup(config, verbose)


# Import commands
from .commands.config import config_cli
from .commands.devices import devices_cli
from .commands.streams import streams_cli
from .commands.pipelines import pipelines_cli
from .commands.server import server_cli

# Register command groups
cli.add_command(config_cli)
cli.add_command(devices_cli)
cli.add_command(streams_cli)
cli.add_command(pipelines_cli)
cli.add_command(server_cli)


@cli.command()
def version():
    """Show version information."""
    from rtaspi import __version__

    click.echo(f"RT-ASP version {__version__}")


@cli.command()
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish"]),
    help="Shell type for completion script",
)
@click.option(
    "--path",
    type=click.Path(dir_okay=False, writable=True),
    help="Path to save completion script",
)
def completion(shell: Optional[str], path: Optional[str]):
    """Generate shell completion script."""
    if not shell:
        # Try to detect shell
        shell = os.path.basename(os.environ.get("SHELL", ""))

    if shell not in ["bash", "zsh", "fish"]:
        click.echo("Unsupported shell type. Please specify --shell", err=True)
        sys.exit(1)

    # Load completion script
    script_path = Path(__file__).parent / "completion" / f"{shell}.{shell}"
    if not script_path.exists():
        click.echo(f"Completion script not found for shell: {shell}", err=True)
        sys.exit(1)

    script_content = script_path.read_text()

    if path:
        # Save to specified path
        Path(path).write_text(script_content)
        click.echo(f"Completion script saved to: {path}")
    else:
        # Print to stdout
        click.echo(script_content)


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
