# Step 3: Configure Training

## Execution Rules
- 🐸 ALWAYS set random seed for reproducibility
- ✅ ALWAYS generate config file, not just command args
- 📊 ALWAYS explain non-default settings

## Your Task
Generate comprehensive training configuration.

## Execution Sequence

### 1. Calculate Optimal Hyperparameters

```python
def calculate_hyperparameters(
    architecture: str,
    dataset_size: int,
    num_classes: int,
    has_imbalance: bool
) -> dict:

    # Base epochs - more data = more epochs useful
    if dataset_size < 500:
        epochs = 100
    elif dataset_size < 2000:
        epochs = 150
    else:
        epochs = 200

    # Batch size based on architecture
    batch_sizes = {
        'yolov8n': 32,
        'yolov8s': 16,
        'yolov8m': 8,
        'yolov11s': 16,
        'rt-detr': 8
    }
    batch_size = batch_sizes.get(architecture, 16)

    # Image size
    imgsz = 640  # Default, works well for most cases

    # Learning rate
    lr = 0.01  # Ultralytics default

    return {
        'epochs': epochs,
        'batch_size': batch_size,
        'imgsz': imgsz,
        'lr0': lr,
        'patience': 20  # Early stopping
    }
```

### 2. Generate Experiment ID

```python
from datetime import datetime
import random
import string

def generate_experiment_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
    return f"exp-{timestamp}-{suffix}"
```

### 3. Generate Training Config

```python
config = {
    # Model
    'model': f"{architecture}.pt",  # Pretrained weights
    'pretrained': True,

    # Data
    'data': str(data_yaml_path),
    'imgsz': hyperparams['imgsz'],

    # Training
    'epochs': hyperparams['epochs'],
    'batch': hyperparams['batch_size'],
    'patience': hyperparams['patience'],

    # Optimizer
    'optimizer': 'AdamW',
    'lr0': hyperparams['lr0'],
    'lrf': 0.01,
    'momentum': 0.937,
    'weight_decay': 0.0005,

    # Augmentation
    'augment': True,
    'hsv_h': 0.015,
    'hsv_s': 0.7,
    'hsv_v': 0.4,
    'degrees': 0.0,
    'translate': 0.1,
    'scale': 0.5,
    'shear': 0.0,
    'perspective': 0.0,
    'flipud': 0.0,
    'fliplr': 0.5,
    'mosaic': 1.0,
    'mixup': 0.0,

    # Reproducibility
    'seed': 42,
    'deterministic': True,

    # Experiment
    'project': project_name,
    'name': experiment_id,
    'save_dir': f'./training/experiments/{experiment_id}'
}
```

### 4. Handle Class Imbalance

```python
if has_imbalance:
    # Adjust augmentation for minority classes
    config['mosaic'] = 1.0
    config['mixup'] = 0.1  # Enable mixup

    # Note: Ultralytics handles class weights automatically
    # but we document the imbalance

    imbalance_note = """
    ⚠️ Class imbalance detected. Applied mitigations:
    - Enabled mixup augmentation
    - Using focal loss (automatic in YOLO)
    - Consider collecting more data for minority classes
    """
```

### 5. Write Config File

```python
import yaml
from pathlib import Path

config_dir = Path("training/configs")
config_dir.mkdir(parents=True, exist_ok=True)

config_path = config_dir / f"{experiment_id}.yaml"
with open(config_path, 'w') as f:
    yaml.dump(config, f, default_flow_style=False)
```

### 6. Present Configuration

```
🎯 Training Configuration

Experiment: {experiment_id}
Config file: {config_path}

═══════════════════════════════════════════════════
MODEL
═══════════════════════════════════════════════════

Architecture: {architecture}
Pretrained: Yes (COCO weights)

═══════════════════════════════════════════════════
TRAINING PARAMETERS
═══════════════════════════════════════════════════

Epochs: {epochs}
  └─ Why: {rationale}

Batch size: {batch_size}
  └─ Why: {rationale}

Image size: {imgsz}
Early stopping patience: {patience}

═══════════════════════════════════════════════════
OPTIMIZER
═══════════════════════════════════════════════════

Type: AdamW
Learning rate: {lr0}
Final LR: {lr0 * lrf}
Weight decay: {weight_decay}

═══════════════════════════════════════════════════
AUGMENTATION
═══════════════════════════════════════════════════

Mosaic: {mosaic}
Flip LR: {fliplr}
HSV adjustments: Enabled
Scale: {scale}

{if mixup_enabled}
Mixup: {mixup} (enabled for class imbalance)
{/if}

═══════════════════════════════════════════════════
REPRODUCIBILITY
═══════════════════════════════════════════════════

Random seed: {seed}
Deterministic: Yes

═══════════════════════════════════════════════════
OUTPUT
═══════════════════════════════════════════════════

Save directory: {save_dir}
Experiment tracking: MLflow (local)

═══════════════════════════════════════════════════

This configuration will be used for training.
Modify? [N to accept / Y to customize]
```

### 7. Allow Customization

If user wants to modify:
```python
customizable = ['epochs', 'batch_size', 'imgsz', 'lr0']
for param in customizable:
    current = config[param]
    new_value = input(f"{param} [{current}]: ")
    if new_value:
        config[param] = type(current)(new_value)
```

### 8. Update Pipeline State

```yaml
training:
  config_path: "{config_path}"
  experiment_id: "{experiment_id}"
  config: {config}
```

## Outputs

- `training_config`: Complete training configuration
- `experiment_id`: Unique experiment identifier

## Completion

> "✅ Training configuration saved!
>
> Config: {config_path}
> Experiment ID: {experiment_id}
>
> Next: Set up training environment (GPU)
>
> Run: `croak estimate` to see time/cost, or
> `croak train` to proceed directly"

WAIT for user before loading step-04-environment.md
