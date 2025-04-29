"""
Device management commands for the rtaspi CLI.

This module provides commands for managing audio/video devices.
"""

import click
import yaml
from typing import Optional
from tabulate import tabulate

from rtaspi.schemas import DeviceConfig, DeviceStatus
from rtaspi.constants import DeviceType
from ..shell import common_options, shell


@click.group(name="devices")
def devices_cli():
    """Manage audio/video devices."""
    pass


@devices_cli.command()
@click.option(
    "--type",
    type=click.Choice([t.name for t in DeviceType]),
    help="Filter by device type",
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
    help="Include device status information",
)
@common_options
def list(type: Optional[str], format: str, status: bool, **kwargs):
    """List configured devices."""
    # Get devices from config
    devices = shell.config.get("devices", {})

    # Filter by type if specified
    if type:
        device_type = DeviceType[type]
        devices = {
            name: config
            for name, config in devices.items()
            if DeviceType[config["type"]] == device_type
        }

    if not devices:
        click.echo("No devices configured")
        return

    if format == "table":
        # Prepare table data
        headers = ["Name", "Type", "Enabled"]
        if status:
            headers.extend(["Status", "Last Seen"])

        rows = []
        for name, config in devices.items():
            row = [
                name,
                config.get("type", "Unknown"),
                "Yes" if config.get("enabled", True) else "No",
            ]
            if status:
                device_status = DeviceStatus(**config.get("status", {}))
                row.extend(
                    [
                        "Online" if device_status.online else "Offline",
                        device_status.last_seen or "Never",
                    ]
                )
            rows.append(row)

        click.echo(tabulate(rows, headers=headers, tablefmt="simple"))

    elif format == "yaml":
        click.echo(yaml.dump(devices, default_flow_style=False))

    else:  # json
        import json

        click.echo(json.dumps(devices, indent=2))


@devices_cli.command()
@click.argument("name")
@click.option(
    "--type",
    type=click.Choice([t.name for t in DeviceType]),
    required=True,
    help="Device type",
)
@click.option(
    "--enabled/--disabled",
    default=True,
    help="Whether the device is enabled",
)
@click.option(
    "--host",
    help="Hostname/IP for network devices",
)
@click.option(
    "--port",
    type=int,
    help="Port number for network devices",
)
@click.option(
    "--username",
    help="Username for device authentication",
)
@click.option(
    "--password",
    help="Password for device authentication",
)
@click.option(
    "--settings",
    type=click.Path(exists=True, dir_okay=False),
    help="YAML file with additional device settings",
)
@common_options
def add(
    name: str,
    type: str,
    enabled: bool,
    host: Optional[str],
    port: Optional[int],
    username: Optional[str],
    password: Optional[str],
    settings: Optional[str],
    **kwargs,
):
    """Add a new device."""
    # Load existing devices
    devices = shell.config.get("devices", {})

    if name in devices:
        click.echo(f"Device '{name}' already exists", err=True)
        return

    # Create device config
    device_type = DeviceType[type]
    config = {
        "name": name,
        "type": type,
        "enabled": enabled,
    }

    # Add connection details for network devices
    if device_type.is_network_device():
        if not host:
            click.echo("Host is required for network devices", err=True)
            return

        config["connection"] = {
            "host": host,
            "port": port,
        }

        if username or password:
            config["connection"]["auth"] = {
                "username": username,
                "password": password,
            }

    # Load additional settings
    if settings:
        with open(settings) as f:
            additional_settings = yaml.safe_load(f)
        config["settings"] = additional_settings

    # Validate config
    try:
        DeviceConfig(**config)
    except Exception as e:
        click.echo(f"Invalid device configuration: {str(e)}", err=True)
        return

    # Add to config
    devices[name] = config
    shell.config["devices"] = devices

    click.echo(f"Device '{name}' added successfully")


@devices_cli.command()
@click.argument("name")
@common_options
def remove(name: str, **kwargs):
    """Remove a device."""
    devices = shell.config.get("devices", {})

    if name not in devices:
        click.echo(f"Device '{name}' not found", err=True)
        return

    del devices[name]
    shell.config["devices"] = devices

    click.echo(f"Device '{name}' removed")


@devices_cli.command()
@click.argument("name")
@click.option(
    "--format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format",
)
@common_options
def show(name: str, format: str, **kwargs):
    """Show device details."""
    devices = shell.config.get("devices", {})

    if name not in devices:
        click.echo(f"Device '{name}' not found", err=True)
        return

    device = devices[name]

    if format == "yaml":
        click.echo(yaml.dump(device, default_flow_style=False))
    else:  # json
        import json

        click.echo(json.dumps(device, indent=2))


@devices_cli.command()
@click.argument("name")
@click.argument("key")
@click.argument("value")
@common_options
def set(name: str, key: str, value: str, **kwargs):
    """Set device configuration value.

    NAME is the device name
    KEY is the dot-separated path to the configuration value
    VALUE is the new value to set
    """
    devices = shell.config.get("devices", {})

    if name not in devices:
        click.echo(f"Device '{name}' not found", err=True)
        return

    # Parse value
    try:
        parsed_value = yaml.safe_load(value)
    except yaml.YAMLError:
        parsed_value = value

    # Update config
    device = devices[name]
    current = device
    parts = key.split(".")
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = parsed_value

    # Validate updated config
    try:
        DeviceConfig(**device)
    except Exception as e:
        click.echo(f"Invalid device configuration: {str(e)}", err=True)
        return

    shell.config["devices"] = devices
    click.echo(f"Device '{name}' configuration updated")


@devices_cli.command()
@click.argument("name")
@click.option(
    "--format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format",
)
@common_options
def status(name: str, format: str, **kwargs):
    """Show device status."""
    devices = shell.config.get("devices", {})

    if name not in devices:
        click.echo(f"Device '{name}' not found", err=True)
        return

    device = devices[name]
    status = device.get("status", {})

    if format == "yaml":
        click.echo(yaml.dump(status, default_flow_style=False))
    else:  # json
        import json

        click.echo(json.dumps(status, indent=2))


@devices_cli.command()
@click.argument("name")
@common_options
def scan(name: str, **kwargs):
    """Scan device capabilities."""
    devices = shell.config.get("devices", {})

    if name not in devices:
        click.echo(f"Device '{name}' not found", err=True)
        return

    click.echo(f"Scanning capabilities for device '{name}'...")
    # TODO: Implement device capability scanning
    click.echo("Device scanning not implemented yet")
