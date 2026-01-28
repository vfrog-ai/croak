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
def annotate():
    """Start vfrog annotation workflow."""
    root = ensure_initialized()
    console.print("Starting vfrog annotation workflow...")
    console.print("[yellow]This command requires vfrog integration.[/yellow]")
    console.print("Visit [cyan]https://vfrog.ai[/cyan] to set up annotation projects.")


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
@click.option("--local/--cloud", default=False, help="Train locally or on Modal.com")
@click.option("--gpu", "-g", default="T4", help="GPU type for cloud training")
@click.option("--epochs", "-e", default=None, type=int, help="Number of epochs")
@click.option("--architecture", "-a", default=None, help="Model architecture")
def train(local: bool, gpu: str, epochs: Optional[int], architecture: Optional[str]):
    """Start model training."""
    root = ensure_initialized()

    from croak.training.trainer import TrainingOrchestrator

    orchestrator = TrainingOrchestrator(root)

    # Prepare configuration
    config = orchestrator.prepare_training(architecture=architecture, epochs=epochs)

    if not config.get("data_yaml"):
        console.print("[red]Error: No data.yaml found. Run 'croak prepare' first.[/red]")
        return

    console.print(Panel.fit(
        f"[bold]Training Configuration[/bold]\n\n"
        f"Architecture: [cyan]{config.get('architecture')}[/cyan]\n"
        f"Epochs: [cyan]{config.get('epochs')}[/cyan]\n"
        f"Batch size: [cyan]{config.get('batch_size')}[/cyan]\n"
        f"Target: [cyan]{'Local' if local else f'Modal.com ({gpu})'}[/cyan]",
        title="🐸 CROAK Training"
    ))

    if local:
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
        state.stages_completed.append("training")
        state.artifacts.model.path = result.get("model_path")
        state.artifacts.model.architecture = config.get("architecture")
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


@deploy.command()
@click.option("--model", "-m", default=None, help="Model path")
@click.option("--name", "-n", default="croak-detector", help="App name")
@click.option("--gpu", "-g", default="T4", help="GPU type")
def cloud(model: Optional[str], name: str, gpu: str):
    """Deploy to Modal.com cloud."""
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


@deploy.command()
@click.option("--model", "-m", default=None, help="Model path")
@click.option("--formats", "-f", default="onnx", help="Export formats (comma-separated)")
def edge(model: Optional[str], formats: str):
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


if __name__ == "__main__":
    main()
