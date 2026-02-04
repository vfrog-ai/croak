# Step 6: Export Training Dataset

## Execution Rules
- 🐸 ALWAYS generate data.yaml for YOLO training
- ✅ ALWAYS verify final directory structure
- 📊 ALWAYS create handoff artifact for Training Agent
- 🔒 ALWAYS compute dataset checksum for reproducibility

## Your Task
Finalize the dataset and prepare handoff to Training Agent.

## Execution Sequence

### 1. Generate data.yaml

```python
from pathlib import Path
import yaml

def generate_data_yaml(
    output_dir: Path,
    class_names: list,
    train_path: str = "images/train",
    val_path: str = "images/val",
    test_path: str = "images/test"
) -> str:
    config = {
        'path': str(output_dir.absolute()),
        'train': train_path,
        'val': val_path,
        'test': test_path,
        'nc': len(class_names),
        'names': class_names
    }

    yaml_path = output_dir / "data.yaml"
    with open(yaml_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    return str(yaml_path)
```

Generated data.yaml:
```yaml
# CROAK Generated Dataset Configuration
# Project: {project_name}
# Generated: {timestamp}

path: /path/to/data/processed
train: images/train
val: images/val
test: images/test

nc: {num_classes}
names:
  - {class_1}
  - {class_2}
  - ...
```

### 2. Verify Directory Structure

```python
def verify_structure(base_path: Path) -> dict:
    expected = [
        "images/train",
        "images/val",
        "images/test",
        "labels/train",
        "labels/val",
        "labels/test",
        "data.yaml"
    ]

    results = {}
    for path in expected:
        full_path = base_path / path
        exists = full_path.exists()
        results[path] = {
            'exists': exists,
            'count': len(list(full_path.glob('*'))) if exists and full_path.is_dir() else None
        }
    return results
```

Report:
```
📊 Dataset Structure Verification

./data/processed/
├── images/
│   ├── train/     {n} images ✅
│   ├── val/       {n} images ✅
│   └── test/      {n} images ✅
├── labels/
│   ├── train/     {n} labels ✅
│   ├── val/       {n} labels ✅
│   └── test/      {n} labels ✅
└── data.yaml      ✅
```

### 3. Compute Dataset Checksum

```python
import hashlib
import json

def compute_dataset_checksum(base_path: Path) -> str:
    """Compute checksum for reproducibility tracking."""
    hasher = hashlib.sha256()

    # Hash data.yaml content
    data_yaml = base_path / "data.yaml"
    hasher.update(data_yaml.read_bytes())

    # Hash file listing (not contents - too slow)
    file_list = sorted([
        str(p.relative_to(base_path))
        for p in base_path.rglob('*')
        if p.is_file()
    ])
    hasher.update(json.dumps(file_list).encode())

    return hasher.hexdigest()[:16]
```

### 4. Compute Final Statistics

```python
def compute_statistics(base_path: Path, class_names: list) -> dict:
    stats = {
        'total_images': 0,
        'total_instances': 0,
        'splits': {},
        'class_counts': {c: 0 for c in class_names},
        'image_sizes': {'widths': [], 'heights': []}
    }

    for split in ['train', 'val', 'test']:
        img_dir = base_path / 'images' / split
        lbl_dir = base_path / 'labels' / split

        images = list(img_dir.glob('*'))
        stats['splits'][split] = len(images)
        stats['total_images'] += len(images)

        for lbl_file in lbl_dir.glob('*.txt'):
            with open(lbl_file) as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        class_id = int(parts[0])
                        stats['class_counts'][class_names[class_id]] += 1
                        stats['total_instances'] += 1

    stats['avg_instances_per_image'] = stats['total_instances'] / stats['total_images']
    return stats
```

### 5. Generate Handoff Artifact

```python
from datetime import datetime

handoff = {
    'dataset_path': str(base_path.absolute()),
    'format': 'yolo',
    'data_yaml_path': str(base_path / 'data.yaml'),

    'splits': {
        'train': stats['splits']['train'],
        'val': stats['splits']['val'],
        'test': stats['splits']['test']
    },

    'classes': {
        'names': class_names,
        'counts': stats['class_counts']
    },

    'statistics': {
        'total_images': stats['total_images'],
        'total_instances': stats['total_instances'],
        'avg_instances_per_image': stats['avg_instances_per_image'],
        'image_sizes': {
            'min': stats['image_sizes']['min'],
            'max': stats['image_sizes']['max'],
            'median': stats['image_sizes']['median']
        }
    },

    'quality_report_path': str(base_path.parent / 'quality-report.md'),
    'validation_passed': True,
    'warnings': warnings,

    'annotation_source': 'vfrog',
    'vfrog_project_id': vfrog_project_id,

    'checksum': dataset_checksum,
    'created_at': datetime.utcnow().isoformat()
}
```

### 6. Final Report

```
═══════════════════════════════════════════════════
📊 DATASET PREPARATION COMPLETE
═══════════════════════════════════════════════════

Project: {project_name}
Location: ./data/processed/

═══════════════════════════════════════════════════
DATASET SUMMARY
═══════════════════════════════════════════════════

Total images: {count}
Total instances: {count}
Classes: {count}

Split Distribution:
  Train: {count} images ({percent}%)
  Val:   {count} images ({percent}%)
  Test:  {count} images ({percent}%)

Class Distribution:
  {class_name}: {count} instances
  ...

Average objects per image: {avg}

═══════════════════════════════════════════════════
QUALITY STATUS
═══════════════════════════════════════════════════

Validation: ✅ PASSED
Annotation source: vfrog ({project_id})
Checksum: {checksum}

{if warnings}
⚠️ Warnings:
{warning_list}
{/if}

═══════════════════════════════════════════════════
FILES GENERATED
═══════════════════════════════════════════════════

✅ data.yaml           - Training configuration
✅ quality-report.md   - Data quality analysis

═══════════════════════════════════════════════════
READY FOR TRAINING
═══════════════════════════════════════════════════

Your dataset is ready! The Training Agent can now:
- Configure model architecture
- Set up training parameters
- Start training

Next steps:
  croak recommend  - Get architecture recommendation
  croak train      - Start training with defaults

🐸 Let's train a model!
```

### 7. Update Pipeline State

```yaml
current_stage: "training"

stages_completed:
  - "data_scan"
  - "data_validation"
  - "data_annotation"
  - "data_split"
  - "data_preparation"

artifacts:
  dataset:
    path: "./data/processed"
    format: "yolo"
    version: "v1.0.0"
    checksum: "{checksum}"
    data_yaml_path: "./data/processed/data.yaml"
    classes: {class_list}
    splits:
      train: {count}
      val: {count}
      test: {count}
    quality_report_path: "./data/quality-report.md"
    vfrog_project_id: "{project_id}"
```

## Outputs

- `dataset_path`: Final dataset location
- `data_yaml`: Path to training configuration
- `handoff_artifact`: Complete artifact for Training Agent

## Completion

Data preparation workflow complete.

Handoff to Training Agent ready.

WORKFLOW COMPLETE - User can now run `croak train` or `croak recommend`
