"""pruv CLI commands — scan, verify, export, undo, upload."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from xycore import XYChain, LocalStorage


@click.group()
@click.version_option(version="1.0.0", prog_name="pruv")
def cli():
    """pruv — Prove what happened."""
    pass


@cli.command()
@click.argument("directory", default=".")
@click.option("--output", "-o", help="Output file path")
@click.option("--json-output", is_flag=True, help="Output as JSON")
@click.option("--include-contents", is_flag=True, help="Include file contents")
def scan(directory: str, output: str | None, json_output: bool, include_contents: bool):
    """Scan a project directory."""
    from ..scanner import scan as do_scan

    graph = do_scan(directory, include_contents=include_contents)
    data = graph.to_dict()

    if json_output or output:
        result = json.dumps(data, indent=2)
        if output:
            Path(output).write_text(result)
            click.echo(f"Scan written to {output}")
        else:
            click.echo(result)
    else:
        click.echo(f"pruv scan: {directory}")
        click.echo(f"  Files: {len(data['files'])}")
        click.echo(f"  Lines: {data.get('total_lines', 0)}")
        click.echo(f"  Hash:  {data['hash']}")
        if data.get("frameworks"):
            fws = ", ".join(f["name"] for f in data["frameworks"])
            click.echo(f"  Frameworks: {fws}")
        if data.get("services"):
            svcs = ", ".join(s["name"] for s in data["services"])
            click.echo(f"  Services: {svcs}")
        if data.get("env_vars"):
            click.echo(f"  Env vars: {len(data['env_vars'])}")


@cli.command()
@click.argument("chain_file")
@click.option("--json-output", is_flag=True, help="Output as JSON")
def verify(chain_file: str, json_output: bool):
    """Verify a chain file."""
    path = Path(chain_file)
    if not path.exists():
        click.echo(f"Error: File not found: {chain_file}", err=True)
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    chain = XYChain.from_dict(data)
    valid, break_index = chain.verify()

    if json_output:
        result = {"valid": valid, "length": chain.length}
        if break_index is not None:
            result["break_index"] = break_index
        click.echo(json.dumps(result, indent=2))
    else:
        if valid:
            click.echo(f"Chain verified: {chain.length} entries, all valid")
        else:
            click.echo(f"Chain BROKEN at entry {break_index}")
            sys.exit(1)


@cli.command()
@click.argument("chain_file")
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "csv"]), default="json")
@click.option("--output", "-o", help="Output file")
def export(chain_file: str, fmt: str, output: str | None):
    """Export a chain to JSON or CSV."""
    path = Path(chain_file)
    if not path.exists():
        click.echo(f"Error: File not found: {chain_file}", err=True)
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    chain = XYChain.from_dict(data)

    if fmt == "json":
        result = json.dumps(chain.to_dict(), indent=2)
    else:
        lines = ["index,timestamp,operation,x,y,xy,status"]
        for entry in chain.entries:
            lines.append(
                f"{entry.index},{entry.timestamp},{entry.operation},"
                f"{entry.x},{entry.y},{entry.xy},{entry.status}"
            )
        result = "\n".join(lines)

    if output:
        Path(output).write_text(result)
        click.echo(f"Exported to {output}")
    else:
        click.echo(result)


@cli.command()
@click.option("--chain", "chain_id", required=True, help="Chain ID")
@click.option("--last", is_flag=True, help="Undo to last checkpoint")
@click.option("--to", "to_checkpoint", help="Checkpoint ID to restore to")
@click.option("--preview", is_flag=True, help="Preview only, don't restore")
@click.option("--storage-dir", default=".pruv", help="Storage directory")
def undo(chain_id: str, last: bool, to_checkpoint: str | None, preview: bool, storage_dir: str):
    """Undo to a checkpoint."""
    storage = LocalStorage(storage_dir)
    try:
        chain = storage.load(chain_id)
    except FileNotFoundError:
        click.echo(f"Error: Chain not found: {chain_id}", err=True)
        sys.exit(1)

    from ..checkpoint import CheckpointManager

    manager = CheckpointManager(chain, storage_dir=f"{storage_dir}/checkpoints")

    if preview and to_checkpoint:
        result = manager.preview_restore(to_checkpoint)
        click.echo(json.dumps(result.to_dict(), indent=2))
    elif last:
        restored = manager.quick_undo()
        if restored:
            storage.save(restored)
            click.echo("Restored to last checkpoint")
        else:
            click.echo("No checkpoints found")
    elif to_checkpoint:
        restored = manager.restore(to_checkpoint)
        storage.save(restored)
        click.echo(f"Restored to checkpoint {to_checkpoint}")
    else:
        click.echo("Specify --last or --to <checkpoint_id>")


@cli.command()
@click.argument("directory", default=".")
@click.option("--api-key", envvar="PRUV_API_KEY", help="pruv API key")
def upload(directory: str, api_key: str | None):
    """Upload a project scan to the cloud."""
    if not api_key:
        click.echo("Error: API key required. Set PRUV_API_KEY or use --api-key", err=True)
        sys.exit(1)

    import asyncio
    from ..scanner import scan as do_scan
    from ..cloud import CloudClient

    graph = do_scan(directory)

    async def _upload():
        chain = XYChain(name=f"scan-{Path(directory).resolve().name}")
        chain.append("scan", y_state=graph.to_state_dict())

        client = CloudClient(api_key=api_key)
        result = await client.upload_chain(chain)
        return result

    result = asyncio.run(_upload())
    if result:
        click.echo(f"Uploaded: chain {result.get('id', 'unknown')}")
    else:
        click.echo("Upload failed (queued for retry)")


def main():
    cli()
