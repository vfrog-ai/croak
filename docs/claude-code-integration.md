# Claude Code Integration

CROAK integrates natively with Claude Code to provide an interactive, guided experience for building object detection models. This guide explains how to set up and use CROAK with Claude Code.

## Overview

When you initialize a CROAK project, the installer automatically:

1. Creates slash command files in `.claude/commands/croak/`
2. Generates a `CLAUDE.md` project context file
3. Sets up agent and workflow definitions that Claude Code can access

This enables you to type commands like `/croak-data` in Claude Code to instantly activate specialized AI agents.

## Setup

### 1. Initialize Your Project

```bash
npx croak-cv init
```

During initialization, you'll be asked which AI coding tools you use. Select **Claude Code** to enable the integration.

### 2. Verify Installation

Run the doctor command to verify Claude Code integration:

```bash
croak doctor
```

Look for the "IDE Integration" section:

```
IDE Integration
────────────────────────────────────────
  ✓ Claude Code commands
    5 agents, 4 workflows
  ✓ CLAUDE.md project context
```

### 3. Open in Claude Code

Open your project directory in:
- VS Code with the Claude extension
- Claude Code CLI (`claude` command)
- Any IDE with Claude Code support

## Available Commands

### Agent Commands

Agents are specialized AI personas that handle specific parts of the ML pipeline.

| Command | Agent | Icon | Description |
|---------|-------|------|-------------|
| `/croak-router` | Dispatcher | 🐸 | Pipeline coordinator - routes requests and tracks state |
| `/croak-data` | Scout | 📊 | Data scanning, validation, format conversion, splitting |
| `/croak-training` | Coach | 🎯 | Architecture selection, training configuration, execution |
| `/croak-evaluation` | Judge | 📈 | Model evaluation, error analysis, performance reports |
| `/croak-deployment` | Shipper | 🚀 | Model export, optimization, cloud/edge deployment |

### Workflow Commands

Workflows execute multi-step pipelines with checklists and handoffs.

| Command | Description |
|---------|-------------|
| `/croak-data-preparation` | scan → validate → annotate → split → export |
| `/croak-model-training` | recommend → configure → execute → handoff |
| `/croak-model-evaluation` | evaluate → analyze → diagnose → report |
| `/croak-model-deployment` | export → optimize → deploy → verify |

## Usage Examples

### Getting Started (Router)

```
You: /croak-router

Claude: 🐸 Dispatcher here! I'm the CROAK pipeline coordinator.

        Current Status:
        - Stage: uninitialized
        - Completed stages: none

        Based on your pipeline state, I recommend starting with data preparation.
        Would you like me to hand you off to Scout (Data Agent)?
```

### Data Preparation (Scout)

```
You: /croak-data

Claude: 📊 Scout reporting for duty! I'm your data quality specialist.

        Available commands:
        • scan <path>  - Discover images and annotations
        • validate     - Check data quality
        • convert      - Convert annotation formats
        • split        - Create train/val/test splits
        • stats        - Show dataset statistics

        What would you like to do?

You: scan data/raw

Claude: Scanning data/raw...
        [Executes: croak scan data/raw]

        Found 1,247 images:
        - 1,198 valid JPG/PNG files
        - 49 files with issues (see report)

        Existing annotations: 892 YOLO format labels detected
        Missing annotations: 355 images need labeling

        Would you like me to validate the existing annotations?
```

### Training (Coach)

```
You: /croak-training

Claude: 🎯 Coach here! Ready to configure your training run.

        I see you have a prepared dataset:
        - 1,198 images (train: 958, val: 180, test: 60)
        - 5 classes: [person, car, bike, dog, cat]

        Based on your dataset size and GPU (Modal T4), I recommend:
        - Architecture: YOLOv8s (balanced speed/accuracy)
        - Epochs: 100 with early stopping
        - Batch size: 16

        Should I generate the training configuration?
```

## How It Works

### Slash Command Files

Each command in `.claude/commands/croak/` is a markdown file with:

1. **Frontmatter** - Command name and description
2. **Activation Instructions** - How Claude should embody the agent
3. **Quick Reference** - Commands and capabilities

Example (`.claude/commands/croak/agents/data.md`):

```markdown
---
name: 'croak-data'
description: 'Activate Scout — CROAK Data Quality Specialist'
---

You must fully embody this agent's persona...

<agent-activation CRITICAL="TRUE">
1. READ the project config from {project-root}/.croak/config.yaml
2. READ the pipeline state from {project-root}/.croak/pipeline-state.yaml
3. LOAD the agent definition from {project-root}/.croak/agents/data.agent.yaml
...
</agent-activation>
```

### CLAUDE.md Project Context

The `CLAUDE.md` file at your project root provides Claude Code with:

- Project configuration (task type, architecture, GPU provider)
- Available slash commands
- Key directories and their purposes
- CLI command reference
- Project conventions

Claude Code reads this file automatically, giving it ambient awareness of your project.

### Pipeline State

Agents coordinate through `.croak/pipeline-state.yaml`:

```yaml
current_stage: training
stages_completed:
  - data_preparation
artifacts:
  dataset:
    path: data/processed
    classes: [person, car, bike, dog, cat]
    splits: {train: 958, val: 180, test: 60}
```

Each agent reads and updates this file to maintain continuity across sessions.

## Regenerating Commands

If you modify agent definitions or upgrade CROAK, regenerate the commands:

```bash
croak upgrade
```

This will:
1. Update agent YAML definitions
2. Regenerate slash command files
3. Update `CLAUDE.md`
4. Recompile agents (optional optimization)

## Troubleshooting

### Commands Not Appearing

1. Verify the `.claude/commands/croak/` directory exists
2. Run `croak doctor` to check IDE integration status
3. Restart Claude Code / reload the window

### Agent Not Loading Context

1. Check that `.croak/config.yaml` exists
2. Verify `.croak/pipeline-state.yaml` is valid YAML
3. Run `croak status` to verify project state

### Regenerate Everything

```bash
# Full regeneration
croak upgrade

# Or reinitialize (preserves config)
croak init --force
```

## Best Practices

1. **Start with Router** - Always begin with `/croak-router` to understand your pipeline state

2. **Follow the Pipeline** - Work through stages in order: data → training → evaluation → deployment

3. **Use Workflows for End-to-End** - When you want to complete a full stage, use workflow commands

4. **Use Agents for Specific Tasks** - When you need a specific action, use agent commands

5. **Check Status Regularly** - Run `croak status` or ask the Router about current state

6. **Trust the Handoffs** - Agents pass structured handoff artifacts to ensure continuity

## IDE Selection

During `croak init`, you can select which IDEs to configure:

```
? Which AI coding tools do you use?
  ◉ Claude Code (.claude/commands/)
  ○ Cursor (.cursor/commands/)     ← Future
  ○ Codex                          ← Future
```

CROAK's architecture supports multiple IDEs through the `platform-codes.yaml` configuration.
