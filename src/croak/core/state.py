"""CROAK pipeline state management."""

from pathlib import Path
from typing import Any, Optional
from datetime import datetime
import yaml
from pydantic import BaseModel, Field


class AnnotationState(BaseModel):
    """Tracks how dataset images were annotated."""

    source: Optional[str] = None  # "vfrog" or "classic"
    method: Optional[str] = None  # "ssat" (vfrog) or "manual" (classic)
    format: Optional[str] = None  # "yolo", "coco", "voc" (classic path tracks this)
    vfrog_iteration_id: Optional[str] = None  # Only when source == "vfrog"
    vfrog_object_id: Optional[str] = None  # Only when source == "vfrog"


class TrainingState(BaseModel):
    """Tracks training provider and path-specific metadata."""

    provider: Optional[str] = None  # "local", "modal", or "vfrog"
    # Classic path fields (provider == "local" or "modal"):
    architecture: Optional[str] = None
    experiment_id: Optional[str] = None
    # vfrog path fields (provider == "vfrog"):
    vfrog_iteration_id: Optional[str] = None


class DeploymentState(BaseModel):
    """Tracks deployment target."""

    target: Optional[str] = None  # "vfrog", "modal", or "edge"
    vfrog_api_key_env: str = "VFROG_API_KEY"


class DatasetArtifact(BaseModel):
    """Dataset artifact information."""

    path: Optional[str] = None
    format: Optional[str] = None
    version: Optional[str] = None
    checksum: Optional[str] = None
    classes: list[str] = Field(default_factory=list)
    splits: dict[str, int] = Field(default_factory=dict)
    quality_report_path: Optional[str] = None
    vfrog_project_id: Optional[str] = None


class ModelArtifact(BaseModel):
    """Model artifact information."""

    path: Optional[str] = None
    architecture: Optional[str] = None
    framework: Optional[str] = None
    experiment_id: Optional[str] = None
    checkpoints: dict[str, Optional[str]] = Field(default_factory=dict)
    metrics: dict[str, Optional[float]] = Field(default_factory=dict)
    training_time_hours: Optional[float] = None
    cost_usd: Optional[float] = None
    handoff_path: Optional[str] = None


class EvaluationArtifact(BaseModel):
    """Evaluation artifact information."""

    report_path: Optional[str] = None
    metrics: dict[str, Optional[float]] = Field(default_factory=dict)
    deployment_ready: bool = False
    recommended_threshold: Optional[float] = None


class DeploymentArtifact(BaseModel):
    """Deployment artifact information."""

    cloud_endpoint: Optional[str] = None
    cloud_api_key: Optional[str] = None
    cloud_dashboard: Optional[str] = None
    edge_model_path: Optional[str] = None
    edge_format: Optional[str] = None
    benchmark: dict[str, Optional[float]] = Field(default_factory=dict)


class Artifacts(BaseModel):
    """All pipeline artifacts."""

    dataset: DatasetArtifact = Field(default_factory=DatasetArtifact)
    model: ModelArtifact = Field(default_factory=ModelArtifact)
    evaluation: EvaluationArtifact = Field(default_factory=EvaluationArtifact)
    deployment: DeploymentArtifact = Field(default_factory=DeploymentArtifact)


class Experiment(BaseModel):
    """Experiment tracking information."""

    id: str
    status: str = "pending"  # pending, running, completed, failed
    started: Optional[str] = None
    completed: Optional[str] = None
    architecture: Optional[str] = None
    metrics: dict[str, float] = Field(default_factory=dict)
    model_path: Optional[str] = None


class StageHistory(BaseModel):
    """History entry for a completed stage."""

    stage: str
    completed_at: str
    duration_seconds: Optional[float] = None
    artifacts: dict[str, Any] = Field(default_factory=dict)


class PipelineState(BaseModel):
    """CROAK pipeline state."""

    version: str = "1.0"
    initialized_at: Optional[str] = None
    last_updated: Optional[str] = None

    current_stage: str = "uninitialized"
    stages_completed: list[str] = Field(default_factory=list)
    stage_history: list[StageHistory] = Field(default_factory=list)

    # Data configuration
    data_yaml_path: Optional[str] = None

    # Annotation, training, and deployment path tracking
    annotation: AnnotationState = Field(default_factory=AnnotationState)
    training_state: TrainingState = Field(default_factory=TrainingState)
    deployment_state: DeploymentState = Field(default_factory=DeploymentState)

    artifacts: Artifacts = Field(default_factory=Artifacts)
    experiments: list[Experiment] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    # Workflow tracking
    workflow_progress: dict[str, list[str]] = Field(default_factory=dict)
    workflow_artifacts: dict[str, dict] = Field(default_factory=dict)

    @classmethod
    def load(cls, state_path: Path) -> "PipelineState":
        """Load state from YAML file."""
        if not state_path.exists():
            return cls()

        with open(state_path) as f:
            data = yaml.safe_load(f)

        if data is None:
            return cls()

        return cls(**data)

    def save(self, state_path: Path) -> None:
        """Save state to YAML file."""
        self.last_updated = datetime.utcnow().isoformat()
        state_path.parent.mkdir(parents=True, exist_ok=True)

        with open(state_path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)

    def complete_stage(self, stage: str) -> None:
        """Mark a stage as completed."""
        if stage not in self.stages_completed:
            self.stages_completed.append(stage)

    def is_stage_completed(self, stage: str) -> bool:
        """Check if a stage is completed."""
        return stage in self.stages_completed

    def validate_provider_annotation_compatibility(self) -> list[str]:
        """Validate that training provider matches annotation source.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []
        provider = self.training_state.provider
        source = self.annotation.source

        if provider == "vfrog" and source and source != "vfrog":
            errors.append(
                "Training provider is 'vfrog' but annotations are from "
                f"'{source}'. vfrog training requires vfrog annotations."
            )

        if provider in ("local", "modal") and source == "vfrog":
            errors.append(
                f"Training provider is '{provider}' but annotations are "
                "from 'vfrog'. vfrog does not export annotations. Use "
                "classic annotations for local/Modal training, or train "
                "with --provider vfrog."
            )

        return errors

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        if warning not in self.warnings:
            self.warnings.append(warning)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        if error not in self.errors:
            self.errors.append(error)

    def add_experiment(self, experiment: Experiment) -> None:
        """Add a new experiment."""
        self.experiments.append(experiment)

    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID."""
        for exp in self.experiments:
            if exp.id == experiment_id:
                return exp
        return None

    @classmethod
    def find_state(cls, start_path: Optional[Path] = None) -> Optional[Path]:
        """Find .croak/pipeline-state.yaml in current or parent directories."""
        current = start_path or Path.cwd()

        while current != current.parent:
            state_path = current / ".croak" / "pipeline-state.yaml"
            if state_path.exists():
                return state_path
            current = current.parent

        return None

    # Workflow tracking methods
    def get_workflow_progress(self, workflow_id: str) -> list[str]:
        """Get list of completed steps for a workflow.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            List of completed step IDs.
        """
        return self.workflow_progress.get(workflow_id, [])

    def complete_workflow_step(
        self,
        workflow_id: str,
        step_id: str,
        artifacts: Optional[dict] = None
    ) -> None:
        """Mark a workflow step as completed.

        Args:
            workflow_id: Workflow identifier.
            step_id: Step identifier.
            artifacts: Optional artifacts produced by the step.
        """
        if workflow_id not in self.workflow_progress:
            self.workflow_progress[workflow_id] = []

        if step_id not in self.workflow_progress[workflow_id]:
            self.workflow_progress[workflow_id].append(step_id)

        if artifacts:
            if workflow_id not in self.workflow_artifacts:
                self.workflow_artifacts[workflow_id] = {}
            self.workflow_artifacts[workflow_id][step_id] = artifacts

    def reset_workflow(self, workflow_id: str) -> None:
        """Reset progress for a workflow.

        Args:
            workflow_id: Workflow identifier.
        """
        self.workflow_progress.pop(workflow_id, None)
        self.workflow_artifacts.pop(workflow_id, None)

    def get_workflow_artifacts(self, workflow_id: str, step_id: Optional[str] = None) -> dict:
        """Get artifacts for a workflow or specific step.

        Args:
            workflow_id: Workflow identifier.
            step_id: Optional step identifier.

        Returns:
            Artifacts dict.
        """
        workflow_arts = self.workflow_artifacts.get(workflow_id, {})
        if step_id:
            return workflow_arts.get(step_id, {})
        return workflow_arts


def load_state(project_root: Path) -> PipelineState:
    """Load pipeline state from project root.

    Args:
        project_root: Path to project root directory.

    Returns:
        PipelineState instance.
    """
    state_path = project_root / ".croak" / "pipeline-state.yaml"
    return PipelineState.load(state_path)
