# CROAK Installer

> 🐸 **CROAK** - Computer Recognition Orchestration Agent Kit

The official installer and CLI for CROAK, an agentic framework for object detection model development.

## Quick Start

```bash
# Install from npm
npx croak-cv init

# Or install globally
npm install -g croak-cv
croak init
```

## What is CROAK?

CROAK is an open-source agentic framework that guides you through the entire object detection pipeline:

- **Data Preparation** - Scan, validate, and prepare your datasets
- **Annotation** - Integration with vfrog.ai for professional labeling
- **Training** - Guided model training with GPU support (local or Modal.com)
- **Evaluation** - Comprehensive model analysis and diagnostics
- **Deployment** - Deploy to cloud (vfrog.ai) or edge (TensorRT/ONNX)

## CLI Commands

| Command | Description |
|---------|-------------|
| `croak init` | Initialize CROAK in current directory |
| `croak doctor` | Check environment and dependencies |
| `croak upgrade` | Upgrade to latest version |
| `croak help` | Show help |

### croak init

Initializes a new CROAK project with interactive configuration:

```bash
croak init
```

**Options:**
- `-y, --yes` - Skip prompts, use defaults
- `--name <name>` - Set project name
- `--no-vfrog` - Skip vfrog.ai integration
- `--no-modal` - Skip Modal.com GPU setup

**What it creates:**

```
your-project/
├── .croak/
│   ├── config.yaml          # Project configuration
│   ├── pipeline-state.yaml  # Pipeline progress tracking
│   ├── agents/              # Agent definitions
│   ├── workflows/           # Workflow specifications
│   ├── knowledge/           # Knowledge base
│   └── contracts/           # Handoff contracts
├── data/
│   ├── raw/                 # Raw images
│   └── processed/           # Processed datasets
├── training/
│   ├── configs/             # Training configurations
│   ├── scripts/             # Training scripts
│   └── experiments/         # Experiment outputs
├── evaluation/
│   └── reports/             # Evaluation reports
└── deployment/
    └── edge/                # Edge deployment packages
```

### croak doctor

Checks your environment for compatibility:

```bash
croak doctor
```

**Checks performed:**
- Python 3.10+ installation
- Required Python packages (ultralytics, torch, etc.)
- NVIDIA GPU availability
- Modal.com configuration
- vfrog.ai API key
- Git installation

**Options:**
- `--fix` - Attempt to fix issues automatically

### croak upgrade

Upgrades CROAK to the latest version:

```bash
croak upgrade
```

**Options:**
- `--check` - Check for updates without installing

## Requirements

- **Node.js** 18.0.0 or higher
- **Python** 3.10 or higher
- **Git** (recommended)
- **NVIDIA GPU** (optional - can use Modal.com for cloud GPU)

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VFROG_API_KEY` | vfrog.ai API key for annotation | For annotation |
| `MODAL_TOKEN_ID` | Modal.com token (set via `modal setup`) | For cloud GPU |

## Configuration

After initialization, edit `.croak/config.yaml` to customize:

```yaml
version: "1.0"

project:
  name: "my-detection-project"
  task_type: "detection"

training:
  framework: "ultralytics"
  architecture: "yolov8s"
  epochs: 100
  batch_size: 16

compute:
  provider: "modal"  # or "local"
  gpu_type: "T4"

tracking:
  backend: "mlflow"  # or "wandb"
```

## Next Steps After Init

1. **Add your images** to `data/raw/`

2. **Scan your data:**
   ```bash
   croak scan
   ```

3. **Prepare your dataset:**
   ```bash
   croak prepare
   ```

4. **Train your model:**
   ```bash
   croak train
   ```

5. **Evaluate results:**
   ```bash
   croak evaluate
   ```

6. **Deploy:**
   ```bash
   croak deploy
   ```

## Troubleshooting

### Python not found

Ensure Python 3.10+ is installed and in your PATH:

```bash
python3 --version
```

### vfrog API key not working

1. Verify the key at https://vfrog.ai/settings/api
2. Ensure the environment variable is set:
   ```bash
   echo $VFROG_API_KEY
   ```

### No GPU detected

CROAK will automatically use Modal.com for cloud GPU training. Run:

```bash
pip install modal
modal setup
```

## Links

- **Documentation:** https://github.com/vfrog-ai/croak
- **Issues:** https://github.com/vfrog-ai/croak/issues
- **vfrog.ai:** https://vfrog.ai

## License

MIT License - see [LICENSE](../LICENSE) for details.

---

🐸 **CROAK** — by [vfrog.ai](https://vfrog.ai)
