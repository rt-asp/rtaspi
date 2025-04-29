"""
Pipeline management commands for the rtaspi CLI.

This module provides commands for managing processing pipelines.
"""

import click
import yaml
from typing import Optional
from tabulate import tabulate

from rtaspi.schemas import PipelineConfig, PipelineStatus
from rtaspi.constants import FilterType
from ..shell import common_options, shell


@click.group(name="pipelines")
def pipelines_cli():
    """Manage processing pipelines."""
    pass


@pipelines_cli.command()
@click.option(
    "--format",
    type=click.Choice(["table", "yaml", "json"]),
    default="table",
    help="Output format",
)
@click.option(
    "--status/--no-status",
    default=True,
    help="Include pipeline status information",
)
@common_options
def list(format: str, status: bool, **kwargs):
    """List configured pipelines."""
    # Get pipelines from config
    pipelines = shell.config.get("pipelines", {})

    if not pipelines:
        click.echo("No pipelines configured")
        return

    if format == "table":
        # Prepare table data
        headers = ["Name", "Enabled", "Stages", "Description"]
        if status:
            headers.extend(["Status", "Start Time"])

        rows = []
        for name, config in pipelines.items():
            stages = config.get("stages", [])

            row = [
                name,
                "Yes" if config.get("enabled", True) else "No",
                str(len(stages)),
                config.get("description", "")[:50]
                + ("..." if len(config.get("description", "")) > 50 else ""),
            ]

            if status:
                pipeline_status = PipelineStatus(**config.get("status", {}))
                row.extend(
                    [
                        "Running" if pipeline_status.running else "Stopped",
                        pipeline_status.start_time or "Never",
                    ]
                )

            rows.append(row)

        click.echo(tabulate(rows, headers=headers, tablefmt="simple"))

    elif format == "yaml":
        click.echo(yaml.dump(pipelines, default_flow_style=False))

    else:  # json
        import json

        click.echo(json.dumps(pipelines, indent=2))


@pipelines_cli.command()
@click.argument("name")
@click.option(
    "--description",
    help="Pipeline description",
)
@click.option(
    "--enabled/--disabled",
    default=True,
    help="Whether the pipeline is enabled",
)
@click.option(
    "--parallel/--sequential",
    default=True,
    help="Whether stages can execute in parallel",
)
@click.option(
    "--settings",
    type=click.Path(exists=True, dir_okay=False),
    help="YAML file with pipeline configuration",
)
@common_options
def create(
    name: str,
    description: Optional[str],
    enabled: bool,
    parallel: bool,
    settings: Optional[str],
    **kwargs,
):
    """Create a new pipeline."""
    # Load existing pipelines
    pipelines = shell.config.get("pipelines", {})

    if name in pipelines:
        click.echo(f"Pipeline '{name}' already exists", err=True)
        return

    # Create pipeline config
    config = {
        "name": name,
        "enabled": enabled,
        "description": description,
        "execution_settings": {
            "parallel_execution": parallel,
        },
        "stages": [],
    }

    # Load settings from file
    if settings:
        with open(settings) as f:
            pipeline_settings = yaml.safe_load(f)
        config.update(pipeline_settings)

    # Validate config
    try:
        PipelineConfig(**config)
    except Exception as e:
        click.echo(f"Invalid pipeline configuration: {str(e)}", err=True)
        return

    # Add to config
    pipelines[name] = config
    shell.config["pipelines"] = pipelines

    click.echo(f"Pipeline '{name}' created successfully")


@pipelines_cli.command()
@click.argument("name")
@click.argument("stage_name")
@click.option(
    "--type",
    type=click.Choice(["source", "filter", "transform", "merge", "split", "output"]),
    required=True,
    help="Stage type",
)
@click.option(
    "--filter",
    "filters",
    multiple=True,
    type=click.Choice([t.name for t in FilterType]),
    help="Add filter to stage",
)
@click.option(
    "--input",
    "inputs",
    multiple=True,
    help="Add input stage",
)
@click.option(
    "--output",
    "outputs",
    multiple=True,
    help="Add output stage",
)
@click.option(
    "--settings",
    type=click.Path(exists=True, dir_okay=False),
    help="YAML file with stage settings",
)
@common_options
def add_stage(
    name: str,
    stage_name: str,
    type: str,
    filters: list[str],
    inputs: list[str],
    outputs: list[str],
    settings: Optional[str],
    **kwargs,
):
    """Add a stage to a pipeline."""
    pipelines = shell.config.get("pipelines", {})

    if name not in pipelines:
        click.echo(f"Pipeline '{name}' not found", err=True)
        return

    pipeline = pipelines[name]
    stages = pipeline.get("stages", [])

    # Check for duplicate stage name
    if any(s["name"] == stage_name for s in stages):
        click.echo(f"Stage '{stage_name}' already exists in pipeline", err=True)
        return

    # Create stage config
    stage_config = {
        "name": stage_name,
        "type": type,
        "enabled": True,
        "filters": [{"type": f, "enabled": True} for f in filters],
        "inputs": list(inputs),
        "outputs": list(outputs),
    }

    # Load additional settings
    if settings:
        with open(settings) as f:
            additional_settings = yaml.safe_load(f)
        stage_config.update(additional_settings)

    # Add stage
    stages.append(stage_config)
    pipeline["stages"] = stages

    # Validate updated pipeline
    try:
        PipelineConfig(**pipeline)
    except Exception as e:
        click.echo(f"Invalid pipeline configuration: {str(e)}", err=True)
        return

    shell.config["pipelines"] = pipelines
    click.echo(f"Stage '{stage_name}' added to pipeline '{name}'")


@pipelines_cli.command()
@click.argument("name")
@click.argument("stage_name")
@common_options
def remove_stage(name: str, stage_name: str, **kwargs):
    """Remove a stage from a pipeline."""
    pipelines = shell.config.get("pipelines", {})

    if name not in pipelines:
        click.echo(f"Pipeline '{name}' not found", err=True)
        return

    pipeline = pipelines[name]
    stages = pipeline.get("stages", [])

    # Find and remove stage
    for i, stage in enumerate(stages):
        if stage["name"] == stage_name:
            del stages[i]
            pipeline["stages"] = stages

            # Validate updated pipeline
            try:
                PipelineConfig(**pipeline)
            except Exception as e:
                click.echo(f"Invalid pipeline configuration: {str(e)}", err=True)
                return

            shell.config["pipelines"] = pipelines
            click.echo(f"Stage '{stage_name}' removed from pipeline '{name}'")
            return

    click.echo(f"Stage '{stage_name}' not found in pipeline", err=True)


@pipelines_cli.command()
@click.argument("name")
@common_options
def remove(name: str, **kwargs):
    """Remove a pipeline."""
    pipelines = shell.config.get("pipelines", {})

    if name not in pipelines:
        click.echo(f"Pipeline '{name}' not found", err=True)
        return

    del pipelines[name]
    shell.config["pipelines"] = pipelines

    click.echo(f"Pipeline '{name}' removed")


@pipelines_cli.command()
@click.argument("name")
@click.option(
    "--format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format",
)
@common_options
def show(name: str, format: str, **kwargs):
    """Show pipeline details."""
    pipelines = shell.config.get("pipelines", {})

    if name not in pipelines:
        click.echo(f"Pipeline '{name}' not found", err=True)
        return

    pipeline = pipelines[name]

    if format == "yaml":
        click.echo(yaml.dump(pipeline, default_flow_style=False))
    else:  # json
        import json

        click.echo(json.dumps(pipeline, indent=2))


@pipelines_cli.command()
@click.argument("name")
@click.option(
    "--format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format",
)
@common_options
def status(name: str, format: str, **kwargs):
    """Show pipeline status."""
    pipelines = shell.config.get("pipelines", {})

    if name not in pipelines:
        click.echo(f"Pipeline '{name}' not found", err=True)
        return

    pipeline = pipelines[name]
    status = pipeline.get("status", {})

    if format == "yaml":
        click.echo(yaml.dump(status, default_flow_style=False))
    else:  # json
        import json

        click.echo(json.dumps(status, indent=2))


@pipelines_cli.command()
@click.argument("name")
@common_options
def start(name: str, **kwargs):
    """Start a pipeline."""
    pipelines = shell.config.get("pipelines", {})

    if name not in pipelines:
        click.echo(f"Pipeline '{name}' not found", err=True)
        return

    click.echo(f"Starting pipeline '{name}'...")
    # TODO: Implement pipeline starting
    click.echo("Pipeline starting not implemented yet")


@pipelines_cli.command()
@click.argument("name")
@common_options
def stop(name: str, **kwargs):
    """Stop a pipeline."""
    pipelines = shell.config.get("pipelines", {})

    if name not in pipelines:
        click.echo(f"Pipeline '{name}' not found", err=True)
        return

    click.echo(f"Stopping pipeline '{name}'...")
    # TODO: Implement pipeline stopping
    click.echo("Pipeline stopping not implemented yet")


@pipelines_cli.command()
@click.argument("name")
@common_options
def validate(name: str, **kwargs):
    """Validate a pipeline configuration."""
    pipelines = shell.config.get("pipelines", {})

    if name not in pipelines:
        click.echo(f"Pipeline '{name}' not found", err=True)
        return

    pipeline = pipelines[name]

    try:
        PipelineConfig(**pipeline)
        click.echo(f"Pipeline '{name}' configuration is valid")
    except Exception as e:
        click.echo(f"Pipeline '{name}' configuration is invalid: {str(e)}", err=True)
