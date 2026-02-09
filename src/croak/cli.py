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
from rich.progress import Progress, SpinnerColumn, TextColumn

from croak import __version__
from croak.core.config import CroakConfig
from croak.core.state import PipelineState, load_state

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
        ".croak/handoffs",
        ".croak/evaluations",
        ".croak/exports",
        ".croak/deployments",
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
        "exports",
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
@click.option("--fix", is_flag=True, help="Attempt automatic fixes for issues found")
def doctor(fix):
    """Check environment and dependencies."""
    console.print(Panel.fit(
        "[bold]Environment Check[/bold]",
        title="🔍 CROAK Doctor"
    ))

    issues = []
    warnings_list = []

    # --- Python Environment ---
    console.print("\n[bold]Python Environment[/bold]")
    console.print("[dim]" + "─" * 40 + "[/dim]")

    import platform
    py_version = platform.python_version()
    py_ok = sys.version_info >= (3, 10)
    _doctor_check("Python " + py_version, py_ok)
    if not py_ok:
        issues.append("Python 3.10+ required")

    # Check key packages
    for pkg_name, required in [
        ("ultralytics", True), ("torch", True), ("modal", False),
        ("pydantic", True), ("pyyaml", True), ("rich", True),
    ]:
        try:
            __import__(pkg_name.replace("-", "_"))
            _doctor_check(f"  {pkg_name}", True)
        except ImportError:
            label = "required" if required else "optional"
            _doctor_check(f"  {pkg_name}", False, label)
            if required:
                issues.append(f"Missing required package: {pkg_name}")
            else:
                warnings_list.append(f"Optional package not installed: {pkg_name}")

    # --- GPU ---
    console.print("\n[bold]GPU & Compute[/bold]")
    console.print("[dim]" + "─" * 40 + "[/dim]")

    try:
        import subprocess
        gpu_result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if gpu_result.returncode == 0:
            parts = gpu_result.stdout.strip().split(", ")
            gpu_name = parts[0].strip() if parts else "Unknown"
            vram_mb = int(parts[1].strip()) if len(parts) > 1 else 0
            vram_gb = vram_mb / 1024
            _doctor_check(f"NVIDIA GPU ({gpu_name})", True)
            _doctor_check(f"  VRAM: {vram_gb:.1f}GB", vram_gb >= 8)
            if vram_gb < 8:
                warnings_list.append("GPU VRAM < 8GB -- may need cloud GPU for larger models")
        else:
            _doctor_check("Local NVIDIA GPU", False, "optional")
            console.print("[dim]    Will use Modal.com or vfrog for GPU training[/dim]")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        _doctor_check("Local NVIDIA GPU", False, "optional")
        console.print("[dim]    Will use Modal.com or vfrog for GPU training[/dim]")

    # Modal
    try:
        import subprocess
        modal_result = subprocess.run(
            ["modal", "token", "show"], capture_output=True, text=True, timeout=10
        )
        modal_ok = "Token" in modal_result.stdout or "authenticated" in modal_result.stdout
        _doctor_check("Modal.com configured", modal_ok)
        if not modal_ok:
            warnings_list.append("Modal.com not configured. Run `modal setup` for cloud GPU.")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        _doctor_check("Modal.com SDK", False, "recommended")
        warnings_list.append("Modal.com not available. Run `pip install modal && modal setup`.")

    # --- vfrog CLI ---
    console.print("\n[bold]vfrog Integration[/bold]")
    console.print("[dim]" + "─" * 40 + "[/dim]")

    from croak.integrations.vfrog import VfrogCLI

    vfrog_installed = VfrogCLI.check_installed()
    if vfrog_installed:
        _doctor_check("vfrog CLI", True)

        vfrog_auth = VfrogCLI.check_authenticated()
        _doctor_check("  Authenticated", vfrog_auth)
        if not vfrog_auth:
            warnings_list.append("vfrog not authenticated. Run `croak vfrog setup`.")

        config_result = VfrogCLI.get_config()
        if config_result["success"] and isinstance(config_result["output"], dict):
            cfg = config_result["output"]
            org_set = bool(cfg.get("organisation_id"))
            proj_set = bool(cfg.get("project_id"))
            _doctor_check("  Organisation set", org_set)
            _doctor_check("  Project set", proj_set)
            if not org_set or not proj_set:
                warnings_list.append("vfrog context incomplete. Run `croak vfrog setup`.")
        else:
            _doctor_check("  Context", False)
            warnings_list.append("Could not read vfrog config.")

        # API key for inference
        import os
        api_key_set = bool(os.environ.get("VFROG_API_KEY"))
        _doctor_check("  API key (inference)", api_key_set, "optional")
        if not api_key_set:
            warnings_list.append("VFROG_API_KEY not set. Needed for vfrog inference.")
    else:
        _doctor_check("vfrog CLI", False, "recommended")
        warnings_list.append("vfrog CLI not installed. Download: https://github.com/vfrog/vfrog-cli/releases")

    # --- Project Status ---
    console.print("\n[bold]Project Status[/bold]")
    console.print("[dim]" + "─" * 40 + "[/dim]")

    root = get_croak_root()
    if root:
        _doctor_check("CROAK initialized", True)
        config_exists = (root / ".croak" / "config.yaml").exists()
        _doctor_check("  Configuration file", config_exists)
        if not config_exists:
            issues.append("Missing config.yaml")
        state_exists = (root / ".croak" / "pipeline-state.yaml").exists()
        _doctor_check("  Pipeline state file", state_exists)
        if not state_exists:
            warnings_list.append("Missing pipeline-state.yaml")
        agents_exist = (root / ".croak" / "agents").exists() or (root / "agents").exists()
        _doctor_check("  Agent definitions", agents_exist)
        if not agents_exist:
            issues.append("Missing agents directory")
    else:
        _doctor_check("CROAK initialized", False)
        issues.append("CROAK not initialized. Run `croak init` first.")

    # --- Summary ---
    console.print("\n[bold]Summary[/bold]")
    console.print("[dim]" + "─" * 40 + "[/dim]")

    if not issues and not warnings_list:
        console.print("\n[green]All checks passed! Your environment is ready.[/green]\n")
    else:
        if issues:
            console.print(f"\n[red]{len(issues)} issue(s) found:[/red]")
            for issue in issues:
                console.print(f"  [red]• {issue}[/red]")
        if warnings_list:
            console.print(f"\n[yellow]{len(warnings_list)} warning(s):[/yellow]")
            for warning in warnings_list:
                console.print(f"  [yellow]• {warning}[/yellow]")
        console.print("")

    if fix and issues:
        console.print("[cyan]Attempting automatic fixes...[/cyan]\n")
        import subprocess
        for issue in issues:
            if "Missing required package:" in issue:
                pkg = issue.split(": ")[1]
                console.print(f"  Installing {pkg}...")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", pkg],
                                   capture_output=True, check=True)
                    console.print(f"  [green]Installed {pkg}[/green]")
                except subprocess.CalledProcessError:
                    console.print(f"  [red]Failed to install {pkg}[/red]")

    if issues:
        sys.exit(1)


def _doctor_check(label: str, passed: bool, optional: str = None):
    """Print a doctor check result."""
    if passed:
        icon = "[green]✓[/green]"
    elif optional:
        icon = "[yellow]○[/yellow]"
    else:
        icon = "[red]✗[/red]"
    suffix = f" [dim]({optional})[/dim]" if optional and not passed else ""
    console.print(f"  {icon} {label}{suffix}")


@main.command()
def help():
    """Show available commands."""
    help_text = """
# CROAK Commands

## Setup
- `croak init` - Initialize new project
- `croak vfrog setup` - Login and configure vfrog platform
- `croak vfrog status` - Show vfrog connection status
- `croak status` - Show pipeline state
- `croak doctor` - Check environment and dependencies

## Data Preparation
- `croak scan <path>` - Discover images and annotations
- `croak validate` - Run data quality checks
- `croak annotate` - Annotate images (two methods):
  - `--method vfrog` (default) - vfrog SSAT auto-annotation
  - `--method classic` - Import from CVAT, Label Studio, etc.
- `croak split` - Create train/val/test splits
- `croak prepare` - Full data preparation pipeline

## Training
- `croak recommend` - Get architecture recommendation
- `croak configure` - Generate training config
- `croak estimate` - Estimate training time/cost
- `croak train` - Start training (three providers):
  - `--provider local` (default) - Train on local GPU
  - `--provider modal` - Train on Modal.com serverless GPU
  - `--provider vfrog` - Train on vfrog platform
- `croak resume` - Resume from checkpoint

## Evaluation
- `croak evaluate` - Run full evaluation
- `croak analyze` - Deep dive into failures
- `croak diagnose` - Figure out why model isn't working
- `croak report` - Generate evaluation report

## Deployment
- `croak export` - Export model (--format onnx|tensorrt|coreml|tflite)
- `croak deploy modal` - Deploy to Modal.com endpoint
- `croak deploy vfrog` - Test vfrog inference endpoint
- `croak deploy edge` - Package for edge deployment

## Utility
- `croak next` - Show suggested next step
- `croak history` - Show pipeline history
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


@main.command()
def next():
    """Suggest the next step based on pipeline state."""
    root = ensure_initialized()
    state = PipelineState.load(root / ".croak" / "pipeline-state.yaml")
    config = CroakConfig.load(root / ".croak" / "config.yaml")

    console.print(Panel.fit(
        f"[cyan]{config.project_name}[/cyan]",
        title="🐸 CROAK - Next Step"
    ))

    # Determine next step based on current stage
    if state.current_stage == "uninitialized":
        console.print("\n[bold]Your next step:[/bold] Add data and scan it\n")
        console.print("1. Add images to [cyan]data/raw/[/cyan]")
        console.print("2. Run: [cyan]croak scan data/raw[/cyan]")
        console.print("\nThis will discover your images and detect any existing annotations.")

    elif state.current_stage == "data_preparation" or "data_preparation" not in state.stages_completed:
        # Check what's been done in data preparation
        has_scan = (root / "data" / "raw").exists() and any((root / "data" / "raw").iterdir()) if (root / "data" / "raw").exists() else False

        if not has_scan:
            console.print("\n[bold]Your next step:[/bold] Scan your data\n")
            console.print("Run: [cyan]croak scan data/raw[/cyan]")
        elif not state.data_yaml_path:
            console.print("\n[bold]Your next step:[/bold] Prepare your data\n")
            console.print("Run: [cyan]croak prepare[/cyan]")
            console.print("\nThis will validate your data and create train/val/test splits.")
        else:
            console.print("\n[bold]Your next step:[/bold] Start training\n")
            console.print("Run: [cyan]croak train[/cyan]")

    elif state.current_stage == "training" or "training" not in state.stages_completed:
        if state.artifacts.model.path:
            console.print("\n[bold]Your next step:[/bold] Evaluate your model\n")
            console.print("Run: [cyan]croak evaluate[/cyan]")
        else:
            console.print("\n[bold]Your next step:[/bold] Train your model\n")
            console.print("1. (Optional) Get architecture recommendation: [cyan]croak recommend[/cyan]")
            console.print("2. (Optional) Estimate training cost: [cyan]croak estimate[/cyan]")
            console.print("3. Start training:")
            console.print("   • Local GPU: [cyan]croak train --provider local[/cyan]")
            console.print("   • Modal.com: [cyan]croak train --provider modal[/cyan]")
            console.print("   • vfrog platform: [cyan]croak train --provider vfrog[/cyan]")

    elif state.current_stage == "evaluation" or "evaluation" not in state.stages_completed:
        console.print("\n[bold]Your next step:[/bold] Evaluate your model\n")
        console.print("Run: [cyan]croak evaluate[/cyan]")
        console.print("\nThis will compute metrics like mAP, precision, and recall.")

    elif state.current_stage == "deployment" or "deployment" not in state.stages_completed:
        console.print("\n[bold]Your next step:[/bold] Deploy your model\n")
        console.print("Options:")
        console.print("  • Export model: [cyan]croak export --format onnx[/cyan]")
        console.print("  • Deploy to Modal.com: [cyan]croak deploy modal[/cyan]")
        console.print("  • Test vfrog inference: [cyan]croak deploy vfrog --image <path>[/cyan]")
        console.print("  • Package for edge: [cyan]croak deploy edge[/cyan]")

    else:
        console.print("\n[green]✓ Pipeline complete![/green]")
        console.print("\nYour model is trained, evaluated, and ready for deployment.")
        console.print("\nYou can:")
        console.print("  • Re-evaluate: [cyan]croak evaluate[/cyan]")
        console.print("  • Export to new format: [cyan]croak export --format <format>[/cyan]")
        console.print("  • Deploy: [cyan]croak deploy modal|vfrog|edge[/cyan]")
        console.print("  • Start fresh: [cyan]croak reset[/cyan]")


@main.command()
def history():
    """Show completed pipeline stages and timestamps."""
    root = ensure_initialized()
    state = PipelineState.load(root / ".croak" / "pipeline-state.yaml")
    config = CroakConfig.load(root / ".croak" / "config.yaml")

    console.print(Panel.fit(
        f"[cyan]{config.project_name}[/cyan]",
        title="🐸 CROAK - Pipeline History"
    ))

    if state.initialized_at:
        console.print(f"\n[bold]Initialized:[/bold] {state.initialized_at}")

    if state.last_updated:
        console.print(f"[bold]Last Updated:[/bold] {state.last_updated}")

    # Show stage history if available
    if state.stage_history:
        console.print("\n[bold]Stage History:[/bold]")
        table = Table()
        table.add_column("Stage", style="cyan")
        table.add_column("Completed At", style="green")
        table.add_column("Duration", style="yellow")

        for entry in state.stage_history:
            duration = ""
            if entry.duration_seconds:
                if entry.duration_seconds < 60:
                    duration = f"{entry.duration_seconds:.1f}s"
                elif entry.duration_seconds < 3600:
                    duration = f"{entry.duration_seconds / 60:.1f}m"
                else:
                    duration = f"{entry.duration_seconds / 3600:.1f}h"
            table.add_row(entry.stage, entry.completed_at, duration)

        console.print(table)

    elif state.stages_completed:
        # Fallback to simple list if no detailed history
        console.print("\n[bold]Completed Stages:[/bold]")
        for stage in state.stages_completed:
            console.print(f"  [green]✓[/green] {stage}")

    else:
        console.print("\n[dim]No stages completed yet.[/dim]")

    # Show experiments if any
    if state.experiments:
        console.print("\n[bold]Experiments:[/bold]")
        table = Table()
        table.add_column("ID", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Architecture", style="yellow")
        table.add_column("Started", style="dim")

        for exp in state.experiments:
            status_style = {
                "completed": "[green]completed[/green]",
                "running": "[yellow]running[/yellow]",
                "failed": "[red]failed[/red]",
                "pending": "[dim]pending[/dim]",
            }.get(exp.status, exp.status)

            table.add_row(
                exp.id,
                status_style,
                exp.architecture or "-",
                exp.started or "-"
            )

        console.print(table)

    console.print(f"\n[bold]Current Stage:[/bold] {state.current_stage}")


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
@click.option("--path", "-p", default="data/processed", help="Dataset path to validate")
def validate(path: str):
    """Validate data quality."""
    root = ensure_initialized()

    from croak.data.validator import DataValidator

    console.print(f"Validating dataset at [cyan]{path}[/cyan]...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running validation checks...", total=None)

        validator = DataValidator(root / path)
        result = validator.validate_all()

        progress.update(task, completed=True)

    # Display results
    if result.is_valid:
        console.print("\n[green]✓ Dataset validation passed![/green]")
    else:
        console.print("\n[red]✗ Dataset validation failed[/red]")

    # Show errors
    if result.errors:
        console.print("\n[red]Errors:[/red]")
        for error in result.errors:
            console.print(f"  • {error}")

    # Show warnings
    if result.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  • {warning}")

    # Show statistics
    if result.statistics:
        console.print("\n[bold]Statistics:[/bold]")
        stats = result.statistics
        if "total_images" in stats:
            console.print(f"  Total images: {stats['total_images']}")
        if "total_annotations" in stats:
            console.print(f"  Total annotations: {stats['total_annotations']}")
        if "class_distribution" in stats:
            console.print("  Class distribution:")
            for cls, count in stats["class_distribution"].items():
                console.print(f"    {cls}: {count}")

    console.print("\nNext: [cyan]croak split[/cyan]")


@main.command()
@click.option("--method", type=click.Choice(["vfrog", "classic"]), default="vfrog",
              help="Annotation method: vfrog (SSAT auto-annotation) or classic (import from external tools)")
@click.option("--iteration-id", default=None, help="Resume existing vfrog iteration (vfrog only)")
@click.option("--object-id", default=None, help="Target vfrog object for iteration (vfrog only)")
@click.option("--random", "random_count", type=int, default=20,
              help="Random dataset images for SSAT (vfrog only)")
@click.option("--status", "check_status", is_flag=True, help="Check annotation status only")
@click.option("--halo", is_flag=True, help="Open HALO URL for review (vfrog only)")
@click.option("--format", "ann_format", type=click.Choice(["yolo", "coco", "voc"]),
              default="yolo", help="Annotation format (classic only)")
@click.option("--annotations-path", default=None, type=click.Path(),
              help="Path to annotation files (classic only)")
def annotate(method, iteration_id, object_id, random_count, check_status, halo,
             ann_format, annotations_path):
    """Annotate dataset images.

    Two methods available:

    \b
    vfrog (default): Auto-annotation via vfrog SSAT. Handles annotation and
    iterative refinement on the platform. Recommended for ease of use.

    \b
    classic: Import annotations from external tools (CVAT, Label Studio,
    Roboflow, etc.) in YOLO, COCO, or VOC format.
    """
    root = ensure_initialized()

    if method == "vfrog":
        _annotate_vfrog(root, iteration_id, object_id, random_count, check_status, halo)
    else:
        _annotate_classic(root, ann_format, annotations_path)


def _annotate_vfrog(root, iteration_id, object_id, random_count, check_status, halo):
    """vfrog SSAT annotation workflow."""
    from croak.integrations.vfrog import VfrogCLI

    # 1. Verify vfrog CLI is installed and authenticated
    if not VfrogCLI.check_installed():
        console.print("[red]vfrog CLI not installed.[/red]")
        console.print("Install from: [cyan]https://github.com/vfrog/vfrog-cli/releases[/cyan]")
        return

    if not VfrogCLI.check_authenticated():
        console.print("[red]Not logged in to vfrog.[/red]")
        console.print("Run: [cyan]croak vfrog setup[/cyan]")
        return

    # 2. Verify context is set
    config_result = VfrogCLI.get_config()
    if config_result['success'] and isinstance(config_result['output'], dict):
        cfg = config_result['output']
        if not cfg.get('project_id'):
            console.print("[red]No vfrog project selected.[/red]")
            console.print("Run: [cyan]croak vfrog setup[/cyan]")
            return
    else:
        console.print("[red]Could not read vfrog config.[/red]")
        return

    # Handle --halo: just show HALO URL
    if halo:
        if not iteration_id:
            console.print("[red]--iteration-id required with --halo[/red]")
            return
        result = VfrogCLI.get_halo_url(iteration_id)
        if result['success']:
            url = result['output'] if isinstance(result['output'], str) else result.get('raw', '')
            if isinstance(result['output'], dict):
                url = result['output'].get('url', result['output'].get('halo_url', str(result['output'])))
            console.print(f"\nHALO Review URL: [cyan]{url}[/cyan]")
            console.print("Open this URL in your browser to review and correct annotations.")
        else:
            console.print(f"[red]Failed to get HALO URL: {result.get('error')}[/red]")
        return

    # Handle --status: check annotation status
    if check_status:
        iters_result = VfrogCLI.list_iterations(object_id)
        if iters_result['success'] and isinstance(iters_result['output'], list):
            table = Table(title="vfrog Iterations")
            table.add_column("ID", style="cyan", max_width=36)
            table.add_column("#", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Trained", style="dim")

            for it in iters_result['output']:
                table.add_row(
                    str(it.get('id', '')),
                    str(it.get('iteration_number', '')),
                    str(it.get('status', '')),
                    str(it.get('trained_status', '-')),
                )
            console.print(table)
        else:
            console.print(f"[yellow]No iterations found or error: {iters_result.get('error')}[/yellow]")
        return

    # Full SSAT workflow
    console.print(Panel.fit(
        "[bold]vfrog SSAT Annotation Workflow[/bold]\n\n"
        "vfrog uses Semi-Supervised Active Training (SSAT) to auto-annotate\n"
        "your images. Each iteration improves on the last.\n\n"
        "Steps: Upload images → Create object → Run SSAT → Review in HALO",
        title="🐸 Annotation"
    ))

    # If resuming an existing iteration
    if iteration_id:
        console.print(f"\nResuming iteration: [cyan]{iteration_id}[/cyan]")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Running SSAT auto-annotation...", total=None)
            result = VfrogCLI.run_ssat(iteration_id, random_count=random_count)
            progress.update(task, completed=True)

        if result['success']:
            console.print("[green]✓ SSAT complete[/green]")
            halo_result = VfrogCLI.get_halo_url(iteration_id)
            if halo_result['success']:
                url = halo_result['output']
                if isinstance(url, dict):
                    url = url.get('url', url.get('halo_url', str(url)))
                console.print(f"\nReview annotations in HALO: [cyan]{url}[/cyan]")
        else:
            console.print(f"[red]SSAT failed: {result.get('error')}[/red]")
        return

    # New annotation workflow
    # Step 1: Check for dataset images
    images_result = VfrogCLI.list_dataset_images()
    image_count = 0
    if images_result['success'] and isinstance(images_result['output'], list):
        image_count = len(images_result['output'])

    if image_count == 0:
        console.print("\n[yellow]No dataset images uploaded yet.[/yellow]")
        console.print("Upload images first:")
        console.print("  [cyan]vfrog dataset_images upload <url1> <url2> ...[/cyan]")
        console.print("\nNote: vfrog requires image URLs (not local files).")
        console.print("Host your images on S3, GCS, or any public URL first.")
        return

    console.print(f"\n[green]✓[/green] {image_count} dataset images found")

    # Step 2: Check for objects or create one
    objects_result = VfrogCLI.list_objects()
    objects = objects_result['output'] if objects_result['success'] and isinstance(objects_result['output'], list) else []

    if not objects and not object_id:
        console.print("\n[yellow]No objects (product images) found.[/yellow]")
        console.print("Create an object first with:")
        console.print("  [cyan]vfrog objects create <product_image_url> --label <name>[/cyan]")
        console.print("\nThe object is the reference image of what you want to detect.")
        return

    if object_id:
        target_object_id = object_id
    else:
        target_object_id = objects[0].get('id', '')
        label = objects[0].get('label', 'unknown')
        console.print(f"Using object: [cyan]{label}[/cyan] ({target_object_id[:8]}...)")

    # Step 3: Create iteration
    console.print(f"\nCreating iteration with {random_count} random images...")
    iter_result = VfrogCLI.create_iteration(target_object_id, random_count=random_count)
    if not iter_result['success']:
        console.print(f"[red]Failed to create iteration: {iter_result.get('error')}[/red]")
        return

    new_iteration_id = ''
    if isinstance(iter_result['output'], dict):
        new_iteration_id = iter_result['output'].get('id', '')
    console.print(f"[green]✓[/green] Iteration created: {new_iteration_id[:8]}...")

    # Step 4: Run SSAT
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Running SSAT auto-annotation...", total=None)
        ssat_result = VfrogCLI.run_ssat(new_iteration_id)
        progress.update(task, completed=True)

    if not ssat_result['success']:
        console.print(f"[red]SSAT failed: {ssat_result.get('error')}[/red]")
        return

    console.print("[green]✓ SSAT auto-annotation complete[/green]")

    # Step 5: Show HALO URL
    halo_result = VfrogCLI.get_halo_url(new_iteration_id)
    if halo_result['success']:
        url = halo_result['output']
        if isinstance(url, dict):
            url = url.get('url', url.get('halo_url', str(url)))
        console.print(f"\n[bold]Review your annotations in HALO:[/bold]")
        console.print(f"  [cyan]{url}[/cyan]")
        console.print("\nAfter reviewing, you can:")
        console.print(f"  • Train on vfrog: [cyan]croak train --provider vfrog[/cyan]")
        console.print(f"  • Next iteration: [cyan]croak annotate --iteration-id {new_iteration_id}[/cyan]")

    # Update pipeline state
    state = load_state(root)
    state.annotation.source = "vfrog"
    state.annotation.method = "ssat"
    state.annotation.vfrog_iteration_id = new_iteration_id
    state.annotation.vfrog_object_id = target_object_id
    state.save(root / ".croak" / "pipeline-state.yaml")


def _annotate_classic(root, ann_format, annotations_path):
    """Classic annotation import workflow."""
    console.print(Panel.fit(
        "[bold]Classic Annotation Import[/bold]\n\n"
        "Import annotations from external tools in YOLO, COCO, or VOC format.\n"
        "Use this if you've annotated with CVAT, Label Studio, Roboflow, etc.",
        title="🐸 Annotation"
    ))

    # Check for images
    data_dir = root / "data"
    raw_dir = data_dir / "raw"
    if raw_dir.exists():
        image_count = sum(1 for f in raw_dir.rglob("*") if f.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'})
    else:
        image_count = 0

    if image_count == 0:
        console.print("\n[yellow]No images found in data/raw/[/yellow]")
        console.print("Add images first, then annotate them with your preferred tool.")
        return

    console.print(f"\n[green]✓[/green] {image_count} images found in data/raw/")

    # Guide user to annotation path
    if not annotations_path:
        console.print("\n[bold]Supported annotation tools:[/bold]")
        console.print("  • CVAT (export as YOLO or COCO)")
        console.print("  • Label Studio (export as YOLO)")
        console.print("  • Roboflow (export as YOLOv8)")
        console.print("  • LabelImg (saves in YOLO or VOC)")
        console.print("  • Any tool that exports YOLO, COCO, or VOC format")
        console.print(f"\nExpected format: [cyan]{ann_format.upper()}[/cyan]")
        console.print("")

        annotations_path = click.prompt(
            "Path to annotation files",
            type=click.Path(exists=True),
        )

    ann_path = Path(annotations_path)
    if not ann_path.exists():
        console.print(f"[red]Path not found: {annotations_path}[/red]")
        return

    # Count annotation files
    if ann_format == "yolo":
        ann_files = list(ann_path.rglob("*.txt"))
    elif ann_format == "coco":
        ann_files = list(ann_path.rglob("*.json"))
    elif ann_format == "voc":
        ann_files = list(ann_path.rglob("*.xml"))
    else:
        ann_files = []

    if not ann_files:
        console.print(f"[red]No {ann_format.upper()} annotation files found in {annotations_path}[/red]")
        return

    console.print(f"[green]✓[/green] Found {len(ann_files)} {ann_format.upper()} annotation files")

    # Copy annotations to data/annotations/
    import shutil
    dest = data_dir / "annotations"
    dest.mkdir(parents=True, exist_ok=True)

    copied = 0
    for f in ann_files:
        shutil.copy2(f, dest / f.name)
        copied += 1

    console.print(f"[green]✓[/green] Copied {copied} annotation files to data/annotations/")

    # Update state
    state = load_state(root)
    state.annotation.source = "classic"
    state.annotation.method = "manual"
    state.annotation.format = ann_format
    state.save(root / ".croak" / "pipeline-state.yaml")

    console.print(Panel.fit(
        "[green]Annotations imported![/green]\n\n"
        f"Format: [cyan]{ann_format.upper()}[/cyan]\n"
        f"Files: [cyan]{copied}[/cyan]\n\n"
        "Next steps:\n"
        "  1. Validate: [cyan]croak validate[/cyan]\n"
        "  2. Split: [cyan]croak split[/cyan]\n"
        "  3. Train: [cyan]croak train --provider local[/cyan]",
        title="🐸 CROAK"
    ))


@main.command()
@click.option("--train", default=0.8, help="Train split ratio")
@click.option("--val", default=0.15, help="Validation split ratio")
@click.option("--test", default=0.05, help="Test split ratio")
@click.option("--seed", default=42, help="Random seed for reproducibility")
@click.option("--stratify/--no-stratify", default=True, help="Stratify by class")
@click.option("--input", "-i", default="data/processed", help="Input dataset path")
def split(train: float, val: float, test: float, seed: int, stratify: bool, input: str):
    """Create train/val/test splits."""
    root = ensure_initialized()

    from croak.data.splitter import DatasetSplitter

    console.print(f"Creating splits: [cyan]{train}/{val}/{test}[/cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Splitting dataset...", total=None)

        splitter = DatasetSplitter(root / input)
        result = splitter.split(
            train_ratio=train,
            val_ratio=val,
            test_ratio=test,
            seed=seed,
            stratify=stratify,
        )

        progress.update(task, completed=True)

    if result.get("success"):
        console.print("\n[green]✓ Dataset split complete![/green]")

        table = Table(title="Split Results")
        table.add_column("Split", style="cyan")
        table.add_column("Images", style="green")

        for split_name, count in result.get("splits", {}).items():
            table.add_row(split_name, str(count))

        console.print(table)

        if result.get("data_yaml_path"):
            console.print(f"\ndata.yaml created: [cyan]{result['data_yaml_path']}[/cyan]")
    else:
        console.print(f"\n[red]Split failed: {result.get('error', 'Unknown error')}[/red]")

    console.print("\nNext: [cyan]croak train[/cyan]")


@main.command()
def prepare():
    """Run full data preparation workflow."""
    root = ensure_initialized()

    console.print("[bold]Starting full data preparation workflow...[/bold]\n")

    # Run validation
    console.print("[cyan]Step 1: Validating dataset...[/cyan]")
    from croak.data.validator import DataValidator

    validator = DataValidator(root / "data/processed")
    result = validator.validate_all()

    if not result.is_valid:
        console.print("[red]Validation failed. Please fix errors before continuing.[/red]")
        for error in result.errors:
            console.print(f"  • {error}")
        return

    console.print("[green]✓ Validation passed[/green]\n")

    # Run split
    console.print("[cyan]Step 2: Creating data splits...[/cyan]")
    from croak.data.splitter import DatasetSplitter

    splitter = DatasetSplitter(root / "data/processed")
    split_result = splitter.split()

    if not split_result.get("success"):
        console.print(f"[red]Split failed: {split_result.get('error')}[/red]")
        return

    console.print("[green]✓ Splits created[/green]\n")

    # Update state
    state = load_state(root)
    state.current_stage = "training"
    state.stages_completed.append("data_preparation")
    state.data_yaml_path = split_result.get("data_yaml_path")
    state.save(root / ".croak" / "pipeline-state.yaml")

    console.print(Panel.fit(
        "[green]Data preparation complete![/green]\n\n"
        f"data.yaml: [cyan]{split_result.get('data_yaml_path')}[/cyan]\n\n"
        "Next: [cyan]croak train[/cyan]",
        title="🐸 CROAK"
    ))


# ============================================================================
# Training Commands
# ============================================================================


@main.command()
def recommend():
    """Get architecture recommendation."""
    root = ensure_initialized()
    state = load_state(root)

    from croak.training.trainer import TrainingOrchestrator

    console.print("Analyzing dataset for architecture recommendation...\n")

    orchestrator = TrainingOrchestrator(root)
    config = orchestrator.prepare_training()

    if not config.get("success", True):
        console.print(f"[red]Error: {config.get('error')}[/red]")
        return

    console.print(Panel.fit(
        f"[bold]Recommended Architecture:[/bold] [cyan]{config.get('architecture', 'yolov8s')}[/cyan]\n\n"
        f"[bold]Configuration:[/bold]\n"
        f"  Epochs: {config.get('epochs', 100)}\n"
        f"  Batch size: {config.get('batch_size', 16)}\n"
        f"  Image size: {config.get('imgsz', 640)}\n"
        f"  Learning rate: {config.get('lr0', 0.01)}\n",
        title="🐸 Architecture Recommendation"
    ))


@main.command()
def configure():
    """Generate training configuration."""
    root = ensure_initialized()

    from croak.training.trainer import TrainingOrchestrator

    console.print("Generating training configuration...")

    orchestrator = TrainingOrchestrator(root)
    config = orchestrator.prepare_training()

    if config.get("config_path"):
        console.print(f"\n[green]✓ Configuration saved:[/green] {config['config_path']}")
    else:
        console.print("[yellow]Configuration generated (not saved to file)[/yellow]")

    console.print("\nNext: [cyan]croak estimate[/cyan] or [cyan]croak train[/cyan]")


@main.command()
@click.option("--gpu", "-g", default="T4", help="GPU type for cost estimation")
def estimate(gpu: str):
    """Estimate training time and cost."""
    root = ensure_initialized()

    from croak.training.trainer import TrainingOrchestrator

    console.print("Estimating training costs...\n")

    orchestrator = TrainingOrchestrator(root)
    config = orchestrator.prepare_training()
    estimate_result = orchestrator.estimate_cost(config)

    table = Table(title="Training Cost Estimate")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("GPU Type", estimate_result.get("gpu", gpu))
    table.add_row("Estimated Hours", f"{estimate_result.get('estimated_hours', 0):.1f}")
    table.add_row("Cost per Hour", f"${estimate_result.get('cost_per_hour', 0):.2f}")
    table.add_row("Estimated Total", f"${estimate_result.get('estimated_cost', 0):.2f}")

    console.print(table)

    console.print(f"\n[dim]{estimate_result.get('note', '')}[/dim]")
    console.print("\nNext: [cyan]croak train[/cyan]")


@main.command()
@click.option("--provider", type=click.Choice(["local", "modal", "vfrog"]),
              default="local", help="Training provider: local (GPU), modal (serverless), vfrog (platform)")
@click.option("--gpu", "-g", default="T4", help="GPU type for Modal training")
@click.option("--epochs", "-e", default=None, type=int, help="Number of epochs (local/modal only)")
@click.option("--architecture", "-a", default=None, help="Model architecture (local/modal only)")
@click.option("--iteration-id", default=None, help="vfrog iteration ID to train (vfrog only)")
def train(provider: str, gpu: str, epochs: Optional[int], architecture: Optional[str],
          iteration_id: Optional[str]):
    """Start model training.

    \b
    Three providers available:
      local  - Train on local GPU (full control over architecture/hyperparams)
      modal  - Train on Modal.com serverless GPU (full control, cloud compute)
      vfrog  - Train on vfrog platform (simple, vfrog handles everything)
    """
    root = ensure_initialized()

    if provider == "vfrog":
        _train_vfrog(root, iteration_id)
    else:
        _train_classic(root, provider, gpu, epochs, architecture)


def _train_vfrog(root, iteration_id):
    """Train on vfrog platform."""
    from croak.integrations.vfrog import VfrogCLI

    if not VfrogCLI.check_installed():
        console.print("[red]vfrog CLI not installed.[/red]")
        console.print("Install from: [cyan]https://github.com/vfrog/vfrog-cli/releases[/cyan]")
        return

    if not VfrogCLI.check_authenticated():
        console.print("[red]Not logged in to vfrog.[/red]")
        console.print("Run: [cyan]croak vfrog setup[/cyan]")
        return

    # Get iteration ID from argument or state
    if not iteration_id:
        state = load_state(root)
        iteration_id = getattr(state, 'vfrog_iteration_id', None)

    if not iteration_id:
        console.print("[red]No iteration ID specified.[/red]")
        console.print("Either:")
        console.print("  • Run [cyan]croak annotate --method vfrog[/cyan] first")
        console.print("  • Or specify: [cyan]croak train --provider vfrog --iteration-id <id>[/cyan]")
        return

    console.print(Panel.fit(
        f"[bold]vfrog Platform Training[/bold]\n\n"
        f"Iteration: [cyan]{iteration_id[:12]}...[/cyan]\n"
        f"Provider: [cyan]vfrog (platform-managed)[/cyan]\n\n"
        "vfrog handles architecture, hyperparameters, and optimization.\n"
        "Training progress is managed on the vfrog platform.",
        title="🐸 CROAK Training"
    ))

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Training on vfrog platform...", total=None)
        result = VfrogCLI.train_iteration(iteration_id)
        progress.update(task, completed=True)

    if result['success']:
        console.print("\n[green]✓ Training complete![/green]")

        # Update state
        state = load_state(root)
        state.current_stage = "evaluation"
        if "training" not in state.stages_completed:
            state.stages_completed.append("training")
        state.training_state.provider = "vfrog"
        state.save(root / ".croak" / "pipeline-state.yaml")

        console.print("\nNext steps:")
        console.print("  • Test inference: [cyan]croak deploy vfrog --image <test-image>[/cyan]")
        console.print("  • Next iteration: [cyan]croak annotate --method vfrog[/cyan]")
    else:
        console.print(f"\n[red]Training failed: {result.get('error')}[/red]")


def _train_classic(root, provider, gpu, epochs, architecture):
    """Train locally or on Modal (classic pipeline)."""
    from croak.training.trainer import TrainingOrchestrator

    orchestrator = TrainingOrchestrator(root)

    # Prepare configuration
    config = orchestrator.prepare_training(architecture=architecture, epochs=epochs)

    if not config.get("data_yaml"):
        console.print("[red]Error: No data.yaml found. Run 'croak prepare' first.[/red]")
        return

    target_label = "Local GPU" if provider == "local" else f"Modal.com ({gpu})"
    console.print(Panel.fit(
        f"[bold]Training Configuration[/bold]\n\n"
        f"Architecture: [cyan]{config.get('architecture')}[/cyan]\n"
        f"Epochs: [cyan]{config.get('epochs')}[/cyan]\n"
        f"Batch size: [cyan]{config.get('batch_size')}[/cyan]\n"
        f"Provider: [cyan]{target_label}[/cyan]",
        title="🐸 CROAK Training"
    ))

    if provider == "local":
        console.print("\n[bold]Starting local training...[/bold]")
        result = orchestrator.train_local(config)
    else:
        console.print(f"\n[bold]Starting cloud training on Modal.com ({gpu})...[/bold]")
        config["gpu"] = gpu
        result = orchestrator.train_modal(config)

    if result.get("success"):
        console.print("\n[green]✓ Training complete![/green]")
        if result.get("model_path"):
            console.print(f"Model saved: [cyan]{result['model_path']}[/cyan]")

        # Update state
        state = load_state(root)
        state.current_stage = "evaluation"
        if "training" not in state.stages_completed:
            state.stages_completed.append("training")
        state.artifacts.model.path = result.get("model_path")
        state.artifacts.model.architecture = config.get("architecture")
        state.training_state.provider = provider
        state.save(root / ".croak" / "pipeline-state.yaml")

        console.print("\nNext: [cyan]croak evaluate[/cyan]")
    else:
        console.print(f"\n[red]Training failed: {result.get('error')}[/red]")


@main.command()
@click.option("--checkpoint", "-c", help="Checkpoint to resume from")
def resume(checkpoint: Optional[str]):
    """Resume training from checkpoint."""
    root = ensure_initialized()

    from croak.training.trainer import TrainingOrchestrator

    if not checkpoint:
        # Find latest checkpoint
        checkpoints_dir = root / "training" / "experiments"
        checkpoints = list(checkpoints_dir.glob("**/last.pt"))
        if not checkpoints:
            console.print("[red]No checkpoints found to resume from.[/red]")
            return
        checkpoint = str(max(checkpoints, key=lambda p: p.stat().st_mtime))

    console.print(f"Resuming training from [cyan]{checkpoint}[/cyan]...")

    orchestrator = TrainingOrchestrator(root)
    result = orchestrator.train_local({"resume": checkpoint})

    if result.get("success"):
        console.print("\n[green]✓ Training complete![/green]")
    else:
        console.print(f"\n[red]Training failed: {result.get('error')}[/red]")


# ============================================================================
# Evaluation Commands
# ============================================================================


@main.command()
@click.option("--model", "-m", default=None, help="Model path to evaluate")
@click.option("--data", "-d", default=None, help="data.yaml path")
@click.option("--conf", default=0.25, help="Confidence threshold")
@click.option("--iou", default=0.5, help="IoU threshold")
@click.option("--split", default="test", help="Dataset split to evaluate")
def evaluate(model: Optional[str], data: Optional[str], conf: float, iou: float, split: str):
    """Run model evaluation."""
    root = ensure_initialized()
    state = load_state(root)

    from croak.evaluation.evaluator import ModelEvaluator

    # Get model path
    if not model:
        model = state.artifacts.model.path
        if not model:
            console.print("[red]No model specified. Use --model or train a model first.[/red]")
            return

    console.print(f"Evaluating model: [cyan]{model}[/cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running evaluation...", total=None)

        evaluator = ModelEvaluator(root)
        result = evaluator.evaluate(
            model_path=model,
            data_yaml=data,
            conf_threshold=conf,
            iou_threshold=iou,
            split=split,
        )

        progress.update(task, completed=True)

    if result.get("success"):
        metrics = result.get("metrics", {})

        console.print("\n[green]✓ Evaluation complete![/green]\n")

        table = Table(title="Evaluation Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("mAP@50", f"{metrics.get('mAP50', 0):.4f}")
        table.add_row("mAP@50-95", f"{metrics.get('mAP50_95', 0):.4f}")
        table.add_row("Precision", f"{metrics.get('precision', 0):.4f}")
        table.add_row("Recall", f"{metrics.get('recall', 0):.4f}")
        table.add_row("F1 Score", f"{metrics.get('f1', 0):.4f}")

        console.print(table)

        if result.get("deployment_ready"):
            console.print("\n[green]✓ Model meets deployment thresholds[/green]")
        else:
            console.print("\n[yellow]⚠ Model does not meet deployment thresholds[/yellow]")

        # Update state
        state.current_stage = "deployment"
        state.stages_completed.append("evaluation")
        state.save(root / ".croak" / "pipeline-state.yaml")

        console.print("\nNext: [cyan]croak report[/cyan] or [cyan]croak export[/cyan]")
    else:
        console.print(f"\n[red]Evaluation failed: {result.get('error')}[/red]")


@main.command()
@click.option("--model", "-m", default=None, help="Model path")
@click.option("--data", "-d", default=None, help="data.yaml path")
@click.option("--samples", "-n", default=20, help="Number of error samples to analyze")
def analyze(model: Optional[str], data: Optional[str], samples: int):
    """Analyze model errors."""
    root = ensure_initialized()
    state = load_state(root)

    from croak.evaluation.evaluator import ModelEvaluator

    if not model:
        model = state.artifacts.model.path
        if not model:
            console.print("[red]No model specified.[/red]")
            return

    if not data:
        data = state.data_yaml_path

    console.print(f"Analyzing errors for model: [cyan]{model}[/cyan]")

    evaluator = ModelEvaluator(root)
    result = evaluator.analyze_errors(model, data, num_samples=samples)

    if result.get("success"):
        console.print("\n[bold]Error Analysis Results:[/bold]\n")

        if result.get("recommendations"):
            console.print("[cyan]Recommendations:[/cyan]")
            for rec in result["recommendations"]:
                console.print(f"  • {rec}")
    else:
        console.print(f"\n[red]Analysis failed: {result.get('error')}[/red]")


@main.command()
def diagnose():
    """Diagnose model performance issues."""
    root = ensure_initialized()
    state = load_state(root)

    console.print("Diagnosing performance issues...\n")

    issues = []

    # Check data quality
    if not state.data_yaml_path:
        issues.append("No data.yaml found - run 'croak prepare' first")

    # Check model
    if not state.artifacts.model.path:
        issues.append("No trained model found - run 'croak train' first")

    # Check evaluation
    if "evaluation" not in state.stages_completed:
        issues.append("Model not evaluated - run 'croak evaluate' first")

    if issues:
        console.print("[yellow]Issues found:[/yellow]")
        for issue in issues:
            console.print(f"  • {issue}")
    else:
        console.print("[green]No obvious issues found.[/green]")
        console.print("\nFor deeper analysis, run [cyan]croak analyze[/cyan]")


@main.command()
@click.option("--model", "-m", default=None, help="Model path")
@click.option("--output", "-o", default="evaluation/reports", help="Output directory")
def report(model: Optional[str], output: str):
    """Generate evaluation report."""
    root = ensure_initialized()
    state = load_state(root)

    from croak.evaluation.evaluator import ModelEvaluator

    if not model:
        model = state.artifacts.model.path
        if not model:
            console.print("[red]No model specified.[/red]")
            return

    console.print("Generating evaluation report...")

    evaluator = ModelEvaluator(root)
    eval_result = evaluator.evaluate(model)

    if eval_result.get("success"):
        report_md = evaluator.generate_report_md(eval_result)

        # Save report
        output_dir = root / output
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / f"evaluation-report-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.md"

        with open(report_path, "w") as f:
            f.write(report_md)

        console.print(f"\n[green]✓ Report saved:[/green] {report_path}")
        console.print("\nNext: [cyan]croak export[/cyan]")
    else:
        console.print(f"\n[red]Report generation failed: {eval_result.get('error')}[/red]")


# ============================================================================
# Deployment Commands
# ============================================================================


@main.command()
@click.option("--format", "-f", type=click.Choice(["onnx", "torchscript", "coreml", "tflite", "engine", "openvino"]), default="onnx")
@click.option("--model", "-m", default=None, help="Model path")
@click.option("--output", "-o", default=None, help="Output directory")
@click.option("--half/--no-half", default=False, help="Use FP16 precision")
def export(format: str, model: Optional[str], output: Optional[str], half: bool):
    """Export model to deployment format."""
    root = ensure_initialized()
    state = load_state(root)

    from croak.deployment.deployer import ModelDeployer

    if not model:
        model = state.artifacts.model.path
        if not model:
            console.print("[red]No model specified.[/red]")
            return

    console.print(f"Exporting model to [cyan]{format}[/cyan]...")

    deployer = ModelDeployer(root)
    result = deployer.export_model(
        model_path=model,
        format=format,
        output_dir=output,
        half=half,
    )

    if result.get("success"):
        console.print(f"\n[green]✓ Export complete![/green]")
        console.print(f"Exported to: [cyan]{result['exported_path']}[/cyan]")
    else:
        console.print(f"\n[red]Export failed: {result.get('error')}[/red]")


@main.group()
def deploy():
    """Deploy model to cloud or edge."""
    pass


@deploy.command('modal')
@click.option("--model", "-m", default=None, help="Model path")
@click.option("--name", "-n", default="croak-detector", help="App name")
@click.option("--gpu", "-g", default="T4", help="GPU type")
def deploy_modal(model: Optional[str], name: str, gpu: str):
    """Deploy to Modal.com serverless endpoint."""
    root = ensure_initialized()
    state = load_state(root)

    from croak.deployment.deployer import ModelDeployer

    if not model:
        model = state.artifacts.model.path
        if not model:
            console.print("[red]No model specified.[/red]")
            return

    console.print(f"Deploying to Modal.com as [cyan]{name}[/cyan]...")

    deployer = ModelDeployer(root)
    result = deployer.deploy_modal(
        model_path=model,
        app_name=name,
        gpu=gpu,
    )

    if result.get("success"):
        console.print(f"\n[green]✓ Deployment complete![/green]")
        if result.get("endpoint_url"):
            console.print(f"Endpoint: [cyan]{result['endpoint_url']}[/cyan]")
    else:
        console.print(f"\n[yellow]Deployment script generated:[/yellow] {result.get('script_path')}")
        console.print(f"Deploy manually with: [cyan]modal deploy {result.get('script_path')}[/cyan]")


@deploy.command('vfrog')
@click.option("--image", "-i", default=None, help="Test image path for inference")
@click.option("--image-url", default=None, help="Test image URL for inference")
@click.option("--api-key", default=None, help="vfrog API key (or set VFROG_API_KEY)")
def deploy_vfrog(image, image_url, api_key):
    """Verify vfrog model inference endpoint.

    Once a model is trained via vfrog SSAT iterations, the inference
    endpoint is automatically available. This command tests it.
    """
    root = ensure_initialized()

    from croak.integrations.vfrog import VfrogCLI

    if not VfrogCLI.check_installed():
        console.print("[red]vfrog CLI not installed.[/red]")
        console.print("Install from: [cyan]https://github.com/vfrog/vfrog-cli/releases[/cyan]")
        return

    if not image and not image_url:
        console.print("[red]Provide a test image: --image <path> or --image-url <url>[/red]")
        return

    console.print("Testing vfrog inference endpoint...")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Running inference...", total=None)
        result = VfrogCLI.run_inference(
            image_path=image,
            image_url=image_url,
            api_key=api_key,
        )
        progress.update(task, completed=True)

    if result['success']:
        console.print("\n[green]✓ Inference endpoint working![/green]")
        output = result['output']
        if isinstance(output, dict):
            detections = output.get('detections', output.get('results', []))
            if isinstance(detections, list):
                console.print(f"Detections: [cyan]{len(detections)}[/cyan]")
                for det in detections[:5]:
                    label = det.get('class', det.get('label', 'unknown'))
                    conf = det.get('confidence', det.get('score', 0))
                    console.print(f"  • {label}: {conf:.2%}")
                if len(detections) > 5:
                    console.print(f"  ... and {len(detections) - 5} more")
        elif result.get('raw'):
            console.print(f"Response: {result['raw'][:500]}")
    else:
        console.print(f"\n[red]Inference failed: {result.get('error')}[/red]")
        console.print("\nMake sure:")
        console.print("  1. A model has been trained via [cyan]croak train --provider vfrog[/cyan]")
        console.print("  2. VFROG_API_KEY is set or use [cyan]--api-key[/cyan]")


@deploy.command('edge')
@click.option("--model", "-m", default=None, help="Model path")
@click.option("--formats", "-f", default="onnx", help="Export formats (comma-separated)")
def deploy_edge(model: Optional[str], formats: str):
    """Prepare edge deployment package."""
    root = ensure_initialized()
    state = load_state(root)

    from croak.deployment.deployer import ModelDeployer

    if not model:
        model = state.artifacts.model.path
        if not model:
            console.print("[red]No model specified.[/red]")
            return

    format_list = [f.strip() for f in formats.split(",")]

    console.print(f"Creating edge deployment package...")

    deployer = ModelDeployer(root)
    result = deployer.generate_deployment_package(
        model_path=model,
        include_formats=format_list,
        include_sample_code=True,
    )

    if result.get("success"):
        console.print(f"\n[green]✓ Deployment package created![/green]")
        console.print(f"Package directory: [cyan]{result['package_dir']}[/cyan]")
    else:
        console.print(f"\n[red]Package creation failed: {result.get('error')}[/red]")


# ============================================================================
# vfrog Platform Commands
# ============================================================================


@main.group()
def vfrog():
    """vfrog platform integration commands."""
    pass


@vfrog.command()
def setup():
    """Interactive vfrog CLI setup (login, select org/project)."""
    from croak.integrations.vfrog import VfrogCLI

    # 1. Check CLI is installed
    if not VfrogCLI.check_installed():
        console.print("[red]vfrog CLI not found.[/red]")
        console.print("Install from: [cyan]https://github.com/vfrog/vfrog-cli/releases[/cyan]")
        return

    console.print("[green]✓[/green] vfrog CLI found\n")

    # 2. Check if already authenticated
    if VfrogCLI.check_authenticated():
        console.print("[green]✓[/green] Already logged in")
    else:
        console.print("Logging in to vfrog...")
        email = click.prompt("Email")
        password = click.prompt("Password", hide_input=True)
        result = VfrogCLI.login(email, password)
        if not result['success']:
            console.print(f"[red]Login failed: {result.get('error')}[/red]")
            return
        console.print("[green]✓[/green] Login successful\n")

    # 3. List organisations, let user pick
    orgs_result = VfrogCLI.list_organisations()
    if not orgs_result['success']:
        console.print(f"[red]Failed to list organisations: {orgs_result.get('error')}[/red]")
        return

    orgs = orgs_result['output'] if isinstance(orgs_result['output'], list) else []
    if not orgs:
        console.print("[yellow]No organisations found. Create one at https://platform.vfrog.ai[/yellow]")
        return

    console.print("[bold]Organisations:[/bold]")
    for idx, org in enumerate(orgs):
        name = org.get('name', org.get('id', 'Unknown'))
        console.print(f"  [{idx + 1}] {name}")

    choice = click.prompt("Select organisation", type=int, default=1)
    if choice < 1 or choice > len(orgs):
        console.print("[red]Invalid selection.[/red]")
        return

    org = orgs[choice - 1]
    org_id = org.get('id', '')
    result = VfrogCLI.set_organisation(org_id)
    if not result['success']:
        console.print(f"[red]Failed to set organisation: {result.get('error')}[/red]")
        return
    console.print(f"[green]✓[/green] Organisation set: {org.get('name', org_id)}\n")

    # 4. List or create project
    projects_result = VfrogCLI.list_projects()
    projects = []
    if projects_result['success'] and isinstance(projects_result['output'], list):
        projects = projects_result['output']

    if projects:
        console.print("[bold]Projects:[/bold]")
        for idx, proj in enumerate(projects):
            title = proj.get('title', proj.get('id', 'Unknown'))
            console.print(f"  [{idx + 1}] {title}")
        console.print(f"  [{len(projects) + 1}] Create new project")

        choice = click.prompt("Select project", type=int, default=1)
        if choice == len(projects) + 1:
            project_name = click.prompt("Project name")
            create_result = VfrogCLI.create_project(project_name)
            if not create_result['success']:
                console.print(f"[red]Failed to create project: {create_result.get('error')}[/red]")
                return
            proj = create_result['output'] if isinstance(create_result['output'], dict) else {}
        elif 1 <= choice <= len(projects):
            proj = projects[choice - 1]
        else:
            console.print("[red]Invalid selection.[/red]")
            return
    else:
        console.print("[dim]No projects found. Creating one...[/dim]")
        project_name = click.prompt("Project name")
        create_result = VfrogCLI.create_project(project_name)
        if not create_result['success']:
            console.print(f"[red]Failed to create project: {create_result.get('error')}[/red]")
            return
        proj = create_result['output'] if isinstance(create_result['output'], dict) else {}

    project_id = proj.get('id', '')
    result = VfrogCLI.set_project(project_id)
    if not result['success']:
        console.print(f"[red]Failed to set project: {result.get('error')}[/red]")
        return
    console.print(f"[green]✓[/green] Project set: {proj.get('title', project_id)}\n")

    # 5. Save to CROAK config if initialized
    root = get_croak_root()
    if root:
        config = CroakConfig.load(root / ".croak" / "config.yaml")
        config.vfrog.project_id = project_id
        config.vfrog.organisation_id = org_id
        config.save(root / ".croak" / "config.yaml")
        console.print("[green]✓[/green] vfrog config saved to .croak/config.yaml")

    console.print(Panel.fit(
        "[green]vfrog setup complete![/green]\n\n"
        f"Organisation: [cyan]{org.get('name', org_id)}[/cyan]\n"
        f"Project: [cyan]{proj.get('title', project_id)}[/cyan]\n\n"
        "You can now use:\n"
        "  [cyan]croak annotate[/cyan] - Start annotation workflow\n"
        "  [cyan]croak train --provider vfrog[/cyan] - Train on vfrog\n"
        "  [cyan]croak vfrog status[/cyan] - Check vfrog status",
        title="🐸 vfrog"
    ))


@vfrog.command()
def status():
    """Show vfrog CLI config and auth status."""
    from croak.integrations.vfrog import VfrogCLI

    if not VfrogCLI.check_installed():
        console.print("[red]vfrog CLI not installed.[/red]")
        console.print("Install from: [cyan]https://github.com/vfrog/vfrog-cli/releases[/cyan]")
        return

    result = VfrogCLI.get_config()
    if not result['success']:
        console.print(f"[red]Failed to get vfrog config: {result.get('error')}[/red]")
        return

    output = result['output']
    if isinstance(output, dict):
        table = Table(title="vfrog Status")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Authenticated", "Yes" if output.get('authenticated') else "[red]No[/red]")
        table.add_row("Organisation", output.get('organisation_id', '[dim]Not set[/dim]'))
        table.add_row("Project", output.get('project_id', '[dim]Not set[/dim]'))
        table.add_row("Object", output.get('object_id', '[dim]Not set[/dim]'))

        console.print(table)
    else:
        console.print(f"Config: {result.get('raw', 'No output')}")


if __name__ == "__main__":
    main()
