# Pipeline Stages

This document defines the CROAK pipeline stages, valid transitions, and requirements for each stage.

## Stage Definitions

### 1. Uninitialized
**Description**: Project created but no work started.

**Entry Condition**: `croak init` completed

**Exit Condition**: User has added data and run `croak scan`

**Artifacts**: None

**Next Stage**: data_preparation

---

### 2. Data Preparation
**Description**: Dataset discovery, validation, annotation, and splitting.

**Entry Condition**: Raw images exist in `data/raw/`

**Exit Condition**:
- Data validated with no critical errors
- Train/val/test splits created
- `data.yaml` generated

**Artifacts**:
- `data/data.yaml` - Dataset configuration
- `data/reports/quality-report.md` - Validation report
- `.croak/handoffs/data-handoff.yaml` - Handoff contract

**Sub-steps**:
1. Scan - Discover images and annotations
2. Validate - Check data quality
3. Annotate - Label via vfrog (if needed)
4. Convert - Standardize format (if needed)
5. Split - Create train/val/test partitions

**Next Stage**: training

---

### 3. Training
**Description**: Model training configuration and execution.

**Entry Condition**:
- Data preparation completed
- `data.yaml` exists and is valid

**Exit Condition**:
- Training completed successfully
- Model weights saved
- Training metrics logged

**Artifacts**:
- `training/experiments/{id}/weights/best.pt` - Best model
- `training/experiments/{id}/weights/last.pt` - Final checkpoint
- `training/configs/train-config.yaml` - Training configuration
- `.croak/handoffs/training-handoff.yaml` - Handoff contract

**Sub-steps**:
1. Recommend - Select architecture
2. Configure - Generate training config
3. Estimate - Calculate time/cost
4. Execute - Run training
5. Monitor - Track progress

**Next Stage**: evaluation

---

### 4. Evaluation
**Description**: Model performance assessment and analysis.

**Entry Condition**:
- Training completed
- Model weights exist

**Exit Condition**:
- Evaluation metrics computed
- Performance report generated
- Deployment readiness determined

**Artifacts**:
- `evaluation/reports/evaluation-report.md` - Performance report
- `evaluation/visualizations/` - Confusion matrices, PR curves
- `.croak/handoffs/evaluation-handoff.yaml` - Handoff contract

**Sub-steps**:
1. Evaluate - Compute metrics on test set
2. Analyze - Investigate errors
3. Diagnose - Identify improvement areas
4. Report - Generate comprehensive report

**Next Stage**: deployment

---

### 5. Deployment
**Description**: Model export, optimization, and deployment.

**Entry Condition**:
- Evaluation completed
- Model meets deployment thresholds (or user override)

**Exit Condition**:
- Model exported to target format(s)
- Deployment package created or cloud deployment active

**Artifacts**:
- `exports/{format}/model.{ext}` - Exported models
- `deployment/edge/` - Edge deployment package
- `deployment/cloud/` - Cloud deployment scripts

**Sub-steps**:
1. Export - Convert to deployment format
2. Optimize - Quantize/compress if needed
3. Validate - Test exported model
4. Deploy - Ship to cloud or package for edge

**Next Stage**: complete

---

### 6. Complete
**Description**: Pipeline finished, model deployed.

**Entry Condition**: Deployment completed

**Exit Condition**: N/A (terminal state)

**Artifacts**: All previous artifacts preserved

---

## Stage Transitions

```
uninitialized ──► data_preparation ──► training ──► evaluation ──► deployment ──► complete
                        │                  │            │
                        └──────────────────┴────────────┘
                              (can revisit earlier stages)
```

### Valid Transitions

| From | To | Trigger |
|------|-----|---------|
| uninitialized | data_preparation | `croak scan` |
| data_preparation | training | `croak prepare` completes |
| training | evaluation | `croak train` completes |
| evaluation | deployment | `croak evaluate` completes |
| deployment | complete | `croak deploy` completes |

### Backward Transitions (Re-iteration)

Users can revisit earlier stages:
- Re-run data preparation with new data
- Re-train with different config
- Re-evaluate with different thresholds

The state tracks `stages_completed` separately from `current_stage` to support this.

## State File Structure

```yaml
version: "1.0"
initialized_at: "2024-01-15T10:30:00Z"
last_updated: "2024-01-15T14:22:00Z"

current_stage: "training"
stages_completed:
  - "data_preparation"

data_yaml_path: "data/data.yaml"

artifacts:
  dataset:
    path: "data/processed"
    classes: ["cat", "dog"]
    splits:
      train: 800
      val: 150
      test: 50
  model:
    path: null
    architecture: null
  evaluation:
    metrics: {}
  deployment:
    cloud_endpoint: null
```
