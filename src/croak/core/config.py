"""CROAK configuration management."""

from pathlib import Path
from typing import Any, Optional
import yaml
from pydantic import BaseModel, Field


class VfrogConfig(BaseModel):
    """vfrog.ai integration configuration."""

    api_key_env: str = "VFROG_API_KEY"
    project_id: Optional[str] = None


class ComputeConfig(BaseModel):
    """Compute provider configuration."""

    provider: str = "modal"  # modal, local, colab, runpod
    gpu_type: str = "T4"
    timeout_hours: int = 4


class TrainingConfig(BaseModel):
    """Training defaults."""

    framework: str = "ultralytics"
    architecture: str = "yolov8s"
    epochs: int = 100
    batch_size: int = 16
    image_size: int = 640
    patience: int = 20


class TrackingConfig(BaseModel):
    """Experiment tracking configuration."""

    backend: str = "mlflow"  # mlflow, wandb
    mlflow_uri: str = "./mlruns"
    wandb_project: Optional[str] = None
    wandb_entity: Optional[str] = None


class DataConfig(BaseModel):
    """Data configuration."""

    format: str = "yolo"
    train_split: float = 0.8
    val_split: float = 0.15
    test_split: float = 0.05


class DeploymentConfig(BaseModel):
    """Deployment configuration."""

    cloud_provider: str = "vfrog"
    edge_format: str = "tensorrt"  # onnx, tensorrt, cuda
    precision: str = "fp16"  # fp32, fp16, int8


class AgentConfig(BaseModel):
    """Agent behavior configuration."""

    verbose: bool = True
    auto_confirm: bool = False


class CroakConfig(BaseModel):
    """Main CROAK configuration."""

    version: str = "1.0"
    project_name: str = ""
    task_type: str = "detection"
    created_at: Optional[str] = None

    vfrog: VfrogConfig = Field(default_factory=VfrogConfig)
    compute: ComputeConfig = Field(default_factory=ComputeConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    tracking: TrackingConfig = Field(default_factory=TrackingConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)
    agents: AgentConfig = Field(default_factory=AgentConfig)

    @classmethod
    def load(cls, config_path: Path) -> "CroakConfig":
        """Load configuration from YAML file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path) as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def save(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)

    @classmethod
    def find_config(cls, start_path: Optional[Path] = None) -> Optional[Path]:
        """Find .croak/config.yaml in current or parent directories."""
        current = start_path or Path.cwd()

        while current != current.parent:
            config_path = current / ".croak" / "config.yaml"
            if config_path.exists():
                return config_path
            current = current.parent

        return None
