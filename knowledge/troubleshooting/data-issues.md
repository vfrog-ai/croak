# Common Data Issues and Solutions

This guide covers frequent data problems encountered during object detection dataset preparation.

## Image Issues

### Corrupt or Unreadable Images

**Symptoms**:
- Validation fails with "corrupt image" errors
- Training crashes with decode errors
- PIL/OpenCV can't open file

**Causes**:
- Incomplete file transfer
- Disk corruption
- Wrong file extension
- Truncated download

**Solutions**:
1. Identify corrupt files:
   ```python
   from PIL import Image
   import os

   for img_path in image_paths:
       try:
           img = Image.open(img_path)
           img.verify()
       except Exception as e:
           print(f"Corrupt: {img_path} - {e}")
   ```
2. Remove or replace corrupt files
3. Re-download from source if available
4. Check disk health if recurring

---

### Inconsistent Image Sizes

**Symptoms**:
- High size variance warning
- Training instability
- Unexpected memory usage

**Causes**:
- Mixed sources (web scrape, cameras, screenshots)
- Different cameras/resolutions
- Rotated images with swapped dimensions

**Solutions**:
1. Resize to consistent dimensions (YOLO handles this, but uniform is better)
2. Group by aspect ratio for batching
3. Use appropriate `imgsz` in training config

**Best Practice**: 640x640 or 1280x1280 for most detection tasks

---

### Low Resolution Images

**Symptoms**:
- Images < 300px on shortest side
- Small objects undetectable
- Poor model performance

**Solutions**:
1. Collect higher resolution images
2. Accept lower accuracy for small objects
3. Use larger input size if GPU memory allows

**Minimum Recommendation**: 640px shortest side

---

### Color Space Issues

**Symptoms**:
- Images appear wrong color
- Model sees different colors than expected
- Inconsistent predictions

**Causes**:
- RGB vs BGR confusion
- CMYK images (print sources)
- Grayscale mixed with color

**Solutions**:
1. Convert all to RGB:
   ```python
   img = Image.open(path).convert('RGB')
   ```
2. Be consistent between training and inference

---

## Annotation Issues

### Missing Annotations

**Symptoms**:
- Annotation coverage < 100%
- Some images have no labels
- Validation warning about unannotated images

**Solutions**:
1. Upload to vfrog for annotation
2. Remove unannotated images:
   ```bash
   croak validate --remove-unannotated
   ```
3. Ensure annotation export included all images

---

### Invalid Bounding Boxes

**Symptoms**:
- Negative coordinates
- Boxes outside image bounds
- Zero-area boxes (width or height = 0)

**Causes**:
- Annotation tool bugs
- Format conversion errors
- Manual annotation mistakes

**Solutions**:
1. Clamp to image bounds:
   ```python
   x1 = max(0, min(x1, img_width))
   y1 = max(0, min(y1, img_height))
   ```
2. Remove zero-area boxes
3. Re-annotate problematic images

---

### Class Name Inconsistencies

**Symptoms**:
- Duplicate classes: "car", "Car", "CAR"
- Typos: "person", "persom"
- Similar names: "vehicle", "car" (semantic overlap)

**Solutions**:
1. Standardize case (lowercase recommended)
2. Create class mapping file
3. Merge similar classes:
   ```yaml
   class_mapping:
     Car: car
     CAR: car
     vehicle: car
   ```

---

### Wrong Annotation Format

**Symptoms**:
- Parser errors
- Missing fields
- Unexpected file structure

**Common Formats**:

| Format | Structure | Example |
|--------|-----------|---------|
| YOLO | `class x_center y_center width height` (normalized) | `0 0.5 0.5 0.1 0.2` |
| COCO | JSON with images, annotations, categories arrays | `{"annotations": [...]}` |
| VOC | XML with `<object><bndbox>` elements | `<xmin>100</xmin>` |

**Solutions**:
```bash
croak convert --from coco --to yolo
```

---

## Class Distribution Issues

### Severe Class Imbalance

**Symptoms**:
- One class has 10x+ more instances than another
- Model ignores minority classes
- High precision, low recall on rare classes

**Causes**:
- Natural distribution (cars more common than motorcycles)
- Collection bias
- Incomplete annotation

**Solutions**:
1. **Collect more minority samples** (best)
2. **Oversample minority class** during training
3. **Use class weights**:
   ```yaml
   # In training config
   cls_weights: [1.0, 5.0, 10.0]  # Boost rare classes
   ```
4. **Data augmentation** focused on minority classes
5. **Merge similar classes** if semantically valid

**Acceptable Ratio**: < 10:1 between most and least common class

---

### Too Few Classes

**Symptoms**:
- Only 1-2 classes defined
- Model overfits easily
- Limited practical use

**Solutions**:
- Consider if task really needs detection (vs classification)
- Add negative class if distinguishing from background is important

---

### Too Many Classes

**Symptoms**:
- 50+ classes
- Many classes have < 20 instances
- Confusion between similar classes

**Solutions**:
1. Merge similar classes into parent categories
2. Focus on most important classes first
3. Use hierarchical approach (train coarse first, then fine-grained)

---

## Dataset Split Issues

### Test Set Too Small

**Symptoms**:
- < 50 images in test set
- Metrics have high variance
- Can't trust evaluation results

**Solutions**:
- Use at least 50-100 images for test
- Consider 80/15/5 or 70/20/10 splits
- Ensure all classes represented in test

---

### Data Leakage

**Symptoms**:
- Training metrics much better than test
- Near-identical images in train and test
- Augmented versions of same image in different splits

**Causes**:
- Random split without checking similarity
- Video frames from same clip in different splits
- Copy-paste during data collection

**Solutions**:
1. Split by source/session, not randomly
2. Check for near-duplicates before splitting
3. Keep all frames from one video in same split

---

### Class Missing from Split

**Symptoms**:
- Validation shows 0 instances for class in test set
- Model can't be evaluated on all classes

**Solutions**:
- Use stratified splitting:
  ```bash
  croak split --stratify
  ```
- Manually verify class distribution across splits

---

## Performance Issues

### Slow Data Loading

**Symptoms**:
- GPU utilization < 50%
- Training bottlenecked by data loading
- Long pauses between batches

**Solutions**:
1. Increase `workers` in dataloader (4-8 typical)
2. Use SSD storage for dataset
3. Pre-resize images to training size
4. Use caching if dataset fits in RAM

---

### Dataset Too Large for Memory

**Symptoms**:
- OOM during data loading
- System swap usage high
- Slow performance

**Solutions**:
1. Use streaming/lazy loading (default in YOLO)
2. Reduce `cache` option in training
3. Use smaller batch size
4. Resize images before training

---

## Diagnostic Commands

```bash
# Check data quality
croak validate --verbose

# View statistics
croak stats

# Visualize samples
croak visualize --samples 20

# Check specific class
croak stats --class "person"

# Find problematic images
croak validate --output issues.json
```
