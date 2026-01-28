# Detection Metrics Explained

## Key Metrics Summary

| Metric | What It Measures | Good Value | Use Case |
|--------|------------------|------------|----------|
| mAP@50 | Detection accuracy (loose) | > 0.7 | General assessment |
| mAP@50-95 | Detection accuracy (strict) | > 0.5 | Precise localization |
| Precision | Correct positives | > 0.8 | Low false alarms |
| Recall | Found all objects | > 0.8 | Missing none |
| F1 | Balance of P and R | > 0.8 | Balanced performance |

## IoU (Intersection over Union)

### Definition

```
IoU = Area of Overlap / Area of Union
```

### Visual

```
┌─────────────┐
│  Predicted  │
│    ┌────────┼────┐
│    │████████│    │
│    │████████│    │  Overlap (Intersection)
└────┼────────┘    │
     │  Ground     │
     │  Truth      │
     └─────────────┘

IoU = Intersection Area / (Pred Area + GT Area - Intersection)
```

### IoU Thresholds

- **IoU = 0.5:** Loose match (allows 50% mismatch)
- **IoU = 0.75:** Strict match
- **IoU = 0.95:** Very strict (almost perfect box)

## Precision

### Definition

```
Precision = True Positives / (True Positives + False Positives)
```

### Plain English
"Of all the boxes the model drew, how many were correct?"

### When to Prioritize
- False alarms are costly (e.g., medical diagnosis)
- Downstream systems can't handle noise
- User trust requires low false positive rate

### Example
```
Model predicts 100 boxes
80 are correct detections
20 are false positives

Precision = 80/100 = 0.80 (80%)
```

## Recall

### Definition

```
Recall = True Positives / (True Positives + False Negatives)
```

### Plain English
"Of all the objects that exist, how many did the model find?"

### When to Prioritize
- Missing objects is costly (e.g., security, safety)
- Better to have false positives than miss real ones
- Comprehensive detection required

### Example
```
Image has 100 real objects
Model finds 75 of them
Model misses 25

Recall = 75/100 = 0.75 (75%)
```

## F1 Score

### Definition

```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

### Plain English
"Harmonic mean of precision and recall - balances both"

### Interpretation

| F1 | Assessment |
|----|------------|
| > 0.9 | Excellent |
| 0.8-0.9 | Good |
| 0.7-0.8 | Acceptable |
| < 0.7 | Needs improvement |

## Average Precision (AP)

### Definition
Area under the Precision-Recall curve for one class

### Calculation
1. Sort predictions by confidence
2. Calculate P and R at each threshold
3. Integrate (area under curve)

### Why Use AP?
- Single number summarizes all thresholds
- Accounts for confidence ranking
- Standard metric for object detection

## Mean Average Precision (mAP)

### mAP@50

```
mAP@50 = Average of AP@50 across all classes
```

- Uses IoU threshold of 0.5
- Most commonly reported metric
- More forgiving of localization errors

### mAP@50-95

```
mAP@50-95 = Average mAP at IoU thresholds [0.5, 0.55, 0.60, ..., 0.95]
```

- Averages across multiple IoU thresholds
- Rewards precise localization
- More challenging metric
- Used by COCO benchmark

### Relationship

```
mAP@50 > mAP@50-95 (always)

Typical ratio: mAP@50-95 ≈ 0.6-0.7 × mAP@50
```

## Interpreting Metrics

### Good Performance Benchmarks

| Dataset Type | mAP@50 | mAP@50-95 |
|--------------|--------|-----------|
| Easy (few classes, distinct) | > 0.85 | > 0.65 |
| Medium (moderate complexity) | > 0.75 | > 0.50 |
| Hard (many classes, similar) | > 0.60 | > 0.40 |

### Red Flags

| Observation | Likely Issue |
|-------------|--------------|
| mAP@50 high, mAP@50-95 low | Localization is poor |
| Precision high, Recall low | Missing many objects |
| Recall high, Precision low | Too many false positives |
| Large variance across classes | Class imbalance |

## Confidence Threshold

### What It Is
Minimum confidence to consider a prediction valid

### Trade-off

```
Higher threshold → Higher precision, Lower recall
Lower threshold → Lower precision, Higher recall
```

### Finding Optimal Threshold

1. Plot precision vs recall at different thresholds
2. Choose threshold that:
   - Maximizes F1 (balanced)
   - Meets precision requirement (if specified)
   - Meets recall requirement (if specified)

### Typical Ranges

| Use Case | Threshold |
|----------|-----------|
| High precision needed | 0.5-0.7 |
| Balanced | 0.25-0.5 |
| High recall needed | 0.1-0.25 |

## Per-Class Analysis

### Why It Matters
- Aggregate mAP hides class-level issues
- Some classes may perform well while others fail
- Imbalanced datasets skew averages

### What to Look For

```
Class       AP@50    Instances
───────────────────────────────
Person      0.85     5000
Car         0.80     3000
Bicycle     0.45     200      ← Problem: Low AP
Skateboard  0.30     50       ← Problem: Low AP, few samples
```

### Interpretation
- Low AP + Low instances → Need more training data
- Low AP + High instances → Model struggles with this class
- High AP + Low instances → Class is distinct/easy

## Size-Based Analysis

### COCO Size Categories

| Size | Pixel Area | Examples |
|------|------------|----------|
| Small | < 32×32 | Distant objects, small items |
| Medium | 32×32 to 96×96 | Most objects |
| Large | > 96×96 | Close/prominent objects |

### Typical Performance Pattern

```
Large objects:  AP = 0.70  (easiest)
Medium objects: AP = 0.50
Small objects:  AP = 0.25  (hardest)
```

### Improving Small Object Detection
- Increase input image size
- Use YOLOv11 (improved small detection)
- Multi-scale training
- Data augmentation focused on small objects
