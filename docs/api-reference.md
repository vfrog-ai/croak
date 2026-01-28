# CROAK API Reference

This document provides the API reference for using CROAK programmatically.

## Core Modules

### Configuration

```python
from croak.core.config import CroakConfig, TrainingConfig, ComputeConfig

# Load project config
config = CroakConfig.load(Path(".croak/config.yaml"))

# Access settings
print(config.project_name)
print(config.training.architecture)
print(config.compute.gpu_type)

# Modify and save
config.training.epochs = 200
config.save(Path(".croak/config.yaml"))
```

### Pipeline State

```python
from croak.core.state import PipelineState, load_state

# Load state
state = load_state(project_dir)

# Check current stage
print(state.current_stage)  # "training", "evaluation", etc.

# Track progress
state.stages_completed.append("data_preparation")
state.current_stage = "training"
state.save(project_dir / ".croak/pipeline-state.yaml")

# Access artifacts
print(state.artifacts.model.path)
print(state.artifacts.dataset.classes)
```

### Security

```python
from croak.core.secrets import SecretsManager
from croak.core.paths import PathValidator
from croak.core.commands import SecureRunner

# Redact secrets from logs
safe_text = SecretsManager.redact(text_with_secrets)

# Get API keys from environment
vfrog_key = SecretsManager.get_vfrog_key()

# Validate paths
validator = PathValidator(project_dir)
safe_path = validator.validate_within_project(user_path)
image_path = validator.validate_image(image_path)

# Run commands securely
result = SecureRunner.run(["python", "train.py"], cwd=project_dir)
```

## Data Module

### Data Validation

```python
from croak.data.validator import DataValidator, ValidationResult

validator = DataValidator(dataset_path)
result = validator.validate_all()

if result.is_valid:
    print("Dataset is valid!")
else:
    print("Errors:", result.errors)

print("Warnings:", result.warnings)
print("Statistics:", result.statistics)
```

#### ValidationResult

| Attribute | Type | Description |
|-----------|------|-------------|
| `is_valid` | bool | Whether validation passed |
| `errors` | List[str] | Critical errors |
| `warnings` | List[str] | Non-critical warnings |
| `statistics` | Dict | Dataset statistics |

### Dataset Splitting

```python
from croak.data.splitter import DatasetSplitter

splitter = DatasetSplitter(dataset_path)
result = splitter.split(
    train_ratio=0.8,
    val_ratio=0.15,
    test_ratio=0.05,
    seed=42,
    stratify=True,
)

if result["success"]:
    print(f"Data YAML: {result['data_yaml_path']}")
    print(f"Splits: {result['splits']}")
```

#### Split Result

```python
{
    "success": True,
    "splits": {"train": 800, "val": 150, "test": 50},
    "data_yaml_path": "/path/to/data.yaml",
    "split_at": "2024-01-01T00:00:00",
}
```

## Training Module

### Training Orchestrator

```python
from croak.training.trainer import TrainingOrchestrator

orchestrator = TrainingOrchestrator(project_dir)

# Prepare training configuration
config = orchestrator.prepare_training(
    architecture="yolov8s",
    epochs=100,
    batch_size=16,
)

# Estimate costs
cost = orchestrator.estimate_cost(config)
print(f"Estimated cost: ${cost['estimated_cost']:.2f}")

# Train locally
result = orchestrator.train_local(config)

# Train on Modal.com
result = orchestrator.train_modal({**config, "gpu": "T4"})

if result["success"]:
    print(f"Model saved: {result['model_path']}")
```

#### Training Config

```python
{
    "architecture": "yolov8s",
    "data_yaml": "/path/to/data.yaml",
    "epochs": 100,
    "batch_size": 16,
    "imgsz": 640,
    "lr0": 0.01,
    "patience": 20,
}
```

## Evaluation Module

### Model Evaluator

```python
from croak.evaluation.evaluator import ModelEvaluator

evaluator = ModelEvaluator(project_dir)

# Run evaluation
result = evaluator.evaluate(
    model_path="best.pt",
    data_yaml="data.yaml",
    conf_threshold=0.25,
    iou_threshold=0.5,
    split="test",
)

print(f"mAP@50: {result['metrics']['mAP50']:.4f}")
print(f"Deployment ready: {result['deployment_ready']}")

# Analyze errors
errors = evaluator.analyze_errors("best.pt", "data.yaml", num_samples=20)
print("Recommendations:", errors["recommendations"])

# Generate report
report_md = evaluator.generate_report_md(result)
with open("report.md", "w") as f:
    f.write(report_md)

# Compare models
comparison = evaluator.compare_models(
    ["model_v1.pt", "model_v2.pt"],
    "data.yaml",
)
print(f"Best model: {comparison['best_model']}")
```

#### Evaluation Metrics

| Metric | Description |
|--------|-------------|
| `mAP50` | Mean Average Precision at IoU 0.5 |
| `mAP50_95` | Mean AP across IoU 0.5-0.95 |
| `precision` | True positives / predictions |
| `recall` | True positives / ground truth |
| `f1` | Harmonic mean of precision and recall |

## Deployment Module

### Model Deployer

```python
from croak.deployment.deployer import ModelDeployer

deployer = ModelDeployer(project_dir)

# Export to ONNX
result = deployer.export_model(
    model_path="best.pt",
    format="onnx",
    half=False,
)
print(f"Exported to: {result['exported_path']}")

# Deploy to Modal.com
result = deployer.deploy_modal(
    model_path="best.pt",
    app_name="my-detector",
    gpu="T4",
)
print(f"Endpoint: {result.get('endpoint_url')}")

# Create deployment package
result = deployer.generate_deployment_package(
    model_path="best.pt",
    include_formats=["onnx", "tflite"],
    include_sample_code=True,
)
print(f"Package: {result['package_dir']}")

# List exports and deployments
exports = deployer.list_exports()
deployments = deployer.list_deployments()
```

#### Export Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `onnx` | Open Neural Network Exchange | Cross-platform |
| `torchscript` | PyTorch serialization | PyTorch serving |
| `coreml` | Apple Core ML | iOS/macOS |
| `tflite` | TensorFlow Lite | Mobile/Edge |
| `engine` | TensorRT | NVIDIA GPUs |
| `openvino` | Intel OpenVINO | Intel hardware |

## Agents Module

### Agent Loader

```python
from croak.agents.loader import AgentLoader

loader = AgentLoader(agents_dir)

# Load all agents
agents = loader.load_all()

for agent_id, agent in agents.items():
    print(f"{agent.title}: {agent.role}")

# Route command to agent
result = loader.route_command("validate my dataset")
if result:
    agent, command = result
    print(f"Agent: {agent.title}")
    print(f"Command: {command.name}")
```

### Agent Definition

```python
agent.id           # "data-agent"
agent.name         # "data_agent"
agent.title        # "Data Agent"
agent.role         # "Data preparation and validation"
agent.expertise    # ["data validation", "preprocessing"]
agent.capabilities # List[AgentCapability]
agent.commands     # List[AgentCommand]

# Generate system prompt
prompt = agent.get_system_prompt()
```

## Workflows Module

### Workflow Executor

```python
from croak.workflows.executor import WorkflowExecutor

executor = WorkflowExecutor(project_dir)

# Load workflow
workflow = executor.load_workflow("full-pipeline")

# Get steps ready to execute
ready = executor.get_ready_steps(workflow, completed_steps=[])

# Complete a step
result = executor.complete_step(
    workflow_id="full-pipeline",
    step_id="validate",
    artifacts={"validation_result": "passed"},
)

# Get workflow status
status = executor.get_workflow_status("full-pipeline")
print(f"Progress: {status['progress_percent']}%")
print(f"Complete: {status['is_complete']}")
```

#### Workflow Status

```python
{
    "workflow_id": "full-pipeline",
    "total_steps": 7,
    "completed_steps": 3,
    "progress_percent": 42.86,
    "is_complete": False,
    "current_step": "train",
}
```

## Contracts Module

### Handoff Validator

```python
from croak.contracts.validator import HandoffValidator

validator = HandoffValidator(contracts_dir)

# Validate data against contract
result = validator.validate("data-handoff", data)
if not result["valid"]:
    print("Errors:", result["errors"])

# Create handoff
handoff_path = validator.create_handoff(
    contract_name="data-handoff",
    from_agent="data",
    to_agent="training",
    data=handoff_data,
    handoffs_dir=handoffs_dir,
)

# Read handoff
handoff = validator.read_handoff(handoff_path)

# Find latest handoff
latest = validator.find_latest_handoff(
    handoffs_dir,
    from_agent="training",
    to_agent="evaluation",
)
```

### Convenience Functions

```python
from croak.contracts.validator import (
    create_data_handoff,
    create_training_handoff,
    create_evaluation_handoff,
)

# Create typed handoffs
data_handoff = create_data_handoff(
    validator=validator,
    dataset_path="/path/to/dataset",
    format="yolo",
    data_yaml_path="/path/to/data.yaml",
    splits={"train": 800, "val": 150, "test": 50},
    classes=["cat", "dog"],
    statistics={"total_images": 1000},
    validation_passed=True,
)
```

## Error Handling

All modules use consistent error handling:

```python
from croak.core.paths import PathSecurityError
from croak.core.commands import CommandSecurityError
from croak.contracts.validator import ContractValidationError

try:
    validator.validate_within_project(suspicious_path)
except PathSecurityError as e:
    print(f"Path security violation: {e}")

try:
    SecureRunner.run(["rm", "-rf", "/"])
except CommandSecurityError as e:
    print(f"Command blocked: {e}")

try:
    validator.create_handoff("contract", "a", "b", invalid_data, dir)
except ContractValidationError as e:
    print(f"Contract validation failed: {e}")
```

## Type Hints

CROAK uses Pydantic models for type safety:

```python
from croak.core.state import PipelineState, Artifacts
from croak.agents.loader import AgentDefinition, AgentCapability

# Full type hints available
state: PipelineState = load_state(project_dir)
agent: AgentDefinition = loader.load_agent("data-agent")
```

## See Also

- [Getting Started](getting-started.md) - Quick start guide
- [Agents](agents.md) - Agent documentation
- [Workflows](workflows.md) - Workflow documentation
