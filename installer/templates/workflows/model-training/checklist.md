# Model Training Checklist

## Pre-Training Checks

- [ ] Data preparation workflow complete
- [ ] Dataset artifact available
- [ ] data.yaml validated
- [ ] All classes have sufficient instances

## Architecture Selection

- [ ] Requirements analyzed (speed vs accuracy)
- [ ] Architecture recommended with rationale
- [ ] User confirmed architecture choice
- [ ] Pretrained weights available

## Configuration

- [ ] Training config generated
- [ ] Hyperparameters set appropriately
- [ ] Augmentation configured
- [ ] Random seed set for reproducibility
- [ ] Experiment tracking configured (MLflow/W&B)

## Environment Setup

- [ ] GPU availability checked
- [ ] Compute provider selected (Modal/local/other)
- [ ] Dependencies installed
- [ ] Storage space verified

## Modal.com Setup (if using)

- [ ] Modal CLI installed (`pip install modal`)
- [ ] Modal authenticated (`modal token new`)
- [ ] Free credits verified
- [ ] Training stub generated

## Training Execution

- [ ] Cost estimate reviewed and approved
- [ ] Training initiated
- [ ] Progress monitoring active
- [ ] Checkpoints saving correctly

## Post-Training

- [ ] Training completed without errors
- [ ] Best checkpoint saved
- [ ] Last checkpoint saved
- [ ] Final metrics logged
- [ ] Training time recorded
- [ ] Cost recorded (if cloud)

## Handoff Ready

- [ ] All artifacts present
- [ ] Metrics captured
- [ ] Handoff artifact generated
- [ ] Ready for Evaluation Agent
