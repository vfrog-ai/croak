# Common Training Issues

## Quick Diagnosis

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Loss = NaN | LR too high, corrupt data | Lower LR, check images |
| mAP = 0 | Wrong annotations | Verify label format |
| Val loss diverges | Overfitting | More augmentation, less model |
| Training very slow | Wrong batch size | Increase batch or reduce imgsz |
| OOM error | Batch too large | Reduce batch size |

## Model Not Learning (mAP ≈ 0)

### Symptom
- Loss may decrease but mAP stays near zero
- Model predicts nothing or random

### Causes & Solutions

**1. Wrong annotation format**
```
Check: Labels should be YOLO format
       class_id x_center y_center width height
       All values normalized 0-1

Fix: Convert annotations with croak convert
```

**2. Class ID mismatch**
```
Check: Class IDs in labels match data.yaml order
       First class = 0, not 1

Fix: Verify data.yaml names match label IDs
```

**3. Empty or missing labels**
```
Check: Every image has corresponding .txt file
       Label files have content

Fix: Re-export annotations from vfrog
```

**4. Path issues in data.yaml**
```
Check: Paths in data.yaml are correct
       Images actually exist at those paths

Fix: Use absolute paths or verify relative paths
```

## NaN Loss

### Symptom
- Loss becomes NaN during training
- Training crashes or produces garbage

### Causes & Solutions

**1. Learning rate too high**
```
Fix: Reduce lr0 from 0.01 to 0.001
     Add warmup_epochs: 5
```

**2. Corrupt images**
```
Check: Run croak validate to find bad images
Fix: Remove or replace corrupt files
```

**3. Extreme annotation values**
```
Check: All bbox values between 0 and 1
       No negative values, no values > 1

Fix: Clean annotations, re-export from vfrog
```

**4. Mixed precision issues**
```
Fix: Try amp: false in config (slower but stable)
```

## Overfitting

### Symptom
- Training loss decreases
- Validation loss increases
- Big gap between train and val mAP

### Solutions

**1. More augmentation**
```yaml
mosaic: 1.0
mixup: 0.1
copy_paste: 0.1
scale: 0.9
```

**2. Smaller model**
```
Switch: yolov8m → yolov8s → yolov8n
```

**3. Earlier stopping**
```yaml
patience: 10  # Stop sooner
```

**4. More data**
```
Best solution: Collect more training images
```

**5. Regularization**
```yaml
weight_decay: 0.001  # Increase from 0.0005
dropout: 0.1         # Add dropout
```

## Underfitting

### Symptom
- Training and validation loss both high
- mAP plateaus early at low value

### Solutions

**1. More epochs**
```yaml
epochs: 200  # Increase from 100
patience: 50 # Allow more time
```

**2. Larger model**
```
Switch: yolov8n → yolov8s → yolov8m
```

**3. Higher learning rate**
```yaml
lr0: 0.02  # Increase from 0.01
```

**4. Less augmentation**
```yaml
mosaic: 0.5
mixup: 0.0
scale: 0.3
```

## Out of Memory (OOM)

### Symptom
- CUDA out of memory error
- Training crashes immediately

### Solutions

**1. Reduce batch size**
```yaml
batch: 8  # Reduce from 16
```

**2. Reduce image size**
```yaml
imgsz: 480  # Reduce from 640
```

**3. Use smaller model**
```
yolov8m → yolov8s → yolov8n
```

**4. Enable gradient checkpointing**
```python
# In training script
model.train(gradient_checkpointing=True)
```

## Slow Training

### Symptom
- Training takes much longer than expected
- GPU utilization low

### Solutions

**1. Increase batch size**
```yaml
batch: 32  # If GPU memory allows
```

**2. Enable mixed precision**
```yaml
amp: true  # Usually default
```

**3. Use faster data loading**
```yaml
workers: 8  # Increase if CPU limited
```

**4. Check GPU utilization**
```bash
nvidia-smi -l 1  # Monitor GPU usage
```

## Class Imbalance Issues

### Symptom
- Good mAP on majority classes
- Poor mAP on minority classes

### Solutions

**1. Data augmentation**
```yaml
mosaic: 1.0   # Helps combine images
mixup: 0.1    # Mixes classes
```

**2. Oversampling minority classes**
```
Duplicate images with minority classes
```

**3. Focal loss (automatic)**
YOLO uses focal loss by default

**4. Class weighting (custom)**
```python
# In training callback
cls_weights = compute_class_weights(dataset)
```

## Inconsistent Results

### Symptom
- Different results each training run
- Hard to reproduce

### Solution
```yaml
seed: 42
deterministic: true
```

## Resume Failed Training

### Symptom
- Training interrupted
- Want to continue from checkpoint

### Solution
```python
# Resume from last checkpoint
model = YOLO('runs/detect/train/weights/last.pt')
model.train(resume=True)
```

Or via CLI:
```bash
yolo train resume model=runs/detect/train/weights/last.pt
```

## Debugging Checklist

When training fails, check in order:

1. ✅ data.yaml paths correct?
2. ✅ Images readable? (croak validate)
3. ✅ Annotations in YOLO format?
4. ✅ Class IDs match data.yaml?
5. ✅ Batch size fits GPU memory?
6. ✅ Learning rate reasonable?
7. ✅ Pretrained weights download?
8. ✅ Disk space available for checkpoints?
