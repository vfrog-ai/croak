# Step 5: Execute Training

## Execution Rules
- 🐸 REQUIRE user confirmation before starting
- ✅ ALWAYS set up experiment tracking first
- 📊 ALWAYS monitor and report progress
- ⚠️ HANDLE interruptions gracefully

## Your Task
Execute model training and monitor progress.

## Execution Sequence

### 1. Final Confirmation

```
🎯 Ready to Train

═══════════════════════════════════════════════════
TRAINING SUMMARY
═══════════════════════════════════════════════════

Experiment: {experiment_id}
Architecture: {architecture}
Dataset: {num_images} images, {num_classes} classes

Training config:
  Epochs: {epochs}
  Batch size: {batch_size}
  Image size: {imgsz}

Environment:
  Provider: {provider}
  GPU: {gpu_type}
  Estimated time: ~{hours} hours
  Estimated cost: ~${cost}

═══════════════════════════════════════════════════

This will start training. The process will:
1. Download pretrained weights (if needed)
2. Set up experiment tracking
3. Train for {epochs} epochs (or until early stopping)
4. Save best and last checkpoints

{if modal}
Training runs on Modal.com cloud.
You can close this terminal - training continues in the cloud.
{else}
Training runs locally.
Keep this terminal open until complete.
{/if}

Start training? [Y/n]
```

### 2. Setup Experiment Tracking

```python
import mlflow
from datetime import datetime

# Setup MLflow
mlflow.set_tracking_uri("./mlruns")
mlflow.set_experiment(project_name)

run = mlflow.start_run(run_name=experiment_id)

# Log parameters
mlflow.log_params({
    'architecture': architecture,
    'epochs': config['epochs'],
    'batch_size': config['batch'],
    'imgsz': config['imgsz'],
    'lr0': config['lr0'],
    'dataset': data_yaml_path,
    'num_classes': num_classes,
    'train_images': train_count,
    'seed': config['seed']
})

print(f"MLflow tracking: {mlflow.get_tracking_uri()}")
print(f"Run ID: {run.info.run_id}")
```

### 3. Execute Training

For Modal:
```python
import subprocess

print("Starting training on Modal.com...")
print("This may take a few minutes to provision GPU...")

result = subprocess.run(
    ['modal', 'run', script_path],
    capture_output=False  # Stream output
)
```

For local:
```python
from ultralytics import YOLO
import yaml

print("Starting local training...")

# Load config
with open(config_path) as f:
    config = yaml.safe_load(f)

# Load model
model = YOLO(f"{architecture}.pt")

# Train with progress callbacks
results = model.train(
    data=config['data'],
    epochs=config['epochs'],
    batch=config['batch'],
    imgsz=config['imgsz'],
    project=config['project'],
    name=config['name'],
    seed=config['seed'],
    deterministic=config['deterministic'],
    patience=config['patience']
)
```

### 4. Monitor Progress

```
🎯 Training in Progress

Experiment: {experiment_id}
Started: {start_time}
GPU: {gpu_type}

═══════════════════════════════════════════════════
PROGRESS
═══════════════════════════════════════════════════

Epoch: {current}/{total}
[████████████░░░░░░░░] {percent}%

Current metrics:
  Box loss:    {box_loss:.4f}
  Cls loss:    {cls_loss:.4f}
  mAP@50:      {map50:.4f}
  mAP@50-95:   {map50_95:.4f}

Best so far:
  mAP@50: {best_map50:.4f} (epoch {best_epoch})

═══════════════════════════════════════════════════
TIME
═══════════════════════════════════════════════════

Elapsed: {elapsed}
ETA: {remaining}
Avg per epoch: {avg_epoch_time}

═══════════════════════════════════════════════════
```

### 5. Handle Training Events

Early stopping:
```
⚡ Early stopping triggered!

Training stopped at epoch {epoch} (patience: {patience})
Best model was at epoch {best_epoch}

This is normal - the model stopped improving.
```

Out of memory:
```
❌ GPU out of memory!

The batch size ({batch_size}) is too large for {gpu_type}.

Recommendations:
1. Reduce batch size: croak configure --batch {smaller_batch}
2. Use smaller image size: croak configure --imgsz 512
3. Use smaller model: yolov8n instead of {architecture}

Would you like to retry with batch size {smaller_batch}? [Y/n]
```

### 6. Training Complete

```
🎯 Training Complete!

═══════════════════════════════════════════════════
RESULTS
═══════════════════════════════════════════════════

Experiment: {experiment_id}
Duration: {total_time}
Epochs: {actual_epochs}/{max_epochs}

Final Metrics:
  mAP@50:      {final_map50}
  mAP@50-95:   {final_map50_95}
  Precision:   {precision}
  Recall:      {recall}

Best Checkpoint:
  Epoch: {best_epoch}
  mAP@50: {best_map50}

═══════════════════════════════════════════════════
ARTIFACTS
═══════════════════════════════════════════════════

Best weights: {best_weights_path}
Last weights: {last_weights_path}
Training logs: {logs_path}
Config: {config_path}

═══════════════════════════════════════════════════
TRACKING
═══════════════════════════════════════════════════

MLflow run: {run_id}
View: mlflow ui --port 5000

{if modal}
═══════════════════════════════════════════════════
COST
═══════════════════════════════════════════════════

GPU time: {gpu_hours} hours
Cost: ${actual_cost}
{/if}
```

### 7. Log Final Metrics

```python
# Log final metrics to MLflow
mlflow.log_metrics({
    'final_mAP50': results.metrics['mAP50'],
    'final_mAP50_95': results.metrics['mAP50-95'],
    'final_precision': results.metrics['precision'],
    'final_recall': results.metrics['recall'],
    'best_epoch': results.best_epoch,
    'training_time_hours': training_time_hours
})

# Log artifacts
mlflow.log_artifact(best_weights_path)
mlflow.log_artifact(config_path)

mlflow.end_run()
```

### 8. Update Pipeline State

```yaml
training:
  status: "completed"
  completed_at: "{timestamp}"

  results:
    best_weights: "{best_weights_path}"
    last_weights: "{last_weights_path}"
    best_epoch: {best_epoch}
    total_epochs: {actual_epochs}

  metrics:
    final_mAP50: {map50}
    final_mAP50_95: {map50_95}
    precision: {precision}
    recall: {recall}

  compute:
    provider: "{provider}"
    gpu_type: "{gpu_type}"
    training_time_hours: {hours}
    cost_usd: {cost}

  tracking:
    mlflow_run_id: "{run_id}"
    tracking_uri: "./mlruns"

stages_completed:
  - "data_preparation"
  - "training_config"
  - "training_execution"
```

## Outputs

- `model_weights`: Path to best checkpoint
- `training_metrics`: Final training metrics

## Completion

> "✅ Training complete!
>
> Best model: {best_weights_path}
> mAP@50: {map50}
>
> Ready for evaluation!
>
> Next: `croak evaluate`"

WAIT for user before loading step-06-handoff.md
