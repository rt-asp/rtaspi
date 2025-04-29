"""
Configuration management commands for the rtaspi CLI.

This module provides commands for viewing and modifying rtaspi configuration.
"""

import os
import click
import yaml
from pathlib import Path
from typing import Optional

from rtaspi.core.config import load_config, save_config
from ..shell import common_options, shell


@click.group(name="config")
def config_cli():
    """Manage rtaspi configuration."""
    pass


@config_cli.command()
@click.argument("key", required=False)
@common_options
def get(key: Optional[str], **kwargs):
    """Get configuration value(s).

    If KEY is provided, show only that value.
    Otherwise, show all configuration values.
    """
    if key:
        # Get specific value
        value = shell.config
        for part in key.split("."):
            try:
                value = value[part]
            except (KeyError, TypeError):
                click.echo(f"Configuration key not found: {key}", err=True)
                return

        # Format output based on value type
        if isinstance(value, (dict, list)):
            click.echo(yaml.dump(value, default_flow_style=False))
        else:
            click.echo(str(value))
    else:
        # Show all config
        click.echo(yaml.dump(shell.config, default_flow_style=False))


@config_cli.command()
@click.argument("key")
@click.argument("value")
@click.option(
    "--level",
    type=click.Choice(["user", "project", "global"]),
    default="user",
    help="Configuration level to modify",
)
@common_options
def set(key: str, value: str, level: str, **kwargs):
    """Set configuration value.

    KEY is the dot-separated path to the configuration value.
    VALUE is the new value to set.
    """
    # Determine config file path based on level
    if level == "user":
        config_path = os.path.expanduser("~/.config/rtaspi/config.yaml")
    elif level == "project":
        config_path = ".rtaspi/config.yaml"
    else:  # global
        config_path = "/etc/rtaspi/config.yaml"

    # Load existing config or create new
    config = {}
    if os.path.exists(config_path):
        config = load_config(config_path)

    # Parse value
    try:
        parsed_value = yaml.safe_load(value)
    except yaml.YAMLError:
        # If YAML parsing fails, treat as string
        parsed_value = value

    # Update config
    current = config
    parts = key.split(".")
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = parsed_value

    # Ensure directory exists
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    # Save config
    save_config(config, config_path)
    click.echo(f"Configuration updated at {config_path}")


@config_cli.command()
@click.argument("key")
@click.option(
    "--level",
    type=click.Choice(["user", "project", "global"]),
    default="user",
    help="Configuration level to modify",
)
@common_options
def unset(key: str, level: str, **kwargs):
    """Remove configuration value.

    KEY is the dot-separated path to the configuration value.
    """
    # Determine config file path based on level
    if level == "user":
        config_path = os.path.expanduser("~/.config/rtaspi/config.yaml")
    elif level == "project":
        config_path = ".rtaspi/config.yaml"
    else:  # global
        config_path = "/etc/rtaspi/config.yaml"

    if not os.path.exists(config_path):
        click.echo(f"Configuration file not found: {config_path}", err=True)
        return

    # Load config
    config = load_config(config_path)

    # Remove key
    current = config
    parts = key.split(".")
    try:
        for part in parts[:-1]:
            current = current[part]
        del current[parts[-1]]
    except (KeyError, TypeError):
        click.echo(f"Configuration key not found: {key}", err=True)
        return

    # Save config
    save_config(config, config_path)
    click.echo(f"Configuration key removed: {key}")


@config_cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path (defaults to stdout)",
)
@common_options
def dump(output: Optional[str], **kwargs):
    """Dump complete configuration to file."""
    config_yaml = yaml.dump(shell.config, default_flow_style=False)

    if output:
        Path(output).write_text(config_yaml)
        click.echo(f"Configuration dumped to {output}")
    else:
        click.echo(config_yaml)


@config_cli.command()
@click.argument(
    "files",
    type=click.Path(exists=True, dir_okay=False),
    nargs=-1,
    required=True,
)
@click.option(
    "--merge/--replace",
    default=True,
    help="Merge with existing config or replace entirely",
)
@common_options
def load(files: tuple[str, ...], merge: bool, **kwargs):
    """Load configuration from file(s).

    Multiple files can be specified and will be merged in order.
    """
    config = {} if not merge else dict(shell.config)

    for file in files:
        new_config = load_config(file)
        if merge:
            # Deep merge
            def merge_dicts(d1, d2):
                for k, v in d2.items():
                    if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
                        merge_dicts(d1[k], v)
                    else:
                        d1[k] = v

            merge_dicts(config, new_config)
        else:
            config = new_config

    # Save as user config
    config_path = os.path.expanduser("~/.config/rtaspi/config.yaml")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    save_config(config, config_path)

    click.echo(f"Configuration {'merged into' if merge else 'loaded to'} {config_path}")
