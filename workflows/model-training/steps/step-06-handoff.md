# Step 6: Handoff to Evaluation

## Execution Rules
- 🐸 ALWAYS verify training completed successfully
- ✅ ALWAYS include all required handoff fields
- 📊 ALWAYS compute dataset hash for reproducibility

## Your Task
Create handoff artifact for Evaluation Agent.

## Execution Sequence

### 1. Verify Training Success

```python
from pathlib import Path

best_weights = Path(state['training']['results']['best_weights'])
if not best_weights.exists():
    raise ValueError(f"Best weights not found: {best_weights}")

# Verify model loads
from ultralytics import YOLO
model = YOLO(str(best_weights))
print(f"✅ Model verified: {model.model_name}")
```

### 2. Collect Training Artifacts

```python
artifacts = {
    'model_path': str(best_weights),
    'architecture': state['training']['architecture'],

    'config': {
        'epochs': config['epochs'],
        'batch_size': config['batch'],
        'image_size': config['imgsz'],
        'optimizer': config['optimizer'],
        'learning_rate': config['lr0'],
        'augmentation': {
            'mosaic': config['mosaic'],
            'mixup': config['mixup'],
            'hsv_h': config['hsv_h'],
            'hsv_s': config['hsv_s'],
            'hsv_v': config['hsv_v'],
            'fliplr': config['fliplr']
        }
    },

    'experiment': {
        'id': experiment_id,
        'tracking_uri': './mlruns',
        'run_id': mlflow_run_id
    },

    'training_metrics': {
        'final_mAP50': state['training']['metrics']['final_mAP50'],
        'final_mAP50_95': state['training']['metrics']['final_mAP50_95'],
        'best_epoch': state['training']['results']['best_epoch'],
        'total_epochs': state['training']['results']['total_epochs'],
        'training_time_hours': state['training']['compute']['training_time_hours']
    },

    'checkpoints': {
        'best': str(best_weights),
        'last': str(last_weights)
    },

    'compute': {
        'provider': state['training']['compute']['provider'],
        'gpu_type': state['training']['compute']['gpu_type'],
        'cost_usd': state['training']['compute']['cost_usd']
    },

    'dataset_hash': state['artifacts']['dataset']['checksum'],
    'random_seed': config['seed']
}
```

### 3. Generate Handoff Artifact

```python
import json
from datetime import datetime

handoff = {
    **artifacts,
    'handoff_version': '1.0',
    'source_agent': 'training',
    'target_agent': 'evaluation',
    'created_at': datetime.utcnow().isoformat()
}

handoff_path = Path(f"training/experiments/{experiment_id}/handoff.json")
with open(handoff_path, 'w') as f:
    json.dump(handoff, f, indent=2)
```

### 4. Summary Report

```
🎯 Training Complete - Ready for Evaluation

═══════════════════════════════════════════════════
TRAINING SUMMARY
═══════════════════════════════════════════════════

Experiment: {experiment_id}
Architecture: {architecture}
Training time: {hours} hours
Cost: ${cost}

═══════════════════════════════════════════════════
PERFORMANCE
═══════════════════════════════════════════════════

Final metrics (on validation set):
  mAP@50:      {map50}
  mAP@50-95:   {map50_95}
  Precision:   {precision}
  Recall:      {recall}

Best checkpoint: epoch {best_epoch}

Note: These are validation metrics.
Final evaluation on test set is next.

═══════════════════════════════════════════════════
ARTIFACTS READY
═══════════════════════════════════════════════════

✅ Best weights:    {best_weights}
✅ Last weights:    {last_weights}
✅ Config:          {config_path}
✅ Logs:            {logs_path}
✅ MLflow run:      {run_id}
✅ Handoff:         {handoff_path}

═══════════════════════════════════════════════════
NEXT STEPS
═══════════════════════════════════════════════════

Your model is trained! Now let's evaluate it properly.

The Evaluation Agent will:
• Run evaluation on the held-out TEST set
• Analyze performance by class and object size
• Identify failure patterns
• Recommend deployment threshold
• Determine deployment readiness

Run: croak evaluate
```

### 5. Update Pipeline State

```yaml
current_stage: "evaluation"

stages_completed:
  - "data_preparation"
  - "training_config"
  - "training_execution"
  - "training"

artifacts:
  model:
    path: "{best_weights}"
    architecture: "{architecture}"
    framework: "ultralytics"
    experiment_id: "{experiment_id}"
    checkpoints:
      best: "{best_weights}"
      last: "{last_weights}"
    metrics:
      mAP50: {map50}
      mAP50_95: {map50_95}
    training_time_hours: {hours}
    cost_usd: {cost}
    handoff_path: "{handoff_path}"
```

### 6. Verify Handoff Completeness

```python
required_handoff_fields = [
    'model_path',
    'architecture',
    'config',
    'experiment',
    'training_metrics',
    'checkpoints',
    'compute',
    'dataset_hash',
    'random_seed'
]

for field in required_handoff_fields:
    assert field in handoff, f"Missing handoff field: {field}"
    assert handoff[field] is not None, f"Null handoff field: {field}"

print("✅ Handoff artifact validated")
```

## Outputs

- `handoff_artifact`: Complete artifact for Evaluation Agent

## Handoff Contract

```typescript
interface TrainingHandoff {
  model_path: string;             // Path to best weights
  architecture: string;           // e.g., "yolov8s"

  config: {
    epochs: number;
    batch_size: number;
    image_size: number;
    optimizer: string;
    learning_rate: number;
    augmentation: Record<string, any>;
  };

  experiment: {
    id: string;
    tracking_uri: string;
    run_id: string;
  };

  training_metrics: {
    final_mAP50: number;
    final_mAP50_95: number;
    best_epoch: number;
    total_epochs: number;
    training_time_hours: number;
  };

  checkpoints: {
    best: string;
    last: string;
  };

  compute: {
    provider: "local" | "modal" | "colab" | "other";
    gpu_type: string;
    cost_usd: number;
  };

  dataset_hash: string;
  random_seed: number;
}
```

## Completion

Training workflow complete.

> "✅ Training complete! Handoff ready for Evaluation Agent.
>
> Your model achieved {map50} mAP@50 on validation.
>
> Next: Comprehensive evaluation on test set
>
> Run: `croak evaluate`"

WORKFLOW COMPLETE - Handoff to Evaluation Agent
