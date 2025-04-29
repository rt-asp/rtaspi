"""
Stream management commands for the rtaspi CLI.

This module provides commands for managing audio/video streams.
"""

import click
import yaml
from typing import Optional
from tabulate import tabulate

from rtaspi.schemas import StreamConfig, StreamStatus
from rtaspi.constants import OutputType, FilterType
from ..shell import common_options, shell


@click.group(name="streams")
def streams_cli():
    """Manage audio/video streams."""
    pass


@streams_cli.command()
@click.option(
    "--device",
    help="Filter by source device",
)
@click.option(
    "--type",
    type=click.Choice(["video", "audio", "both"]),
    help="Filter by stream type",
)
@click.option(
    "--format",
    type=click.Choice(["table", "yaml", "json"]),
    default="table",
    help="Output format",
)
@click.option(
    "--status/--no-status",
    default=True,
    help="Include stream status information",
)
@common_options
def list(
    device: Optional[str], type: Optional[str], format: str, status: bool, **kwargs
):
    """List configured streams."""
    # Get streams from config
    streams = shell.config.get("streams", {})

    # Apply filters
    if device:
        streams = {
            name: config
            for name, config in streams.items()
            if config.get("source", {}).get("device_name") == device
        }

    if type:
        streams = {
            name: config
            for name, config in streams.items()
            if config.get("source", {}).get("stream_type") == type
        }

    if not streams:
        click.echo("No streams configured")
        return

    if format == "table":
        # Prepare table data
        headers = ["Name", "Device", "Type", "Enabled", "Outputs"]
        if status:
            headers.extend(["Status", "Duration"])

        rows = []
        for name, config in streams.items():
            source = config.get("source", {})
            outputs = config.get("outputs", [])

            row = [
                name,
                source.get("device_name", "Unknown"),
                source.get("stream_type", "Unknown"),
                "Yes" if config.get("enabled", True) else "No",
                ", ".join(o.get("type", "Unknown") for o in outputs[:3])
                + ("..." if len(outputs) > 3 else ""),
            ]

            if status:
                stream_status = StreamStatus(**config.get("status", {}))
                duration = (
                    f"{stream_status.duration}s"
                    if stream_status.duration is not None
                    else "N/A"
                )
                row.extend(["Active" if stream_status.active else "Inactive", duration])

            rows.append(row)

        click.echo(tabulate(rows, headers=headers, tablefmt="simple"))

    elif format == "yaml":
        click.echo(yaml.dump(streams, default_flow_style=False))

    else:  # json
        import json

        click.echo(json.dumps(streams, indent=2))


@streams_cli.command()
@click.argument("name")
@click.option(
    "--device",
    required=True,
    help="Source device name",
)
@click.option(
    "--type",
    type=click.Choice(["video", "audio", "both"]),
    required=True,
    help="Stream type",
)
@click.option(
    "--enabled/--disabled",
    default=True,
    help="Whether the stream is enabled",
)
@click.option(
    "--output",
    "outputs",
    multiple=True,
    type=(str, click.Choice([t.name for t in OutputType])),
    help="Add output (name type)",
)
@click.option(
    "--filter",
    "filters",
    multiple=True,
    type=(click.Choice([t.name for t in FilterType]), int),
    help="Add filter (type order)",
)
@click.option(
    "--settings",
    type=click.Path(exists=True, dir_okay=False),
    help="YAML file with additional stream settings",
)
@common_options
def create(
    name: str,
    device: str,
    type: str,
    enabled: bool,
    outputs: list[tuple[str, str]],
    filters: list[tuple[str, int]],
    settings: Optional[str],
    **kwargs,
):
    """Create a new stream."""
    # Load existing streams
    streams = shell.config.get("streams", {})

    if name in streams:
        click.echo(f"Stream '{name}' already exists", err=True)
        return

    # Create stream config
    config = {
        "name": name,
        "enabled": enabled,
        "source": {
            "device_name": device,
            "stream_type": type,
            "enabled": True,
        },
        "outputs": [
            {
                "name": output_name,
                "type": output_type,
                "enabled": True,
            }
            for output_name, output_type in outputs
        ],
        "filters": [
            {
                "type": filter_type,
                "enabled": True,
                "order": order,
            }
            for filter_type, order in filters
        ],
    }

    # Load additional settings
    if settings:
        with open(settings) as f:
            additional_settings = yaml.safe_load(f)
        config.update(additional_settings)

    # Validate config
    try:
        StreamConfig(**config)
    except Exception as e:
        click.echo(f"Invalid stream configuration: {str(e)}", err=True)
        return

    # Add to config
    streams[name] = config
    shell.config["streams"] = streams

    click.echo(f"Stream '{name}' created successfully")


@streams_cli.command()
@click.argument("name")
@common_options
def remove(name: str, **kwargs):
    """Remove a stream."""
    streams = shell.config.get("streams", {})

    if name not in streams:
        click.echo(f"Stream '{name}' not found", err=True)
        return

    del streams[name]
    shell.config["streams"] = streams

    click.echo(f"Stream '{name}' removed")


@streams_cli.command()
@click.argument("name")
@click.option(
    "--format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format",
)
@common_options
def show(name: str, format: str, **kwargs):
    """Show stream details."""
    streams = shell.config.get("streams", {})

    if name not in streams:
        click.echo(f"Stream '{name}' not found", err=True)
        return

    stream = streams[name]

    if format == "yaml":
        click.echo(yaml.dump(stream, default_flow_style=False))
    else:  # json
        import json

        click.echo(json.dumps(stream, indent=2))


@streams_cli.command()
@click.argument("name")
@click.argument("key")
@click.argument("value")
@common_options
def set(name: str, key: str, value: str, **kwargs):
    """Set stream configuration value.

    NAME is the stream name
    KEY is the dot-separated path to the configuration value
    VALUE is the new value to set
    """
    streams = shell.config.get("streams", {})

    if name not in streams:
        click.echo(f"Stream '{name}' not found", err=True)
        return

    # Parse value
    try:
        parsed_value = yaml.safe_load(value)
    except yaml.YAMLError:
        parsed_value = value

    # Update config
    stream = streams[name]
    current = stream
    parts = key.split(".")
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = parsed_value

    # Validate updated config
    try:
        StreamConfig(**stream)
    except Exception as e:
        click.echo(f"Invalid stream configuration: {str(e)}", err=True)
        return

    shell.config["streams"] = streams
    click.echo(f"Stream '{name}' configuration updated")


@streams_cli.command()
@click.argument("name")
@click.option(
    "--format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format",
)
@common_options
def status(name: str, format: str, **kwargs):
    """Show stream status."""
    streams = shell.config.get("streams", {})

    if name not in streams:
        click.echo(f"Stream '{name}' not found", err=True)
        return

    stream = streams[name]
    status = stream.get("status", {})

    if format == "yaml":
        click.echo(yaml.dump(status, default_flow_style=False))
    else:  # json
        import json

        click.echo(json.dumps(status, indent=2))


@streams_cli.command()
@click.argument("name")
@common_options
def start(name: str, **kwargs):
    """Start a stream."""
    streams = shell.config.get("streams", {})

    if name not in streams:
        click.echo(f"Stream '{name}' not found", err=True)
        return

    click.echo(f"Starting stream '{name}'...")
    # TODO: Implement stream starting
    click.echo("Stream starting not implemented yet")


@streams_cli.command()
@click.argument("name")
@common_options
def stop(name: str, **kwargs):
    """Stop a stream."""
    streams = shell.config.get("streams", {})

    if name not in streams:
        click.echo(f"Stream '{name}' not found", err=True)
        return

    click.echo(f"Stopping stream '{name}'...")
    # TODO: Implement stream stopping
    click.echo("Stream stopping not implemented yet")


@streams_cli.command()
@click.argument("name")
@common_options
def restart(name: str, **kwargs):
    """Restart a stream."""
    streams = shell.config.get("streams", {})

    if name not in streams:
        click.echo(f"Stream '{name}' not found", err=True)
        return

    click.echo(f"Restarting stream '{name}'...")
    # TODO: Implement stream restarting
    click.echo("Stream restarting not implemented yet")
