# Step 3: Validate Data Quality

## Execution Rules
- 🐸 ALWAYS check every image can be opened
- ✅ ALWAYS report corrupt or problematic files
- ⚠️ NEVER proceed to training if validation fails
- 📊 ALWAYS generate quality report

## Your Task
Perform comprehensive data quality validation.

## Execution Sequence

### 1. Validate Image Integrity

```python
from PIL import Image
from pathlib import Path

def validate_image(path: Path) -> dict:
    try:
        with Image.open(path) as img:
            img.verify()  # Check file integrity
        with Image.open(path) as img:
            img.load()    # Actually load pixels
        return {'path': path, 'valid': True}
    except Exception as e:
        return {'path': path, 'valid': False, 'error': str(e)}
```

### 2. Check for Duplicates

```python
import hashlib

def find_duplicates(images: list) -> list:
    hashes = {}
    duplicates = []
    for img_path in images:
        h = hashlib.md5(open(img_path, 'rb').read()).hexdigest()
        if h in hashes:
            duplicates.append((img_path, hashes[h]))
        else:
            hashes[h] = img_path
    return duplicates
```

### 3. Validate Existing Annotations (if present)

For YOLO format:
```python
def validate_yolo_annotation(txt_path: Path, img_size: tuple) -> dict:
    issues = []
    with open(txt_path) as f:
        for line_num, line in enumerate(f, 1):
            parts = line.strip().split()
            if len(parts) != 5:
                issues.append(f"Line {line_num}: Expected 5 values, got {len(parts)}")
            else:
                class_id, x, y, w, h = map(float, parts)
                if not (0 <= x <= 1 and 0 <= y <= 1):
                    issues.append(f"Line {line_num}: Center coordinates out of range")
                if not (0 < w <= 1 and 0 < h <= 1):
                    issues.append(f"Line {line_num}: Width/height out of range")
    return {'valid': len(issues) == 0, 'issues': issues}
```

### 4. Analyze Class Distribution (if annotations exist)

```python
def analyze_class_distribution(annotations: list) -> dict:
    class_counts = {}
    for ann in annotations:
        for obj in ann['objects']:
            cls = obj['class']
            class_counts[cls] = class_counts.get(cls, 0) + 1
    return class_counts
```

### 5. Generate Quality Report

```
📊 Data Quality Report

═══════════════════════════════════════════════════
VALIDATION SUMMARY
═══════════════════════════════════════════════════

Overall Status: {PASS / FAIL / WARNINGS}

═══════════════════════════════════════════════════
IMAGE VALIDATION
═══════════════════════════════════════════════════

Total images: {count}
Valid: {valid_count} ✅
Corrupt: {corrupt_count} {❌ if > 0 else ✅}

{if corrupt_count > 0}
Corrupt files:
{corrupt_file_list}

Action required: Remove or replace corrupt files before proceeding.
{/if}

Duplicates found: {duplicate_count}
{if duplicate_count > 0}
{duplicate_list}
Recommendation: Consider removing duplicates to avoid data leakage.
{/if}

═══════════════════════════════════════════════════
SIZE CONSISTENCY
═══════════════════════════════════════════════════

Size distribution:
  Min: {min_size}
  Max: {max_size}
  Median: {median_size}
  Std dev: {std_dev}

{if high_variance}
⚠️ High variance in image sizes detected.
   Training will resize all images to {target_size}.
   Very small images may lose detail.
   Very large images will be downscaled.
{else}
✅ Image sizes are reasonably consistent.
{/if}

═══════════════════════════════════════════════════
ANNOTATION VALIDATION
═══════════════════════════════════════════════════

{if no_annotations}
No existing annotations found.
Images will be annotated via vfrog in the next step.
{else}
Format: {format}
Coverage: {annotated_count}/{total_count} ({percent}%)

{if coverage < 100}
⚠️ {missing_count} images missing annotations.
   All images must be annotated before training.
{/if}

Annotation issues: {issue_count}
{if issue_count > 0}
{issue_list}
{/if}
{/if}

═══════════════════════════════════════════════════
CLASS DISTRIBUTION
═══════════════════════════════════════════════════

{if has_annotations}
Class            Instances    Percent
────────────────────────────────────────
{class_table}

{if imbalanced}
⚠️ Class imbalance detected
   Ratio: {max_class}:{min_class} = {ratio}:1

   The model may underperform on minority classes.
   Recommendations:
   - Collect more data for minority classes
   - Apply augmentation (will be configured during training)
   - Consider class weighting
{else}
✅ Class distribution is reasonably balanced.
{/if}
{/if}

═══════════════════════════════════════════════════
RECOMMENDATIONS
═══════════════════════════════════════════════════

{recommendation_list}
```

### 6. Save Quality Report

```python
report_path = Path("data/quality-report.md")
report_path.write_text(report_content)
```

### 7. Update Pipeline State

```yaml
artifacts:
  dataset:
    quality_report_path: "data/quality-report.md"
    validation_passed: {true/false}
    warnings: {warning_list}

stages_completed:
  - "data_init"
  - "data_scan"
  - "data_validation"
```

## Validation Rules

| Check | Threshold | Level |
|-------|-----------|-------|
| Corrupt images | 0 | ERROR |
| Missing annotations | 0% (at training) | ERROR |
| Class imbalance ratio | > 10:1 | WARNING |
| Min instances per class | < 50 | WARNING |
| Image count | < 100 | WARNING |

## Outputs

- `quality_report`: Path to generated report
- `validation_status`: PASS / FAIL / WARNINGS

## Completion

{if validation_passed}
> "✅ Validation complete! Your data looks good.
>
> {if has_annotations}
> Annotations found. Ready to split dataset.
> Next: `croak split`
> {else}
> No annotations found. Let's get them labeled.
> Next: `croak annotate`
> {/if}"
{else}
> "❌ Validation failed. Please fix the issues above before continuing.
>
> Most common fixes:
> - Remove corrupt images
> - Complete missing annotations
> - Address class imbalance"
{/if}

WAIT for user before loading next step
