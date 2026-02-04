# Step 1: Initialize Training

## Execution Rules
- 🐸 ALWAYS verify dataset artifact from Data Agent
- ✅ ALWAYS validate data.yaml exists and is correct
- ⚠️ NEVER proceed without valid dataset

## Your Task
Verify prerequisites and initialize training context.

## Execution Sequence

### 1. Load Pipeline State

```python
import yaml
from pathlib import Path

state_path = Path(".croak/pipeline-state.yaml")
with open(state_path) as f:
    state = yaml.safe_load(f)
```

Check prerequisites:
- `data_preparation` in `stages_completed`
- `artifacts.dataset` is populated

### 2. Validate Dataset Artifact

```python
dataset = state['artifacts']['dataset']

required_fields = [
    'path',
    'format',
    'data_yaml_path',
    'splits',
    'classes'
]

for field in required_fields:
    if field not in dataset or dataset[field] is None:
        raise ValueError(f"Missing required field: {field}")
```

If dataset artifact missing:
> "❌ Dataset not ready for training.
>
> The Data Agent hasn't completed data preparation.
> Please run `croak prepare` first to prepare your dataset."

### 3. Validate data.yaml

```python
data_yaml_path = Path(dataset['data_yaml_path'])
with open(data_yaml_path) as f:
    data_config = yaml.safe_load(f)

# Verify required fields
required = ['path', 'train', 'val', 'nc', 'names']
for field in required:
    assert field in data_config, f"data.yaml missing: {field}"

# Verify paths exist
base_path = Path(data_config['path'])
for split in ['train', 'val']:
    split_path = base_path / data_config[split]
    assert split_path.exists(), f"Split path missing: {split_path}"
```

### 4. Report Dataset Summary

```
🎯 Training Initialization

═══════════════════════════════════════════════════
DATASET READY
═══════════════════════════════════════════════════

Location: {dataset_path}
Format: YOLO

Images:
  Train: {train_count}
  Val: {val_count}
  Test: {test_count}

Classes ({num_classes}):
{class_list}

Total instances: {instance_count}
Avg per image: {avg}

═══════════════════════════════════════════════════
QUALITY STATUS
═══════════════════════════════════════════════════

Data validation: ✅ Passed
Annotation source: vfrog

{if warnings}
⚠️ Warnings from data preparation:
{warning_list}
{/if}

Ready to configure training!
```

### 5. Create Training Context

```python
training_context = {
    'dataset': {
        'path': dataset['path'],
        'data_yaml': dataset['data_yaml_path'],
        'classes': dataset['classes']['names'],
        'num_classes': len(dataset['classes']['names']),
        'train_images': dataset['splits']['train'],
        'val_images': dataset['splits']['val'],
        'test_images': dataset['splits']['test']
    },
    'recommendations': {
        'suggested_architecture': None,  # Set in next step
        'suggested_epochs': None,
        'suggested_batch_size': None
    },
    'constraints': {
        'has_gpu': check_local_gpu(),
        'imbalanced_classes': check_imbalance(dataset)
    }
}
```

### 6. Update Pipeline State

```yaml
current_stage: "training"
training:
  status: "initializing"
  context: {training_context}
```

## Outputs

- `dataset_artifact`: Validated dataset information
- `training_context`: Context for architecture recommendation

## Completion

> "✅ Dataset validated and ready for training!
>
> Next: Get an architecture recommendation
>
> Run: `croak recommend`
>
> Or skip straight to training with defaults:
> `croak train`"

WAIT for user before loading step-02-recommend.md
