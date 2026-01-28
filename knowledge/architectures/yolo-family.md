# YOLO Family Reference

## Overview

YOLO (You Only Look Once) is a family of real-time object detection models. CROAK v1.0 supports:

- **YOLOv8** (Ultralytics, 2023) - Primary recommendation
- **YOLOv11** (Ultralytics, 2024) - Latest generation
- **RT-DETR** (Baidu, 2023) - Transformer alternative

## YOLOv8 Architecture

### Key Components

1. **Backbone (CSPDarknet)**
   - Feature extraction
   - C2f modules for efficient computation
   - SPPF for multi-scale features

2. **Neck (PANet)**
   - Feature pyramid network
   - Top-down and bottom-up paths
   - Multi-scale feature fusion

3. **Head (Decoupled)**
   - Separate classification and regression
   - Anchor-free design
   - Distribution focal loss

### Model Variants

```
YOLOv8n  →  YOLOv8s  →  YOLOv8m  →  YOLOv8l  →  YOLOv8x
 (nano)     (small)    (medium)    (large)    (xlarge)
   ↓          ↓          ↓          ↓          ↓
 3.2M       11.2M      25.9M      43.7M      68.2M params
```

### Pretrained Weights

All variants have COCO pretrained weights:
- `yolov8n.pt` - 6.3 MB
- `yolov8s.pt` - 22.5 MB
- `yolov8m.pt` - 52.0 MB
- `yolov8l.pt` - 87.7 MB
- `yolov8x.pt` - 137.0 MB

## YOLOv11 Improvements

### Over YOLOv8

1. **Better backbone efficiency**
   - Improved C2f modules
   - Better parameter utilization

2. **Enhanced small object detection**
   - Improved feature pyramid
   - Better attention mechanisms

3. **Reduced model size**
   - ~10-20% fewer parameters
   - Similar or better accuracy

### Model Variants

```
YOLOv11n: ~2.6M params (vs 3.2M in v8n)
YOLOv11s: ~9.4M params (vs 11.2M in v8s)
YOLOv11m: ~20.1M params (vs 25.9M in v8m)
```

## Training Configuration

### Recommended Settings

```yaml
# YOLOv8s defaults for object detection
model: yolov8s.pt
epochs: 100
batch: 16
imgsz: 640
optimizer: AdamW
lr0: 0.01
lrf: 0.01
momentum: 0.937
weight_decay: 0.0005
warmup_epochs: 3
warmup_momentum: 0.8
warmup_bias_lr: 0.1
patience: 20
```

### Augmentation Defaults

```yaml
# Standard augmentation
hsv_h: 0.015      # Hue shift
hsv_s: 0.7        # Saturation shift
hsv_v: 0.4        # Value shift
degrees: 0.0      # Rotation
translate: 0.1    # Translation
scale: 0.5        # Scaling
shear: 0.0        # Shearing
perspective: 0.0  # Perspective
flipud: 0.0       # Vertical flip
fliplr: 0.5       # Horizontal flip
mosaic: 1.0       # Mosaic probability
mixup: 0.0        # Mixup probability
copy_paste: 0.0   # Copy-paste augmentation
```

### Per-Model Recommendations

| Model | Batch Size | Image Size | Notes |
|-------|------------|------------|-------|
| YOLOv8n | 32-64 | 640 | Can increase batch |
| YOLOv8s | 16-32 | 640 | Default recommendation |
| YOLOv8m | 8-16 | 640 | May need smaller batch |
| YOLOv8l | 4-8 | 640 | Memory intensive |

## Loss Functions

### Box Loss (CIoU)
- Complete IoU loss
- Considers overlap, center distance, aspect ratio
- Better convergence than standard IoU

### Classification Loss (BCE)
- Binary cross-entropy
- Per-class prediction
- Better for multi-label scenarios

### Distribution Focal Loss (DFL)
- Regression as distribution learning
- Improves localization accuracy
- Unique to YOLOv8+

## Inference

### Basic Inference

```python
from ultralytics import YOLO

model = YOLO('yolov8s.pt')
results = model('image.jpg')

for result in results:
    boxes = result.boxes
    for box in boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        xyxy = box.xyxy[0].tolist()
```

### Batch Inference

```python
results = model(['img1.jpg', 'img2.jpg', 'img3.jpg'])
```

### Streaming Inference

```python
for result in model('video.mp4', stream=True):
    # Process each frame
    pass
```

## Export Formats

YOLO supports export to:

| Format | Command | Use Case |
|--------|---------|----------|
| ONNX | `model.export(format='onnx')` | Cross-platform |
| TensorRT | `model.export(format='engine')` | NVIDIA edge |
| CoreML | `model.export(format='coreml')` | Apple devices |
| TFLite | `model.export(format='tflite')` | Mobile |
| OpenVINO | `model.export(format='openvino')` | Intel hardware |

## Common Issues

### 1. NaN Loss
- Reduce learning rate
- Check for corrupt images
- Reduce batch size

### 2. Slow Convergence
- Increase learning rate slightly
- Add warmup epochs
- Check data quality

### 3. Overfitting
- Add more augmentation
- Reduce model size
- Add dropout (via config)
- Get more training data

### 4. Poor Small Object Detection
- Increase image size (imgsz=1280)
- Use YOLOv11
- Add multi-scale training
