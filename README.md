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

# 2. Check your environment (Python, GPU, vfrog CLI, etc.)
croak doctor

# 3. Add images to data/raw/ and scan them
croak scan

# 4. Follow the guided workflow
croak annotate  # Annotate via vfrog SSAT or import from external tools
croak train     # Train locally, on Modal.com, or on vfrog platform
croak evaluate  # Evaluate model performance & diagnostics
croak deploy    # Deploy to vfrog inference, Modal, or edge
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `croak init` | Initialize CROAK in current directory |
| `croak doctor` | Check environment and dependencies |
| `croak scan` | Scan and analyze your image dataset |
| `croak validate` | Validate data quality |
| `croak prepare` | Prepare dataset for training |
| `croak annotate` | Annotate images (vfrog SSAT or classic import) |
| `croak train` | Train model (local GPU, Modal, or vfrog platform) |
| `croak evaluate` | Evaluate trained model performance |
| `croak deploy` | Deploy model to vfrog, Modal, or edge |
| `croak status` | Show current pipeline status |
| `croak vfrog setup` | Login to vfrog CLI and select organisation/project |
| `croak vfrog status` | Show vfrog CLI auth and context status |
| `croak next` | Advance to next SSAT iteration |
| `croak history` | Show iteration history |
| `croak upgrade` | Upgrade to latest version |
| `croak help` | Show help |

## Annotation Paths

CROAK supports two annotation workflows. You are never locked into one path.

### vfrog SSAT (recommended for ease of use)

Iterative auto-annotation powered by the [vfrog CLI](https://github.com/vfrog/vfrog-cli). Upload dataset images, create a reference object, run SSAT (Synthetic Self-Annotation Technology) iterations, review labels in HALO, and train on vfrog's managed platform.

```bash
croak vfrog setup           # Login and select organisation/project
croak annotate              # Guided SSAT workflow
croak train --provider vfrog
```

### Classic (full control)

Import annotations from external tools (CVAT, Label Studio, Roboflow, etc.) in YOLO, COCO, or VOC format. Train on your own GPU or on Modal.com.

```bash
croak annotate --method classic --format yolo --path ./annotations
croak train --provider local    # or --provider modal
```

### Comparison

|  | vfrog SSAT | Classic |
|---|---|---|
| **Annotation** | Auto-annotation + HALO review | External tools (CVAT, Label Studio, etc.) |
| **Training** | vfrog managed platform | Local GPU or Modal.com |
| **Deployment** | vfrog inference API | Edge (ONNX, TensorRT) or Modal |
| **Setup** | `croak vfrog setup` | Bring your own annotations |
| **Best for** | Getting started quickly | Full control over pipeline |

## Training & Deployment

### Training Providers

| Provider | Command | Description |
|----------|---------|-------------|
| **Local** | `croak train --provider local` | Train on your own NVIDIA GPU |
| **Modal** | `croak train --provider modal` | Serverless GPU via [Modal.com](https://modal.com) |
| **vfrog** | `croak train --provider vfrog` | Managed training on vfrog platform (requires vfrog annotations) |

### Deployment Targets

| Target | Command | Description |
|--------|---------|-------------|
| **vfrog** | `croak deploy vfrog` | Managed inference API with auto-scaling |
| **Edge** | `croak deploy edge` | Export to ONNX, TensorRT, CoreML, or TFLite |
| **Modal** | `croak deploy modal` | Serverless inference via Modal.com |

## Using CROAK with Claude Code

CROAK integrates natively with Claude Code through slash commands. This is the recommended way to use CROAK for an interactive, guided experience.

### Setup

1. **Initialize your project** - this automatically sets up Claude Code integration:
   ```bash
   npx croak-cv init
   ```

2. **Open your project in Claude Code** (VS Code with Claude extension, or Claude Code CLI)

3. **Start with the Router** - type `/croak-router` to get guidance on next steps

### Slash Commands

Once initialized, these slash commands are available in Claude Code:

#### Agent Commands
| Command | Agent | What It Does |
|---------|-------|--------------|
| `/croak-router` | 🐸 Dispatcher | **Start here!** Pipeline coordinator that guides you through the workflow |
| `/croak-data` | 📊 Scout | Scan directories, validate images, manage vfrog SSAT or classic annotations |
| `/croak-training` | 🎯 Coach | Configure training across local GPU, Modal, or vfrog platform |
| `/croak-evaluation` | 📈 Judge | Evaluate models, analyze errors, generate reports |
| `/croak-deployment` | 🚀 Shipper | Deploy to vfrog inference, Modal serverless, or edge devices |

#### Workflow Commands
| Command | Description |
|---------|-------------|
| `/croak-data-preparation` | Full data pipeline: scan → validate → annotate → split → export |
| `/croak-model-training` | Training pipeline: recommend → configure → execute → handoff |
| `/croak-model-evaluation` | Evaluation pipeline: evaluate → analyze → diagnose → report |
| `/croak-model-deployment` | Deployment pipeline: export → optimize → deploy → verify |

### Example Session

```
You: /croak-router

Claude: 🐸 Dispatcher here! I see this is a new CROAK project.
        Current stage: uninitialized

        Let me help you get started. Do you have images ready to train on?

You: Yes, I have 500 product images in ~/photos/products

Claude: Great! Let me hand you off to Scout (Data Agent) to scan and validate them.

You: /croak-data

Claude: 📊 Scout reporting for duty! I'll help you prepare your dataset.
        Let me scan ~/photos/products...
        [Runs: croak scan ~/photos/products]

        Found 500 images. 487 valid, 13 have issues...
```

### How It Works

When you run `croak init`, CROAK creates:
- `.claude/skills/croak-*/SKILL.md` - Skill files (e.g., croak-router/SKILL.md)
- `CLAUDE.md` - Project context file that Claude Code reads automatically

Claude Code discovers these files and makes them available as slash commands. Each command activates a specialized AI persona with domain expertise.

## What CROAK Does

CROAK provides structured workflows for computer vision model development through five specialist agents:

1. **Router Agent ("Dispatcher")** 🐸 - Coordinates the pipeline, routes requests to specialists, and tracks state
2. **Data Agent ("Scout")** 📊 - Validates datasets, manages vfrog SSAT annotation or classic annotation import
3. **Training Agent ("Coach")** 🎯 - Configures and executes training across local GPU, Modal, or vfrog platform
4. **Evaluation Agent ("Judge")** 📈 - Analyzes model performance with actionable diagnostics and reports
5. **Deployment Agent ("Shipper")** 🚀 - Deploys to vfrog inference API, Modal serverless, or edge devices (ONNX/TensorRT)

Each agent has guardrails to prevent common mistakes, a knowledge base for domain expertise, and handoff contracts for passing context between stages.

## Requirements

- **Node.js** 18.0.0+ (for CLI installer)
- **Python** 3.10+ (for training/evaluation)
- **Git** (recommended)
- **[vfrog CLI](https://github.com/vfrog/vfrog-cli)** (for SSAT annotation and vfrog deployment - optional but recommended)
- [vfrog.ai](https://vfrog.ai) account (for vfrog SSAT and inference)
- NVIDIA GPU (optional - can use [Modal.com](https://modal.com) for cloud GPU)

### vfrog CLI Setup

The vfrog CLI is a standalone Go binary. It is not a Python package.

```bash
# Download from https://github.com/vfrog/vfrog-cli/releases
chmod +x vfrog && sudo mv vfrog /usr/local/bin/

# Login and configure via CROAK
croak vfrog setup
```

Authentication is email/password based (via Supabase). The CLI stores auth tokens locally in `~/.vfrog/`.

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VFROG_API_KEY` | vfrog.ai API key for inference | Only for `croak deploy vfrog` / `vfrog inference` |
| `MODAL_TOKEN_ID` | Modal.com token (via `modal setup`) | For cloud GPU training |

> **Note:** `VFROG_API_KEY` is only needed for inference. Annotation, training, and other vfrog operations use CLI authentication (`croak vfrog setup`).

## Features

### v1.0 "Detection Core"

- **Claude Code Integration** - Native slash commands for all agents and workflows
- Object Detection workflows (YOLO v8/v11, RT-DETR)
- vfrog CLI integration for SSAT annotation, platform training, and inference
- Modal.com integration for serverless GPU training
- Edge deployment (ONNX, TensorRT, CoreML, TFLite)
- MLflow/W&B experiment tracking
- Auto-generated `CLAUDE.md` project context
- Dual-path design: vfrog SSAT (simple) or classic (full control)

## Project Structure

After running `croak init`, your project will have:

```
your-project/
├── .claude/                   # Claude Code integration
│   └── skills/
│       ├── croak-router/      # /croak-router skill
│       │   └── SKILL.md
│       ├── croak-data/        # /croak-data skill
│       │   └── SKILL.md
│       └── ...                # Other skills
├── .croak/                    # CROAK configuration
│   ├── config.yaml           # Project configuration
│   ├── pipeline-state.yaml   # Pipeline progress tracking
│   ├── agents/               # Agent YAML definitions
│   ├── workflows/            # Workflow specifications
│   ├── knowledge/            # Knowledge base
│   └── contracts/            # Handoff contracts
├── CLAUDE.md                  # Project context for Claude Code
├── data/
│   ├── raw/                  # Raw images
│   └── processed/            # Processed datasets
├── training/
│   ├── configs/              # Training configurations
│   ├── scripts/              # Training scripts
│   └── experiments/          # Experiment outputs
├── evaluation/
│   └── reports/              # Evaluation reports
└── deployment/
    └── edge/                 # Edge deployment packages
```

## Documentation

- [Getting Started](docs/getting-started.md)
- [Claude Code Integration](docs/claude-code-integration.md)
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

### vfrog CLI not found

1. Download the binary from [vfrog CLI releases](https://github.com/vfrog/vfrog-cli/releases)
2. Make it executable and add to PATH:
   ```bash
   chmod +x vfrog
   sudo mv vfrog /usr/local/bin/
   vfrog version  # Verify
   ```

### vfrog not authenticated

Run the interactive setup to login and configure your context:

```bash
croak vfrog setup
```

This walks you through email/password login, organisation selection, and project selection.

### vfrog context not set

Check your current vfrog status:

```bash
croak vfrog status
```

If organisation or project are missing, run `croak vfrog setup` again.

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

*Built by [vfrog.ai](https://vfrog.ai)*
