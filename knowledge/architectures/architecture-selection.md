# Architecture Selection Guide

## Quick Decision Matrix

| Scenario | Recommended | Why |
|----------|-------------|-----|
| Edge deployment, real-time | YOLOv8n | Smallest, fastest |
| General purpose, beginner | YOLOv8s | Best balance |
| High accuracy needed | YOLOv8m | More capacity |
| Small objects critical | YOLOv11s | Improved small detection |
| No NMS preferred | RT-DETR | End-to-end transformer |

## Architecture Comparison

### YOLOv8 Family (Recommended for most cases)

| Model | Params | mAP@50 (COCO) | Speed (T4) | Best For |
|-------|--------|---------------|------------|----------|
| YOLOv8n | 3.2M | ~37.3 | ~100 FPS | Edge, mobile |
| YOLOv8s | 11.2M | ~44.9 | ~70 FPS | General purpose |
| YOLOv8m | 25.9M | ~50.2 | ~45 FPS | Accuracy focus |
| YOLOv8l | 43.7M | ~52.9 | ~30 FPS | High accuracy |
| YOLOv8x | 68.2M | ~53.9 | ~20 FPS | Maximum accuracy |

### YOLOv11 (Latest generation)

| Model | Params | Improvement Over v8 |
|-------|--------|---------------------|
| YOLOv11n | ~2.6M | Better small objects, lighter |
| YOLOv11s | ~9.4M | Improved feature extraction |
| YOLOv11m | ~20.1M | Better accuracy/speed ratio |

### RT-DETR (Transformer-based)

- **Parameters:** ~32M (RT-DETR-L)
- **Pros:** No NMS, end-to-end, variable input sizes
- **Cons:** Slower, more memory, complex training
- **Best for:** When NMS is problematic, research applications

## Selection Criteria

### 1. Deployment Target

**Edge/Mobile:**
- Use YOLOv8n or YOLOv11n
- Prioritize inference speed
- Consider TensorRT optimization

**Cloud API:**
- Can use YOLOv8s/m
- Latency less critical
- Accuracy more important

**Desktop/Server:**
- YOLOv8s is the sweet spot
- YOLOv8m if accuracy is critical

### 2. Dataset Size

| Training Images | Recommended Max Model |
|-----------------|----------------------|
| < 500 | YOLOv8n (avoid overfitting) |
| 500 - 2000 | YOLOv8s |
| 2000 - 10000 | YOLOv8m |
| > 10000 | YOLOv8l/x |

### 3. Number of Classes

| Classes | Recommendation |
|---------|----------------|
| 1-5 | YOLOv8n sufficient |
| 5-20 | YOLOv8s recommended |
| 20-80 | YOLOv8m or larger |
| 80+ | YOLOv8l/x |

### 4. Object Characteristics

**Small objects (< 32px):**
- YOLOv11 (improved small detection)
- Higher input resolution (imgsz=1280)

**Large objects (> 200px):**
- All YOLO variants work well
- Can reduce input size for speed

**Dense scenes (many objects):**
- YOLOv8m+ for better separation
- RT-DETR if NMS issues occur

## Default Recommendation

For most users starting out:

```
YOLOv8s
```

**Why:**
- Best balance of speed and accuracy
- Well-documented, widely used
- Good pretrained weights
- Works with most dataset sizes
- Easy to iterate from (up to m, down to n)

## When to Deviate

**Use YOLOv8n when:**
- Edge deployment required
- Real-time (>30 FPS) needed
- Very limited training data (<500 images)
- Model size constrained (<10MB)

**Use YOLOv8m when:**
- Cloud deployment
- Accuracy is critical
- Large dataset (>2000 images)
- Many classes (>20)

**Use YOLOv11 when:**
- Small object detection is critical
- Latest improvements desired
- Compatible infrastructure

**Use RT-DETR when:**
- NMS causes issues
- Transformer-based preferred
- Research/experimental context
