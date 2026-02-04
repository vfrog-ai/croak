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
| `/croak-data` | 📊 Scout | Scan directories, validate images, check annotations, prepare datasets |
| `/croak-training` | 🎯 Coach | Configure training, select architectures, manage experiments |
| `/croak-evaluation` | 📈 Judge | Evaluate models, analyze errors, generate reports |
| `/croak-deployment` | 🚀 Shipper | Export models, deploy to cloud (vfrog) or edge (TensorRT) |

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
- `.claude/commands/croak/agents/` - Slash command files for each agent
- `.claude/commands/croak/workflows/` - Slash command files for each workflow
- `CLAUDE.md` - Project context file that Claude Code reads automatically

Claude Code discovers these files and makes them available as slash commands. Each command activates a specialized AI persona with domain expertise.

## What CROAK Does

CROAK provides structured workflows for computer vision model development:

1. **Router Agent ("Dispatcher")** 🐸 - Coordinates the pipeline and routes requests to specialists
2. **Data Agent ("Scout")** 📊 - Validates, formats, and manages your datasets
3. **Training Agent ("Coach")** 🎯 - Configures and executes model training
4. **Evaluation Agent ("Judge")** 📈 - Analyzes model performance with actionable insights
5. **Deployment Agent ("Shipper")** 🚀 - Deploys to cloud (vfrog) or edge (CUDA/TensorRT)

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

- ✅ **Claude Code Integration** - Native slash commands for all agents and workflows
- ✅ Object Detection workflows
- ✅ YOLO family (v8, v11) and RT-DETR architectures
- ✅ vfrog.ai integration for annotation and cloud deployment
- ✅ Modal.com integration for GPU training
- ✅ Edge deployment (ONNX, TensorRT, CUDA)
- ✅ MLflow/W&B experiment tracking
- ✅ Auto-generated `CLAUDE.md` project context

## Project Structure

After running `croak init`, your project will have:

```
your-project/
├── .claude/                   # Claude Code integration
│   └── commands/
│       └── croak/
│           ├── agents/        # Agent slash commands (/croak-data, etc.)
│           └── workflows/     # Workflow slash commands
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
