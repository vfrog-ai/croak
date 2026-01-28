# 🐸 CROAK

**Computer Recognition Orchestration Agent Kit**

> When your model croaks, CROAK helps you figure out why.

CROAK is an open-source agentic framework that guides developers through the complete lifecycle of building and deploying object detection models. It operates as a specialized "team" of AI agents callable from modern coding assistants (Claude Code, Cursor, Codex).

## Installation

### Option 1: npm CLI (Recommended)

The fastest way to get started. Requires Node.js 18+.

```bash
# Initialize a new CROAK project with interactive setup
npx croak-cv init

# Or install globally for repeated use
npm install -g croak-cv
croak init
```

### Option 2: pip (Python Package)

For Python-first workflows or programmatic access.

```bash
pip install croak-cv
croak init
```

### Option 3: From Source

```bash
git clone https://github.com/vfrog-ai/croak.git
cd croak
./install.sh        # Unix/macOS
# or
./install.ps1       # Windows PowerShell
```

## Quick Start

```bash
# 1. Initialize a new project
croak init

# 2. Check your environment
croak doctor

# 3. Add images to data/raw/ and scan them
croak scan

# 4. Follow the guided workflow
croak prepare  # Data preparation & annotation
croak train    # Model training (local or Modal.com GPU)
croak evaluate # Model evaluation & diagnostics
croak deploy   # Deploy to cloud (vfrog) or edge (TensorRT)
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `croak init` | Initialize CROAK in current directory |
| `croak doctor` | Check environment and dependencies |
| `croak scan` | Scan and analyze your image dataset |
| `croak prepare` | Prepare dataset for training |
| `croak train` | Configure and run model training |
| `croak evaluate` | Evaluate trained model performance |
| `croak deploy` | Deploy model to cloud or edge |
| `croak status` | Show current pipeline status |
| `croak upgrade` | Upgrade to latest version |
| `croak help` | Show help |

## What CROAK Does

CROAK provides structured workflows for computer vision model development:

1. **Data Agent ("Scout")** - Validates, formats, and manages your datasets
2. **Training Agent ("Coach")** - Configures and executes model training
3. **Evaluation Agent ("Judge")** - Analyzes model performance with actionable insights
4. **Deployment Agent ("Shipper")** - Deploys to cloud (vfrog) or edge (CUDA/TensorRT)

## Requirements

- **Node.js** 18.0.0+ (for CLI installer)
- **Python** 3.10+ (for training/evaluation)
- **Git** (recommended)
- [vfrog.ai](https://vfrog.ai) account (for annotation and cloud deployment)
- NVIDIA GPU (optional - can use [Modal.com](https://modal.com) for cloud GPU)

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VFROG_API_KEY` | vfrog.ai API key | For annotation/deployment |
| `MODAL_TOKEN_ID` | Modal.com token (via `modal setup`) | For cloud GPU training |

## Features

### v1.0 "Detection Core"

- ✅ Object Detection workflows
- ✅ YOLO family (v8, v11) and RT-DETR architectures
- ✅ vfrog.ai integration for annotation and cloud deployment
- ✅ Modal.com integration for GPU training
- ✅ Edge deployment (ONNX, TensorRT, CUDA)
- ✅ MLflow/W&B experiment tracking

## Project Structure

After running `croak init`, your project will have:

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

## Documentation

- [Getting Started](docs/getting-started.md)
- [Agent Reference](docs/agents.md)
- [Workflow Guide](docs/workflows.md)
- [Knowledge Base](knowledge/README.md)
- [Installer README](installer/README.md)

## Philosophy

**One workflow. One assistant. Zero barriers.**

- Opinionated by default, flexible when needed
- Mentor, not teacher - explains the "why" behind recommendations
- Validates before expensive operations
- Production-first, not prototype-first

## Troubleshooting

### Python not found

Ensure Python 3.10+ is installed and in your PATH:

```bash
python3 --version
```

### No GPU detected

CROAK will automatically use Modal.com for cloud GPU training:

```bash
pip install modal
modal setup
```

### vfrog API key not working

1. Verify the key at https://vfrog.ai/settings/api
2. Ensure the environment variable is set:
   ```bash
   export VFROG_API_KEY=your_api_key_here
   ```

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

*Built by [vfrog.ai](https://vfrog.ai)*
