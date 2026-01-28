# CROAK Agents

CROAK uses specialized agents to handle different stages of the ML pipeline. Each agent is an expert in its domain and can be orchestrated together or used independently.

## Agent Overview

| Agent | Role | Key Commands |
|-------|------|--------------|
| Data Agent | Data preparation & validation | `validate`, `split`, `prepare` |
| Training Agent | Model training orchestration | `train`, `configure`, `estimate` |
| Evaluation Agent | Model evaluation & analysis | `evaluate`, `analyze`, `report` |
| Deployment Agent | Model export & deployment | `export`, `deploy` |
| GPU Agent | Compute resource management | `provision`, `monitor` |

## Data Agent

The Data Agent specializes in dataset preparation, validation, and quality assurance.

### Capabilities

- **Dataset Validation**: Checks image integrity, annotation format, class balance
- **Data Splitting**: Creates stratified train/val/test splits
- **Quality Metrics**: Calculates dataset statistics and identifies issues
- **Format Conversion**: Converts between YOLO, COCO, and VOC formats

### Commands

```bash
# Scan for images and annotations
croak scan data/raw

# Validate dataset quality
croak validate --path data/processed

# Create splits
croak split --train 0.8 --val 0.15 --test 0.05 --stratify

# Full preparation pipeline
croak prepare
```

### Handoff Contract

The Data Agent produces a handoff containing:

```yaml
contract: data-handoff
data:
  dataset_path: /path/to/processed
  format: yolo
  data_yaml_path: /path/to/data.yaml
  splits:
    train: 800
    val: 150
    test: 50
  classes: [cat, dog, bird]
  statistics:
    total_images: 1000
    total_annotations: 2500
  validation_passed: true
```

## Training Agent

The Training Agent handles model training configuration and execution.

### Capabilities

- **Architecture Selection**: Recommends models based on dataset characteristics
- **Hyperparameter Tuning**: Suggests optimal training parameters
- **Cost Estimation**: Estimates training time and cloud costs
- **Training Orchestration**: Manages local and cloud training runs

### Supported Architectures

| Architecture | Use Case | Size |
|--------------|----------|------|
| YOLOv8n | Edge devices, real-time | 3.2M params |
| YOLOv8s | Balanced speed/accuracy | 11.2M params |
| YOLOv8m | Higher accuracy | 25.9M params |
| YOLOv8l | Maximum accuracy | 43.7M params |
| YOLOv11s | Latest generation | ~11M params |
| RT-DETR-l | Transformer-based | ~32M params |

### Commands

```bash
# Get architecture recommendation
croak recommend

# Generate training config
croak configure

# Estimate training cost
croak estimate --gpu T4

# Start training
croak train --gpu T4 --epochs 100

# Resume from checkpoint
croak resume --checkpoint training/experiments/exp1/last.pt
```

### Handoff Contract

The Training Agent produces:

```yaml
contract: training-handoff
data:
  model_path: /path/to/best.pt
  architecture: yolov8s
  config:
    epochs: 100
    batch_size: 16
    lr0: 0.01
  experiment:
    id: exp-001
    name: frog-detector-v1
  training_metrics:
    final_mAP50: 0.85
    final_mAP50_95: 0.72
    best_epoch: 87
  checkpoints:
    - path: /path/to/best.pt
      epoch: 87
    - path: /path/to/last.pt
      epoch: 100
  compute:
    provider: modal
    gpu_type: T4
    training_time_seconds: 3600
  dataset_hash: abc123def456
  random_seed: 42
```

## Evaluation Agent

The Evaluation Agent analyzes trained models and generates reports.

### Capabilities

- **Metric Calculation**: mAP, precision, recall, F1 by class
- **Error Analysis**: Identifies failure patterns and problem areas
- **Threshold Optimization**: Recommends confidence thresholds
- **Comparative Analysis**: Compares multiple model versions

### Commands

```bash
# Run evaluation
croak evaluate --model best.pt --split test

# Analyze errors
croak analyze --samples 20

# Diagnose issues
croak diagnose

# Generate report
croak report --output evaluation/reports/
```

### Metrics Explained

| Metric | Description | Good Value |
|--------|-------------|------------|
| mAP@50 | Mean AP at IoU 0.5 | >0.7 |
| mAP@50-95 | Mean AP across IoUs | >0.5 |
| Precision | True positives / predictions | >0.8 |
| Recall | True positives / ground truth | >0.8 |
| F1 | Harmonic mean of P & R | >0.8 |

## Deployment Agent

The Deployment Agent handles model export and deployment to various targets.

### Capabilities

- **Format Export**: ONNX, TorchScript, CoreML, TFLite, TensorRT
- **Cloud Deployment**: Modal.com serverless endpoints
- **Edge Packages**: Self-contained deployment bundles
- **Optimization**: Quantization and optimization for target hardware

### Export Formats

| Format | Use Case | Platform |
|--------|----------|----------|
| ONNX | Cross-platform | Any |
| TorchScript | PyTorch serving | Server |
| CoreML | Apple devices | iOS/macOS |
| TFLite | Mobile/edge | Android/Edge |
| TensorRT | NVIDIA GPUs | Server |
| OpenVINO | Intel hardware | Edge/Server |

### Commands

```bash
# Export to ONNX
croak export --format onnx --model best.pt

# Export with FP16
croak export --format onnx --half

# Deploy to Modal.com
croak deploy cloud --name my-detector --gpu T4

# Create edge package
croak deploy edge --formats onnx,tflite
```

## Custom Agents

You can define custom agents by creating YAML files in the `agents/` directory:

```yaml
id: custom-agent
name: custom_agent
title: Custom Agent
role: Custom processing
expertise:
  - custom task 1
  - custom task 2

capabilities:
  - name: custom-capability
    description: Does custom things
    parameters:
      - name: input
        type: string
        required: true

commands:
  - name: custom-cmd
    description: Run custom command
    usage: croak custom-cmd <input>
    examples:
      - croak custom-cmd myfile.txt
```

## Agent Communication

Agents communicate through handoff contracts. Each handoff:

1. **Validates** data against a JSON Schema
2. **Records** the transfer in `.croak/handoffs/`
3. **Provides** artifacts for the next agent

```python
from croak.contracts.validator import HandoffValidator

validator = HandoffValidator(contracts_dir)

# Create handoff
handoff_path = validator.create_handoff(
    contract_name="data-handoff",
    from_agent="data",
    to_agent="training",
    data={...},
    handoffs_dir=handoffs_dir,
)

# Read handoff
handoff = validator.read_handoff(handoff_path)
```

## See Also

- [Workflows](workflows.md) - Orchestrating agents
- [API Reference](api-reference.md) - Programmatic usage
