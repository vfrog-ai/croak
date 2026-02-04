# Step 5: Create Dataset Splits

## Execution Rules
- 🐸 ALWAYS use stratified splitting to maintain class proportions
- ✅ ALWAYS ensure no data leakage between splits
- ⚠️ ALWAYS warn if test set is too small for reliable evaluation
- 📊 ALWAYS report split statistics

## Your Task
Create train/validation/test splits with proper stratification.

## Execution Sequence

### 1. Get Split Configuration

Default splits from config:
```yaml
splits:
  train: 0.8   # 80%
  val: 0.15    # 15%
  test: 0.05   # 5%
```

Confirm with user:
> "Let's split your dataset for training.
>
> **Proposed splits:**
>
> | Split | Percent | Images |
> |-------|---------|--------|
> | Train | 80%     | {n}    |
> | Val   | 15%     | {n}    |
> | Test  | 5%      | {n}    |
>
> **What each split is for:**
> - **Train:** Model learns from these
> - **Val:** Used during training to prevent overfitting
> - **Test:** Final evaluation (never seen during training)
>
> Use these splits? [Y/n or enter custom like '70/20/10']"

### 2. Validate Split Sizes

```python
def validate_splits(total: int, train: float, val: float, test: float) -> list:
    warnings = []

    test_count = int(total * test)
    if test_count < 20:
        warnings.append(f"Test set only has {test_count} images. "
                       "Recommend at least 20 for reliable evaluation.")

    val_count = int(total * val)
    if val_count < 10:
        warnings.append(f"Validation set only has {val_count} images. "
                       "Recommend at least 10.")

    return warnings
```

### 3. Perform Stratified Split

```python
from sklearn.model_selection import train_test_split
import numpy as np

def stratified_split(images: list, labels: list,
                     train_ratio: float, val_ratio: float, test_ratio: float,
                     seed: int = 42) -> dict:
    """
    Split dataset maintaining class proportions in each split.
    """
    # Get primary class for each image (for stratification)
    primary_classes = [get_primary_class(lbl) for lbl in labels]

    # First split: separate test set
    train_val_imgs, test_imgs, train_val_lbls, test_lbls = train_test_split(
        images, labels,
        test_size=test_ratio,
        stratify=primary_classes,
        random_state=seed
    )

    # Second split: separate train and val
    val_ratio_adjusted = val_ratio / (train_ratio + val_ratio)
    train_val_classes = [get_primary_class(lbl) for lbl in train_val_lbls]

    train_imgs, val_imgs, train_lbls, val_lbls = train_test_split(
        train_val_imgs, train_val_lbls,
        test_size=val_ratio_adjusted,
        stratify=train_val_classes,
        random_state=seed
    )

    return {
        'train': (train_imgs, train_lbls),
        'val': (val_imgs, val_lbls),
        'test': (test_imgs, test_lbls)
    }
```

### 4. Verify No Data Leakage

```python
def check_data_leakage(splits: dict) -> bool:
    """Ensure no image appears in multiple splits."""
    train_set = set(splits['train'][0])
    val_set = set(splits['val'][0])
    test_set = set(splits['test'][0])

    assert train_set.isdisjoint(val_set), "Train/val overlap!"
    assert train_set.isdisjoint(test_set), "Train/test overlap!"
    assert val_set.isdisjoint(test_set), "Val/test overlap!"

    return True
```

### 5. Copy Files to Split Directories

```python
from pathlib import Path
import shutil

def organize_splits(splits: dict, output_dir: Path):
    for split_name, (images, labels) in splits.items():
        img_dir = output_dir / "images" / split_name
        lbl_dir = output_dir / "labels" / split_name

        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        for img_path, lbl_path in zip(images, labels):
            shutil.copy(img_path, img_dir / img_path.name)
            shutil.copy(lbl_path, lbl_dir / lbl_path.name)
```

Progress:
> "Creating dataset splits...
>
> [████████████████████] 100%
>
> Copying files to:
> - ./data/processed/images/train/ ({n} images)
> - ./data/processed/images/val/ ({n} images)
> - ./data/processed/images/test/ ({n} images)"

### 6. Report Split Statistics

```
📊 Dataset Split Complete

═══════════════════════════════════════════════════
SPLIT SUMMARY
═══════════════════════════════════════════════════

Split    Images    Instances    Percent
──────────────────────────────────────────────
Train    {n}       {instances}  {pct}%
Val      {n}       {instances}  {pct}%
Test     {n}       {instances}  {pct}%
──────────────────────────────────────────────
Total    {n}       {instances}  100%

═══════════════════════════════════════════════════
CLASS DISTRIBUTION BY SPLIT
═══════════════════════════════════════════════════

Class          Train    Val      Test
──────────────────────────────────────────────
{class_1}      {n}      {n}      {n}
{class_2}      {n}      {n}      {n}
...

✅ Stratification maintained - class proportions consistent across splits.

═══════════════════════════════════════════════════
DATA INTEGRITY
═══════════════════════════════════════════════════

✅ No data leakage detected
✅ All images have corresponding labels
✅ Random seed: {seed} (reproducible)

{warnings_if_any}
```

### 7. Update Pipeline State

```yaml
artifacts:
  dataset:
    splits:
      train: {count}
      val: {count}
      test: {count}
    split_seed: {seed}
    stratified: true

stages_completed:
  - "data_init"
  - "data_scan"
  - "data_validation"
  - "data_annotation"
  - "data_split"
```

## Outputs

- `train_split`: Images and labels for training
- `val_split`: Images and labels for validation
- `test_split`: Images and labels for final evaluation

## Completion

> "✅ Dataset splits created!
>
> Your data is organized and ready for training.
>
> Next: Export the final dataset configuration
>
> Run: `croak export` or continue with `croak prepare`"

WAIT for user before loading step-06-export.md
