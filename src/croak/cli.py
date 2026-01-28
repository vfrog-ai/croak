"""CROAK Command Line Interface."""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from croak import __version__
from croak.core.config import CroakConfig
from croak.core.state import PipelineState

console = Console()


def get_croak_root() -> Optional[Path]:
    """Find CROAK project root (directory containing .croak/)."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".croak").exists():
            return current
        current = current.parent
    return None


def ensure_initialized():
    """Ensure CROAK is initialized in current directory."""
    root = get_croak_root()
    if root is None:
        console.print("[red]CROAK not initialized.[/red]")
        console.print("Run [cyan]croak init[/cyan] to initialize a new project.")
        sys.exit(1)
    return root


@click.group()
@click.version_option(version=__version__, prog_name="croak")
def main():
    """CROAK - Computer Recognition Orchestration Agent Kit

    An agentic framework for object detection model development.

    https://github.com/vfrog-ai/croak
    """
    pass


# ============================================================================
# Utility Commands
# ============================================================================


@main.command()
@click.option("--name", "-n", prompt="Project name", help="Name for the project")
def init(name: str):
    """Initialize CROAK in current directory."""
    croak_dir = Path.cwd() / ".croak"

    if croak_dir.exists():
        console.print("[yellow]CROAK already initialized in this directory.[/yellow]")
        return

    # Create directory structure
    directories = [
        ".croak",
        ".croak/logs",
        "data/raw",
        "data/annotations",
        "data/processed/images/train",
        "data/processed/images/val",
        "data/processed/images/test",
        "data/processed/labels/train",
        "data/processed/labels/val",
        "data/processed/labels/test",
        "training/configs",
        "training/scripts",
        "training/experiments",
        "evaluation/reports",
        "evaluation/visualizations",
        "deployment/cloud",
        "deployment/edge",
        "deployment/validation",
    ]

    for dir_path in directories:
        (Path.cwd() / dir_path).mkdir(parents=True, exist_ok=True)

    # Create config
    config = CroakConfig(
        project_name=name,
        created_at=datetime.utcnow().isoformat(),
    )
    config.save(croak_dir / "config.yaml")

    # Create initial state
    state = PipelineState(
        initialized_at=datetime.utcnow().isoformat(),
    )
    state.save(croak_dir / "pipeline-state.yaml")

    console.print(Panel.fit(
        f"[green]CROAK initialized![/green]\n\n"
        f"Project: [cyan]{name}[/cyan]\n"
        f"Directory: [cyan]{Path.cwd()}[/cyan]\n\n"
        "Next steps:\n"
        "1. Add images to [cyan]data/raw/[/cyan]\n"
        "2. Run [cyan]croak scan data/raw[/cyan]\n"
        "3. Follow the guided workflow",
        title="🐸 CROAK"
    ))


@main.command()
def status():
    """Show pipeline status."""
    root = ensure_initialized()
    state = PipelineState.load(root / ".croak" / "pipeline-state.yaml")
    config = CroakConfig.load(root / ".croak" / "config.yaml")

    # Build status display
    console.print(Panel.fit(
        f"[cyan]{config.project_name}[/cyan]",
        title="🐸 CROAK Pipeline Status"
    ))

    # Current stage
    stage_display = {
        "uninitialized": "Not started",
        "data_preparation": "Data Preparation",
        "training": "Training",
        "evaluation": "Evaluation",
        "deployment": "Deployment",
        "complete": "Complete",
    }

    console.print(f"\n[bold]Current Stage:[/bold] {stage_display.get(state.current_stage, state.current_stage)}")

    # Completed stages
    if state.stages_completed:
        console.print("\n[bold]Completed:[/bold]")
        for stage in state.stages_completed:
            console.print(f"  [green]✓[/green] {stage}")

    # Artifacts
    if state.artifacts.dataset.path:
        console.print(f"\n[bold]Dataset:[/bold] {state.artifacts.dataset.path}")
        if state.artifacts.dataset.classes:
            console.print(f"  Classes: {', '.join(state.artifacts.dataset.classes)}")

    if state.artifacts.model.path:
        console.print(f"\n[bold]Model:[/bold] {state.artifacts.model.path}")
        console.print(f"  Architecture: {state.artifacts.model.architecture}")

    # Warnings
    if state.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in state.warnings:
            console.print(f"  ⚠️ {warning}")

    # Next steps
    console.print("\n[bold]Next Steps:[/bold]")
    if state.current_stage == "uninitialized":
        console.print("  1. Add images to data/raw/")
        console.print("  2. Run: croak scan data/raw")
    elif "data_preparation" not in state.stages_completed:
        console.print("  Run: croak prepare")
    elif "training" not in state.stages_completed:
        console.print("  Run: croak train")
    elif "evaluation" not in state.stages_completed:
        console.print("  Run: croak evaluate")
    else:
        console.print("  Run: croak deploy")


@main.command()
def help():
    """Show available commands."""
    help_text = """
# CROAK Commands

## Data Preparation
- `croak scan <path>` - Discover images and annotations
- `croak validate` - Run data quality checks
- `croak annotate` - Start vfrog annotation workflow
- `croak split` - Create train/val/test splits
- `croak prepare` - Full data preparation pipeline

## Training
- `croak recommend` - Get architecture recommendation
- `croak configure` - Generate training config
- `croak estimate` - Estimate training time/cost
- `croak train` - Start training
- `croak resume` - Resume from checkpoint

## Evaluation
- `croak evaluate` - Run full evaluation
- `croak analyze` - Deep dive into failures
- `croak diagnose` - Figure out why model isn't working
- `croak report` - Generate evaluation report

## Deployment
- `croak export` - Export model (--format onnx|tensorrt)
- `croak deploy cloud` - Deploy to vfrog
- `croak deploy edge` - Deploy to edge device

## Utility
- `croak init` - Initialize new project
- `croak status` - Show pipeline state
- `croak help` - Show this help
- `croak reset` - Reset pipeline state
    """
    console.print(Markdown(help_text))


@main.command()
@click.confirmation_option(prompt="This will reset all pipeline state. Continue?")
def reset():
    """Reset pipeline state."""
    root = ensure_initialized()

    # Reset state
    state = PipelineState(
        initialized_at=datetime.utcnow().isoformat(),
    )
    state.save(root / ".croak" / "pipeline-state.yaml")

    console.print("[green]Pipeline state reset.[/green]")


# ============================================================================
# Data Commands
# ============================================================================


@main.command()
@click.argument("path", type=click.Path(exists=True))
def scan(path: str):
    """Scan directory for images and annotations."""
    root = ensure_initialized()

    from croak.data.scanner import scan_directory

    console.print(f"Scanning [cyan]{path}[/cyan]...")

    results = scan_directory(Path(path))

    # Display results
    table = Table(title="Scan Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Images", str(results["total_images"]))
    table.add_row("Formats", ", ".join(results["formats"].keys()))
    table.add_row("Existing Annotations", "Yes" if results["has_annotations"] else "No")

    console.print(table)

    if results["total_images"] < 100:
        console.print(
            "[yellow]Warning: Less than 100 images. "
            "Object detection typically needs 100+ images.[/yellow]"
        )

    console.print("\nNext: [cyan]croak validate[/cyan]")


@main.command()
def validate():
    """Validate data quality."""
    root = ensure_initialized()
    console.print("Validating data quality...")
    console.print("[yellow]This command will be fully implemented with the Data Agent.[/yellow]")


@main.command()
def annotate():
    """Start vfrog annotation workflow."""
    root = ensure_initialized()
    console.print("Starting vfrog annotation workflow...")
    console.print("[yellow]This command will be fully implemented with the Data Agent.[/yellow]")


@main.command()
@click.option("--train", default=0.8, help="Train split ratio")
@click.option("--val", default=0.15, help="Validation split ratio")
@click.option("--test", default=0.05, help="Test split ratio")
def split(train: float, val: float, test: float):
    """Create train/val/test splits."""
    root = ensure_initialized()
    console.print(f"Creating splits: {train}/{val}/{test}")
    console.print("[yellow]This command will be fully implemented with the Data Agent.[/yellow]")


@main.command()
def prepare():
    """Run full data preparation workflow."""
    root = ensure_initialized()
    console.print("Starting data preparation workflow...")
    console.print("[yellow]This command will be fully implemented with the Data Agent.[/yellow]")


# ============================================================================
# Training Commands
# ============================================================================


@main.command()
def recommend():
    """Get architecture recommendation."""
    root = ensure_initialized()
    console.print("Analyzing dataset for architecture recommendation...")
    console.print("[yellow]This command will be fully implemented with the Training Agent.[/yellow]")


@main.command()
def configure():
    """Generate training configuration."""
    root = ensure_initialized()
    console.print("Generating training configuration...")
    console.print("[yellow]This command will be fully implemented with the Training Agent.[/yellow]")


@main.command()
def estimate():
    """Estimate training time and cost."""
    root = ensure_initialized()
    console.print("Estimating training costs...")
    console.print("[yellow]This command will be fully implemented with the Training Agent.[/yellow]")


@main.command()
def train():
    """Start model training."""
    root = ensure_initialized()
    console.print("Starting training workflow...")
    console.print("[yellow]This command will be fully implemented with the Training Agent.[/yellow]")


@main.command()
def resume():
    """Resume training from checkpoint."""
    root = ensure_initialized()
    console.print("Resuming training...")
    console.print("[yellow]This command will be fully implemented with the Training Agent.[/yellow]")


# ============================================================================
# Evaluation Commands
# ============================================================================


@main.command()
def evaluate():
    """Run model evaluation."""
    root = ensure_initialized()
    console.print("Running evaluation...")
    console.print("[yellow]This command will be fully implemented with the Evaluation Agent.[/yellow]")


@main.command()
def analyze():
    """Analyze model errors."""
    root = ensure_initialized()
    console.print("Analyzing errors...")
    console.print("[yellow]This command will be fully implemented with the Evaluation Agent.[/yellow]")


@main.command()
def diagnose():
    """Diagnose model performance issues."""
    root = ensure_initialized()
    console.print("Diagnosing performance issues...")
    console.print("[yellow]This command will be fully implemented with the Evaluation Agent.[/yellow]")


@main.command()
def report():
    """Generate evaluation report."""
    root = ensure_initialized()
    console.print("Generating report...")
    console.print("[yellow]This command will be fully implemented with the Evaluation Agent.[/yellow]")


# ============================================================================
# Deployment Commands
# ============================================================================


@main.command()
@click.option("--format", "-f", type=click.Choice(["onnx", "tensorrt"]), default="onnx")
def export(format: str):
    """Export model to deployment format."""
    root = ensure_initialized()
    console.print(f"Exporting to {format}...")
    console.print("[yellow]This command will be fully implemented with the Deployment Agent.[/yellow]")


@main.group()
def deploy():
    """Deploy model to cloud or edge."""
    pass


@deploy.command()
def cloud():
    """Deploy to vfrog cloud."""
    root = ensure_initialized()
    console.print("Deploying to vfrog cloud...")
    console.print("[yellow]This command will be fully implemented with the Deployment Agent.[/yellow]")


@deploy.command()
def edge():
    """Deploy to edge device."""
    root = ensure_initialized()
    console.print("Preparing edge deployment...")
    console.print("[yellow]This command will be fully implemented with the Deployment Agent.[/yellow]")


if __name__ == "__main__":
    main()
