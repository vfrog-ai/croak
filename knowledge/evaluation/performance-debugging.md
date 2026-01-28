# Performance Debugging Guide

## Diagnostic Framework

Use this guide when:
- Model isn't learning at all
- Performance is worse than expected
- Production performance dropped
- Certain classes are failing

## Model Not Learning At All

### Symptoms
- mAP stays at or near 0
- Loss may decrease but predictions are empty
- Model outputs nothing or random boxes

### Diagnostic Steps

**Step 1: Check 10 random samples**
```python
# Visually verify annotations are correct
from ultralytics import YOLO
import cv2

# Load a few images and their labels
# Draw boxes to verify they're correct
```

Questions to answer:
- Are boxes in the right places?
- Are class IDs correct?
- Are there any empty label files?

**Step 2: Verify data.yaml**
```yaml
# Check these match exactly:
names:
  0: person    # ← Must match class_id 0 in labels
  1: car       # ← Must match class_id 1 in labels
```

**Step 3: Check annotation format**
```
# Correct YOLO format:
# class_id x_center y_center width height
# All values normalized 0-1
0 0.5 0.5 0.3 0.4  ✓ Correct
0 100 200 50 80    ✗ Wrong (not normalized)
1 0.5 0.5 0.3 0.4  ✗ Wrong if class 1 doesn't exist
```

**Step 4: Verify image loading**
```python
# Ensure images load correctly
from PIL import Image
img = Image.open(image_path)
img.verify()  # Check file integrity
```

### Common Fixes
1. Re-export annotations from vfrog in YOLO format
2. Fix class ID mapping in data.yaml
3. Remove corrupt images
4. Ensure all images have labels

## Poor Accuracy (mAP < 0.5)

### Possible Causes

**1. Insufficient data**
```
Symptom: Model learns but plateaus early
Check: Number of images per class
Fix: Collect more data or use heavy augmentation
```

**2. Class imbalance**
```
Symptom: Good on majority classes, bad on minority
Check: Instance count per class
Fix: Oversample minority, use class weights
```

**3. Model too small**
```
Symptom: Both train and val loss plateau high
Check: Model complexity vs data complexity
Fix: Try larger model (yolov8s → yolov8m)
```

**4. Annotation quality**
```
Symptom: Loss is normal but mAP is low
Check: Random sample of annotations
Fix: Re-annotate with vfrog, ensure consistency
```

### Diagnostic Checklist
- [ ] At least 100 images total?
- [ ] At least 50 instances per class?
- [ ] Annotations tight around objects?
- [ ] Consistent labeling across images?
- [ ] No missing annotations?
- [ ] Model appropriate for data size?

## Production Performance Drop

### Scenario
Model worked well in evaluation but fails in production

### Diagnostic Steps

**Step 1: Compare image distributions**

```python
# Analyze production images vs training
def compare_distributions(train_dir, prod_samples):
    # Compare:
    # - Brightness
    # - Resolution
    # - Object sizes
    # - Aspect ratios
```

**Step 2: Check for domain shift**

| Factor | Training | Production | Issue? |
|--------|----------|------------|--------|
| Lighting | Indoor | Outdoor | Yes |
| Resolution | 1080p | 480p | Yes |
| Camera angle | Front | Side | Yes |
| Object types | All trained | New types | Yes |

**Step 3: Analyze confidence scores**

```python
# If production confidence is systematically lower
# → Domain shift is likely

# Compare average confidence:
# Training images: avg conf = 0.85
# Production images: avg conf = 0.45  ← Problem!
```

### Common Causes

**1. Lighting changes**
```
Training: Well-lit indoor
Production: Variable outdoor lighting

Fix: Add lighting augmentation, collect production samples
```

**2. Camera/resolution changes**
```
Training: High-res professional photos
Production: Low-res webcam

Fix: Train with varied resolutions, add compression artifacts
```

**3. New object variations**
```
Training: Cars from side view
Production: Cars from aerial view

Fix: Collect examples of new variations
```

**4. Seasonal/temporal drift**
```
Training: Summer images
Production: Winter (snow, different lighting)

Fix: Collect data across conditions
```

### Fix Strategy

1. **Quick fix:** Adjust confidence threshold
2. **Medium fix:** Fine-tune on production samples
3. **Best fix:** Collect production data, retrain

## Single Class Failing

### Diagnostic Steps

**Step 1: Check instance count**
```
Class       Instances    AP@50
person      5000         0.85  ✓
car         3000         0.80  ✓
bicycle     200          0.45  ← Low
```

**Step 2: Analyze class characteristics**

Questions:
- Is this class visually similar to another?
- Is this class much smaller/larger than others?
- Is this class often occluded?
- Are annotations consistent for this class?

**Step 3: Review sample predictions**

```python
# Look at false negatives (missed detections)
# Look at false positives (wrong detections)
# Look at misclassifications (confused with other class)
```

### Common Patterns

**Similar appearance to another class**
```
Symptom: Class A often predicted as Class B
Fix: More training data showing differences
     Better annotation guidelines
```

**Small object class**
```
Symptom: Works for close objects, fails for distant
Fix: Increase imgsz (640 → 1280)
     Use YOLOv11 for small objects
```

**Rare poses/views**
```
Symptom: Works for common views, fails for unusual
Fix: Collect data showing varied poses
     Add rotation augmentation
```

## Overfitting Symptoms

### How to Detect

```
Epoch   Train mAP   Val mAP   Gap
10      0.60        0.55      0.05  ✓
20      0.75        0.65      0.10  ✓
30      0.85        0.68      0.17  ⚠️
40      0.92        0.65      0.27  ❌ Overfitting
```

### Solutions by Severity

**Mild (gap < 0.15):**
- Enable early stopping
- Add light augmentation

**Moderate (gap 0.15-0.25):**
- Increase augmentation
- Reduce model size
- Add dropout

**Severe (gap > 0.25):**
- Need more training data
- Significantly reduce model
- Heavy regularization

## Quick Diagnosis Flowchart

```
Model not performing well?
│
├─ mAP ≈ 0?
│   └─ Check: annotations, data.yaml, paths
│
├─ mAP < 0.3?
│   └─ Check: data quality, class balance, model size
│
├─ mAP 0.3-0.5?
│   └─ Check: hyperparameters, augmentation, more epochs
│
├─ mAP 0.5-0.7?
│   └─ Check: per-class, try larger model, more data
│
└─ Production drop?
    └─ Check: domain shift, confidence distribution
```
