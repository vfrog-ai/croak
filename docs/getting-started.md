# Getting Started with CROAK

CROAK (Computer Recognition Orchestration Agent Kit) is an agentic framework for building object detection models. This guide walks you through setting up your first project.

## Prerequisites

- Python 3.10+
- Node.js 18+ (for the CLI installer)
- A GPU for training (local or cloud via Modal.com)

## Installation

### Option 1: NPM Installer (Recommended)

```bash
npx croak-cv
```

This will:
1. Check Python and pip versions
2. Create a virtual environment
3. Install CROAK and dependencies
4. Set up a new project

### Option 2: Manual Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install CROAK
pip install croak-cv

# Initialize a project
croak init --name my-project
```

## Project Structure

After initialization, your project will have this structure:

```
my-project/
├── .croak/                    # CROAK configuration
│   ├── config.yaml           # Project configuration
│   ├── pipeline-state.yaml   # Pipeline progress tracking
│   ├── handoffs/             # Agent handoff files
│   └── logs/                 # Execution logs
├── data/
│   ├── raw/                  # Original images
│   ├── annotations/          # Annotation files
│   └── processed/            # Prepared dataset
│       ├── images/
│       └── labels/
├── training/
│   ├── configs/              # Training configurations
│   └── experiments/          # Training runs
├── evaluation/
│   └── reports/              # Evaluation reports
└── deployment/
    ├── cloud/                # Cloud deployment configs
    └── edge/                 # Edge deployment packages
```

## Basic Workflow

### 1. Add Your Data

Place your images in the `data/raw/` directory:

```bash
cp ~/my-images/*.jpg data/raw/
```

### 2. Scan Your Data

```bash
croak scan data/raw
```

This discovers images and checks for existing annotations.

### 3. Annotate (if needed)

If you don't have annotations, use vfrog.ai:

```bash
croak annotate
```

Or provide your own YOLO-format labels in `data/processed/labels/`.

### 4. Validate Data

```bash
croak validate
```

Checks data quality, class balance, and annotation integrity.

### 5. Create Splits

```bash
croak split --train 0.8 --val 0.15 --test 0.05
```

Creates train/validation/test splits with a `data.yaml` file.

### 6. Train Model

```bash
# Train on Modal.com (cloud GPU)
croak train --gpu T4

# Or train locally
croak train --local
```

### 7. Evaluate

```bash
croak evaluate
```

Runs evaluation on the test set and shows metrics.

### 8. Export/Deploy

```bash
# Export to ONNX
croak export --format onnx

# Deploy to Modal.com
croak deploy cloud --name my-detector
```

## Configuration

### Project Config (`.croak/config.yaml`)

```yaml
version: "1.0"
project_name: "my-project"
task_type: "detection"

training:
  framework: ultralytics
  architecture: yolov8s
  epochs: 100
  batch_size: 16
  image_size: 640

compute:
  provider: modal
  gpu_type: T4
```

### Environment Variables

```bash
# Required for vfrog.ai integration
export VFROG_API_KEY=your_key_here

# Required for Modal.com cloud training
export MODAL_TOKEN_ID=your_id
export MODAL_TOKEN_SECRET=your_secret
```

## Next Steps

- Learn about [Agents](agents.md) and how they work
- Understand [Workflows](workflows.md) and customization
- Explore the [API Reference](api-reference.md)
