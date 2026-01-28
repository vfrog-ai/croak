# 🐸 CROAK

**Computer Recognition Orchestration Agent Kit**

> When your model croaks, CROAK helps you figure out why.

CROAK is an open-source agentic framework that guides developers through the complete lifecycle of building and deploying object detection models. It operates as a specialized "team" of AI agents callable from modern coding assistants (Claude Code, Cursor, Codex).

## Quick Start

```bash
# Install CROAK
pip install croak-cv

# Initialize in your project
croak init

# Scan your images
croak scan ./images

# Follow the guided workflow
croak prepare  # Data preparation
croak train    # Model training
croak evaluate # Model evaluation
croak deploy   # Deployment
```

## What CROAK Does

CROAK provides structured workflows for computer vision model development:

1. **Data Agent ("Scout")** - Validates, formats, and manages your datasets
2. **Training Agent ("Coach")** - Configures and executes model training
3. **Evaluation Agent ("Judge")** - Analyzes model performance with actionable insights
4. **Deployment Agent ("Shipper")** - Deploys to cloud (vfrog) or edge (CUDA/TensorRT)

## Requirements

- Python 3.10+
- [vfrog.ai](https://vfrog.ai) account (for annotation)
- NVIDIA GPU (optional, for local training/edge deployment)

## Features

### v1.0 "Detection Core"

- ✅ Object Detection workflows
- ✅ YOLO family (v8, v11) and RT-DETR architectures
- ✅ vfrog.ai integration for annotation and cloud deployment
- ✅ Modal.com integration for GPU training
- ✅ Edge deployment (ONNX, TensorRT, CUDA)
- ✅ MLflow/W&B experiment tracking

## Documentation

- [Getting Started](docs/getting-started.md)
- [Agent Reference](docs/agents.md)
- [Workflow Guide](docs/workflows.md)
- [Knowledge Base](knowledge/README.md)

## Philosophy

**One workflow. One assistant. Zero barriers.**

- Opinionated by default, flexible when needed
- Mentor, not teacher - explains the "why" behind recommendations
- Validates before expensive operations
- Production-first, not prototype-first

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

*Built by [vfrog.ai](https://vfrog.ai)*
