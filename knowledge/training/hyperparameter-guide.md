# Hyperparameter Guide

## Quick Reference

| Parameter | Default | Range | When to Adjust |
|-----------|---------|-------|----------------|
| epochs | 100 | 50-300 | More data → more epochs |
| batch | 16 | 4-64 | Limited by GPU memory |
| imgsz | 640 | 320-1280 | Small objects → larger |
| lr0 | 0.01 | 0.001-0.1 | Rarely needs change |
| patience | 20 | 10-50 | Early stopping trigger |

## Epochs

### How to Choose

```
Dataset Size    Recommended Epochs
< 500 images    50-100
500-2000        100-150
2000-10000      150-200
> 10000         200-300
```

### Why These Values

- Too few: Model underfits
- Too many: Wastes compute (early stopping helps)
- YOLO uses early stopping by default

### Adjustment Strategy

1. Start with 100 epochs
2. Watch validation loss
3. If still improving at end, increase
4. If plateaus early, decrease or check data

## Batch Size

### Selection Guide

| GPU Memory | YOLOv8n | YOLOv8s | YOLOv8m |
|------------|---------|---------|---------|
| 8 GB | 32 | 16 | 8 |
| 12 GB | 64 | 32 | 16 |
| 16 GB | 64 | 32 | 16 |
| 24 GB | 64 | 64 | 32 |

### Effects

- **Larger batch:** Faster training, more stable gradients
- **Smaller batch:** More regularization, fits in memory

### If Out of Memory

1. Reduce batch size by half
2. If still OOM, reduce image size
3. Consider gradient accumulation

## Image Size (imgsz)

### Options

| Size | Speed | Accuracy | Memory |
|------|-------|----------|--------|
| 320 | Fastest | Lower | Low |
| 480 | Fast | Good | Medium |
| 640 | Balanced | Good | Medium |
| 800 | Slower | Better | High |
| 1280 | Slowest | Best | Very High |

### When to Increase

- Small objects in images (< 32px)
- High-resolution source images
- Accuracy is priority over speed

### When to Decrease

- Large objects only
- Speed is critical
- Limited GPU memory

## Learning Rate

### Default: 0.01

Works for most cases. Don't change unless:

**Reduce (0.001-0.005) when:**
- Training is unstable (loss oscillates)
- Fine-tuning pretrained model
- Very small dataset

**Increase (0.02-0.05) when:**
- Training is very slow
- Large dataset
- Training from scratch (rare)

### Learning Rate Schedule

YOLO uses cosine decay:
- Starts at `lr0`
- Ends at `lr0 * lrf` (default: 0.01)
- Smooth decay over training

## Optimizer

### AdamW (Default, Recommended)

```yaml
optimizer: AdamW
momentum: 0.937
weight_decay: 0.0005
```

Best for most cases. Adaptive learning rates per parameter.

### SGD (Alternative)

```yaml
optimizer: SGD
momentum: 0.937
nesterov: true
```

Sometimes better for very large datasets.

## Augmentation Parameters

### Standard Augmentation

```yaml
# Geometric
translate: 0.1      # Random translation ±10%
scale: 0.5          # Random scaling 50%-150%
fliplr: 0.5         # Horizontal flip 50%
flipud: 0.0         # Vertical flip (usually off)

# Color
hsv_h: 0.015        # Hue ±1.5%
hsv_s: 0.7          # Saturation ±70%
hsv_v: 0.4          # Value ±40%
```

### Heavy Augmentation (for overfitting)

```yaml
mosaic: 1.0         # Always use mosaic
mixup: 0.1          # 10% mixup
copy_paste: 0.1     # 10% copy-paste
degrees: 10         # ±10° rotation
scale: 0.9          # More aggressive scaling
```

### Light Augmentation (small dataset)

```yaml
mosaic: 0.5         # 50% mosaic
mixup: 0.0          # No mixup
translate: 0.05     # Less translation
scale: 0.3          # Less scaling
```

## Early Stopping

### patience Parameter

- Default: 20 epochs
- Model stops if mAP doesn't improve for `patience` epochs

### Adjustment

| Scenario | Patience |
|----------|----------|
| Quick iteration | 10 |
| Standard training | 20 |
| Want to ensure convergence | 50 |

## Warmup

### Parameters

```yaml
warmup_epochs: 3        # Epochs of warmup
warmup_momentum: 0.8    # Starting momentum
warmup_bias_lr: 0.1     # Starting bias LR
```

### Why Warmup Helps

- Prevents early training instability
- Allows model to adjust to learning rate
- Usually don't need to change

## Complete Example Configurations

### Small Dataset (<500 images)

```yaml
epochs: 100
batch: 16
imgsz: 640
lr0: 0.01
patience: 30
mosaic: 0.5
mixup: 0.0
scale: 0.3
```

### Medium Dataset (500-2000 images)

```yaml
epochs: 150
batch: 16
imgsz: 640
lr0: 0.01
patience: 20
mosaic: 1.0
mixup: 0.0
```

### Large Dataset (>2000 images)

```yaml
epochs: 200
batch: 32
imgsz: 640
lr0: 0.01
patience: 20
mosaic: 1.0
mixup: 0.1
```

### Small Objects

```yaml
imgsz: 1280
batch: 8  # Reduced for memory
scale: 0.3
mosaic: 1.0
```
