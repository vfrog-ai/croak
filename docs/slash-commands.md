# CROAK Slash Commands Reference

Complete reference for all CROAK slash commands available in Claude Code.

## Quick Reference

### Agent Commands

| Command | Agent | Description |
|---------|-------|-------------|
| `/croak-router` | 🐸 Dispatcher | Pipeline coordinator and request router |
| `/croak-data` | 📊 Scout | Data scanning, validation, and preparation |
| `/croak-training` | 🎯 Coach | Model training configuration and execution |
| `/croak-evaluation` | 📈 Judge | Model evaluation and error analysis |
| `/croak-deployment` | 🚀 Shipper | Model export and deployment |

### Workflow Commands

| Command | Description |
|---------|-------------|
| `/croak-data-preparation` | Full data preparation pipeline |
| `/croak-model-training` | Full model training pipeline |
| `/croak-model-evaluation` | Full model evaluation pipeline |
| `/croak-model-deployment` | Full model deployment pipeline |

---

## Agent Commands (Detailed)

### `/croak-router` - Pipeline Coordinator

**Agent Name:** Dispatcher
**Icon:** 🐸
**Role:** Pipeline coordinator that routes requests and tracks state

**What it does:**
- Classifies user requests and routes to appropriate agent
- Tracks pipeline state and progress
- Recommends next steps based on current stage
- Manages agent handoffs

**When to use:**
- Starting a new session (to understand current state)
- Unsure which agent to use
- Need guidance on next steps
- Want a status overview

**Example:**
```
You: /croak-router
Claude: 🐸 Dispatcher here! Current status:
        Stage: data_preparation
        Completed: [scan, validate]

        Recommendation: Run /croak-data to continue with dataset splitting.
```

**Available actions:**
- `status` - Show pipeline status
- `next` - Suggest next step
- `history` - Show completed steps
- `help` - Show available commands

---

### `/croak-data` - Data Quality Specialist

**Agent Name:** Scout
**Icon:** 📊
**Role:** Dataset validation and preparation expert

**What it does:**
- Scans directories for images
- Validates image quality and integrity
- Checks and validates annotations
- Converts between annotation formats (COCO, VOC, YOLO)
- Creates train/val/test splits
- Generates dataset statistics
- Coordinates with vfrog.ai for annotation

**When to use:**
- Preparing a new dataset
- Validating existing data
- Converting annotation formats
- Creating dataset splits
- Diagnosing data quality issues

**Example:**
```
You: /croak-data
Claude: 📊 Scout here! Ready to prepare your dataset.

You: scan data/raw
Claude: Found 1,247 images. 1,198 valid, 49 with issues.
        Annotations: 892 YOLO labels found.
```

**Available actions:**
- `scan <path>` - Discover images and annotations
- `validate` - Check data quality
- `convert` - Convert annotation formats
- `split` - Create train/val/test splits
- `stats` - Show dataset statistics
- `prepare` - Full preparation workflow
- `visualize` - Preview sample images with annotations

**CLI equivalent:** `croak scan`, `croak validate`, `croak split`

---

### `/croak-training` - Training Specialist

**Agent Name:** Coach
**Icon:** 🎯
**Role:** ML training configuration and execution expert

**What it does:**
- Recommends model architectures based on dataset
- Generates training configurations
- Creates training scripts (local and Modal.com)
- Estimates GPU costs and training time
- Manages experiment tracking
- Handles checkpoint management

**When to use:**
- Selecting a model architecture
- Configuring training parameters
- Starting a training run
- Comparing experiments
- Resuming training

**Example:**
```
You: /croak-training
Claude: 🎯 Coach here! I see your dataset is ready.

        Recommended architecture: YOLOv8s
        Estimated training time: 2.5 hours on T4 GPU

        Shall I generate the training config?
```

**Available actions:**
- `recommend` - Get architecture recommendation
- `configure` - Generate training config
- `estimate` - Estimate cost and time
- `train` - Start training
- `resume` - Resume from checkpoint
- `compare` - Compare experiments

**CLI equivalent:** `croak train`

---

### `/croak-evaluation` - Evaluation Specialist

**Agent Name:** Judge
**Icon:** 📈
**Role:** Model evaluation and performance analyst

**What it does:**
- Computes comprehensive metrics (mAP, precision, recall)
- Analyzes performance by class and object size
- Identifies failure patterns and edge cases
- Optimizes confidence thresholds
- Generates evaluation reports
- Creates visualizations (confusion matrix, PR curves)

**When to use:**
- After training completes
- Comparing model versions
- Diagnosing performance issues
- Before deployment decision
- Generating reports for stakeholders

**Example:**
```
You: /croak-evaluation
Claude: 📈 Judge here! Let me evaluate your model.

        Results on test set:
        - mAP@50: 0.847
        - mAP@50-95: 0.623

        Per-class analysis shows 'bicycle' underperforming...
```

**Available actions:**
- `evaluate` - Run full evaluation
- `compare` - Compare models
- `analyze` - Detailed error analysis
- `threshold` - Optimize confidence threshold
- `report` - Generate evaluation report
- `visualize` - Create visualizations
- `diagnose` - Identify issues
- `slices` - Analyze by data slices

**CLI equivalent:** `croak evaluate`

---

### `/croak-deployment` - Deployment Specialist

**Agent Name:** Shipper
**Icon:** 🚀
**Role:** Model deployment and production engineer

**What it does:**
- Optimizes models (quantization, pruning)
- Exports to various formats (ONNX, TensorRT)
- Deploys to cloud (vfrog.ai)
- Deploys to edge devices (NVIDIA Jetson)
- Validates deployments
- Sets up monitoring
- Manages rollbacks

**When to use:**
- Model ready for production
- Exporting for specific hardware
- Deploying to cloud endpoint
- Deploying to edge device
- Setting up production monitoring

**Example:**
```
You: /croak-deployment
Claude: 🚀 Shipper ready for deployment!

        Model: yolov8s_best.pt (47.2 MB)
        Options:
        1. Cloud deploy to vfrog.ai
        2. Edge export (TensorRT FP16)
        3. ONNX export
```

**Available actions:**
- `optimize` - Optimize model (quantization)
- `export` - Export to format
- `deploy cloud` - Deploy to vfrog.ai
- `deploy edge` - Deploy to edge device
- `validate` - Test deployment
- `rollback` - Revert to previous version
- `benchmark` - Performance benchmarks

**CLI equivalent:** `croak export`, `croak deploy`

---

## Workflow Commands (Detailed)

Workflow commands execute multi-step pipelines with checklists and automatic handoffs.

### `/croak-data-preparation`

**Pipeline:** scan → validate → annotate → split → export

**Steps:**
1. **Initialize** - Set up data pipeline
2. **Scan** - Discover images in data/raw
3. **Validate** - Check image and annotation quality
4. **Annotate** - Send to vfrog.ai if needed
5. **Split** - Create train/val/test splits
6. **Export** - Generate data.yaml and handoff

**Checklist:**
- [ ] All images validated and readable
- [ ] Annotations in YOLO format
- [ ] Train/val/test splits created
- [ ] Class balance reviewed
- [ ] Quality report generated
- [ ] data.yaml configured

**Output:** DataHandoff artifact for training agent

---

### `/croak-model-training`

**Pipeline:** recommend → configure → execute → handoff

**Steps:**
1. **Initialize** - Load dataset handoff
2. **Recommend** - Suggest architecture
3. **Configure** - Generate training config
4. **Environment** - Set up GPU environment
5. **Execute** - Run training
6. **Handoff** - Create training handoff

**Checklist:**
- [ ] Architecture selected
- [ ] Training config generated
- [ ] Random seeds set
- [ ] Experiment tracking configured
- [ ] Training completed
- [ ] Best checkpoint saved

**Output:** TrainingHandoff artifact for evaluation agent

---

### `/croak-model-evaluation`

**Pipeline:** evaluate → analyze → diagnose → report

**Steps:**
1. **Initialize** - Load training handoff
2. **Compute** - Calculate metrics
3. **Analyze** - Per-class and slice analysis
4. **Diagnose** - Identify issues (optional)
5. **Visualize** - Generate visualizations
6. **Report** - Create evaluation report

**Checklist:**
- [ ] Metrics computed on test set
- [ ] Per-class metrics analyzed
- [ ] Object size analysis done
- [ ] Failure patterns identified
- [ ] Visualizations generated
- [ ] Deployment recommendation made

**Output:** EvaluationHandoff artifact for deployment agent

---

### `/croak-model-deployment`

**Pipeline:** export → optimize → deploy → verify

**Steps:**
1. **Initialize** - Load evaluation handoff
2. **Optimize** - Quantize/prune model
3. **Export** - Convert to target format
4. **Deploy Cloud** - Deploy to vfrog.ai (conditional)
5. **Deploy Edge** - Deploy to device (conditional)
6. **Validate** - Test deployment

**Checklist:**
- [ ] Model optimized
- [ ] Format exported
- [ ] Deployment successful
- [ ] Smoke test passed
- [ ] Monitoring configured
- [ ] Rollback plan ready

**Output:** Deployed model endpoint or edge package

---

## Command Syntax

All commands can be invoked by typing them in Claude Code:

```
/croak-<command>
```

You can also provide context after the command:

```
/croak-data I have images in ~/photos/products that need scanning
```

```
/croak-training Can you configure training for a small model suitable for mobile?
```

---

## Tips

1. **Start with Router** - When unsure, start with `/croak-router` for guidance

2. **Follow the Pipeline** - Data → Training → Evaluation → Deployment

3. **Use Workflows for Complete Tasks** - Use workflow commands for end-to-end processes

4. **Use Agents for Specific Tasks** - Use agent commands when you need one specific action

5. **Check Status** - Ask any agent "what's the current status?" or use `/croak-router`

6. **Agents Remember Context** - Within a session, agents maintain awareness of previous actions
