# Data Quality Checklist

## Quick Validation

Run these checks before training:

```
☐ All images readable (no corrupt files)
☐ All images have corresponding labels
☐ Label format matches expected (YOLO)
☐ At least 100 images total
☐ At least 50 instances per class
☐ Class imbalance ratio < 10:1
☐ No duplicate images between splits
```

## Image Quality

### File Integrity

```python
from PIL import Image
from pathlib import Path

def check_images(directory):
    issues = []
    for path in Path(directory).rglob('*'):
        if path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
            try:
                with Image.open(path) as img:
                    img.verify()
            except Exception as e:
                issues.append((path, str(e)))
    return issues
```

**Pass:** All images open without errors

**Fail Actions:**
- Remove corrupt files
- Re-download or re-capture
- Check storage integrity

### Resolution Consistency

| Check | Threshold | Action |
|-------|-----------|--------|
| Min dimension | > 320px | Exclude smaller |
| Max dimension | < 4096px | Resize larger |
| Aspect ratio | 0.5 - 2.0 | Review outliers |

**Best Practice:** Resize to consistent size before training (YOLO handles this, but consistency helps)

### Image Content

Visual inspection (sample 10-20 images):
- ☐ Images are relevant to task
- ☐ Target objects are visible
- ☐ Sufficient lighting
- ☐ Not too blurry
- ☐ Representative of deployment conditions

## Annotation Quality

### Format Validation (YOLO)

```
# Correct format (each line):
class_id x_center y_center width height

# All values normalized 0-1 except class_id (integer)
0 0.456 0.523 0.234 0.345  ✓
1 0.123 0.789 0.100 0.200  ✓
0 456 523 234 345           ✗ (not normalized)
```

### Coverage Check

```python
def check_coverage(images_dir, labels_dir):
    images = set(p.stem for p in Path(images_dir).glob('*'))
    labels = set(p.stem for p in Path(labels_dir).glob('*.txt'))

    missing_labels = images - labels
    extra_labels = labels - images

    return {
        'total_images': len(images),
        'missing_labels': missing_labels,
        'extra_labels': extra_labels,
        'coverage': len(labels & images) / len(images)
    }
```

**Target:** 100% coverage (every image has label)

### Annotation Accuracy

Visual review (sample 20-30 images):
- ☐ Boxes are tight around objects (not too loose)
- ☐ All instances labeled (nothing missed)
- ☐ Correct class assigned
- ☐ Consistent across similar images
- ☐ Partial objects labeled (edge cases)

### Common Annotation Issues

| Issue | Impact | Fix |
|-------|--------|-----|
| Loose boxes | Poor localization | Re-annotate tighter |
| Missing instances | Low recall | Complete annotations |
| Wrong class | Confusion | Re-verify labels |
| Inconsistent | Noise in training | Establish guidelines |

## Class Distribution

### Balance Analysis

```python
def analyze_classes(labels_dir, class_names):
    counts = {name: 0 for name in class_names}

    for label_file in Path(labels_dir).glob('*.txt'):
        with open(label_file) as f:
            for line in f:
                class_id = int(line.split()[0])
                counts[class_names[class_id]] += 1

    return counts
```

### Thresholds

| Check | Warning | Error |
|-------|---------|-------|
| Min instances/class | < 50 | < 20 |
| Max imbalance ratio | > 10:1 | > 50:1 |
| Total instances | < 500 | < 100 |

### Handling Imbalance

**Options:**
1. Collect more data for minority classes
2. Oversample minority classes (duplicate images)
3. Use augmentation to balance
4. Apply class weighting in training

## Dataset Splits

### Split Ratios

| Split | Purpose | Recommended |
|-------|---------|-------------|
| Train | Learning | 70-80% |
| Val | Hyperparameter tuning | 10-20% |
| Test | Final evaluation | 10-15% |

### Stratification

Ensure class proportions are similar across splits:

```
Class     Train   Val    Test   (should be similar)
person    72%     75%    73%    ✓
car       20%     18%    21%    ✓
bicycle   8%      7%     6%     ✓
```

### No Data Leakage

Critical checks:
- ☐ Same image not in multiple splits
- ☐ Similar images (same scene) in same split
- ☐ Temporal sequences kept together

## Object Size Distribution

### COCO Size Categories

| Size | Pixels | Example |
|------|--------|---------|
| Small | < 32×32 | Distant pedestrians |
| Medium | 32-96×96 | Cars at intersection |
| Large | > 96×96 | Close-up objects |

### Check Distribution

```python
def analyze_sizes(labels_dir, img_sizes):
    sizes = {'small': 0, 'medium': 0, 'large': 0}

    for label_file in Path(labels_dir).glob('*.txt'):
        img_w, img_h = img_sizes[label_file.stem]
        with open(label_file) as f:
            for line in f:
                _, _, _, w, h = map(float, line.split())
                area = (w * img_w) * (h * img_h)
                if area < 32*32:
                    sizes['small'] += 1
                elif area < 96*96:
                    sizes['medium'] += 1
                else:
                    sizes['large'] += 1

    return sizes
```

### If Small Objects Dominate

- Increase image size (imgsz=1280)
- Use YOLOv11 (better small detection)
- Consider multi-scale training

## Final Checklist

Before starting training:

```
Data Integrity
☐ All images readable
☐ All images have labels
☐ Labels in correct format

Quality
☐ Annotations visually verified (sample)
☐ Boxes tight around objects
☐ No missing instances

Distribution
☐ At least 100 images total
☐ At least 50 instances per class
☐ Class imbalance < 10:1
☐ Train/val/test splits created
☐ Stratification applied
☐ No data leakage

Documentation
☐ Class names documented
☐ data.yaml created
☐ Quality report generated
```
