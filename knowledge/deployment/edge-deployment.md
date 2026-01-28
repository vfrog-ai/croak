# Edge Deployment Guide

## Overview

Edge deployment runs inference locally on:
- NVIDIA Jetson devices
- Desktop GPUs
- Industrial PCs with NVIDIA GPUs

## Deployment Formats

| Format | Best For | Speed | Compatibility |
|--------|----------|-------|---------------|
| PyTorch | Development | Baseline | Any CUDA GPU |
| ONNX | Cross-platform | 1.2x | Any platform |
| TensorRT | NVIDIA production | 2-3x | NVIDIA only |

## Export Chain

```
PyTorch (.pt)
    │
    ├── Direct CUDA inference (simplest)
    │
    └── Export to ONNX (.onnx)
            │
            ├── ONNX Runtime (cross-platform)
            │
            └── Convert to TensorRT (.engine)
                    │
                    └── Maximum NVIDIA performance
```

## ONNX Export

### Basic Export

```python
from ultralytics import YOLO

model = YOLO('best.pt')
model.export(format='onnx', imgsz=640)
# Creates: best.onnx
```

### Export Options

```python
model.export(
    format='onnx',
    imgsz=640,          # Input size
    half=True,          # FP16 precision
    simplify=True,      # Simplify ONNX graph
    opset=17,           # ONNX opset version
    dynamic=False       # Static shapes (faster)
)
```

### ONNX Inference

```python
import onnxruntime as ort
import numpy as np
import cv2

# Load model
session = ort.InferenceSession('best.onnx')
input_name = session.get_inputs()[0].name

# Preprocess image
img = cv2.imread('image.jpg')
img = cv2.resize(img, (640, 640))
img = img.transpose(2, 0, 1)  # HWC to CHW
img = np.expand_dims(img, 0).astype(np.float32) / 255.0

# Run inference
outputs = session.run(None, {input_name: img})
```

## TensorRT Export

### Requirements

- NVIDIA GPU
- CUDA Toolkit
- TensorRT installed
- cuDNN

### Basic Export

```python
from ultralytics import YOLO

model = YOLO('best.pt')
model.export(format='engine', imgsz=640)
# Creates: best.engine
```

### Export Options

```python
model.export(
    format='engine',
    imgsz=640,
    half=True,          # FP16 (recommended)
    int8=False,         # INT8 quantization
    dynamic=False,      # Static batch
    workspace=4,        # GB for TensorRT
    batch=1             # Batch size
)
```

### Precision Options

| Precision | Speed | Accuracy | Use Case |
|-----------|-------|----------|----------|
| FP32 | 1x | Full | Development |
| FP16 | 1.5-2x | ~Same | Production (default) |
| INT8 | 2-3x | -1-2% | Max speed |

### INT8 Calibration

```python
# INT8 requires calibration data
model.export(
    format='engine',
    int8=True,
    data='calibration_data.yaml'  # Subset of training data
)
```

### TensorRT Inference

```python
from ultralytics import YOLO

# Load TensorRT engine
model = YOLO('best.engine')

# Run inference
results = model('image.jpg')
```

## CUDA Direct Inference

### Simplest Approach

```python
from ultralytics import YOLO
import torch

# Load model on GPU
model = YOLO('best.pt')
model.to('cuda')

# Enable FP16 for speed
with torch.cuda.amp.autocast():
    results = model('image.jpg')
```

### Batch Inference

```python
# Process multiple images
results = model(['img1.jpg', 'img2.jpg', 'img3.jpg'])
```

## Performance Comparison

### On NVIDIA Jetson Orin (YOLOv8s, 640x640)

| Format | Latency | Throughput | Memory |
|--------|---------|------------|--------|
| PyTorch FP32 | 45ms | 22 FPS | 1.2 GB |
| PyTorch FP16 | 28ms | 35 FPS | 0.8 GB |
| ONNX FP16 | 25ms | 40 FPS | 0.7 GB |
| TensorRT FP16 | 12ms | 83 FPS | 0.5 GB |
| TensorRT INT8 | 8ms | 125 FPS | 0.4 GB |

### On Desktop RTX 3080 (YOLOv8s, 640x640)

| Format | Latency | Throughput |
|--------|---------|------------|
| PyTorch FP16 | 8ms | 125 FPS |
| TensorRT FP16 | 4ms | 250 FPS |
| TensorRT INT8 | 3ms | 333 FPS |

## Inference Script Template

```python
#!/usr/bin/env python3
"""
CROAK Edge Inference Script
"""

import argparse
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

class Detector:
    def __init__(self, model_path: str, conf_threshold: float = 0.25):
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

    def detect(self, image_path: str) -> list:
        results = self.model(image_path, conf=self.conf_threshold)

        detections = []
        for result in results:
            for box in result.boxes:
                detections.append({
                    'class': result.names[int(box.cls[0])],
                    'confidence': float(box.conf[0]),
                    'bbox': box.xyxy[0].tolist()
                })

        return detections

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--conf', type=float, default=0.25)
    args = parser.parse_args()

    detector = Detector(args.model, args.conf)
    detections = detector.detect(args.image)

    for det in detections:
        print(f"{det['class']}: {det['confidence']:.2f}")

if __name__ == '__main__':
    main()
```

## Jetson-Specific Setup

### Install Dependencies

```bash
# On Jetson (JetPack 5.x)
pip install ultralytics
pip install onnxruntime-gpu  # Jetson version

# TensorRT is pre-installed with JetPack
```

### Optimize for Jetson

```python
# Use Jetson-optimized settings
model.export(
    format='engine',
    imgsz=640,
    half=True,
    workspace=2,  # Lower for Jetson
    device=0
)
```

### Power Mode

```bash
# Set to max performance
sudo nvpmodel -m 0
sudo jetson_clocks
```

## Troubleshooting

### TensorRT Build Fails

```
Error: TensorRT build failed

Fix:
1. Ensure CUDA/TensorRT versions match
2. Try lower workspace size
3. Update TensorRT to latest
```

### ONNX Runtime CUDA Not Found

```
Error: CUDA provider not available

Fix:
1. Install onnxruntime-gpu (not onnxruntime)
2. Verify CUDA is in PATH
3. Check CUDA version compatibility
```

### Engine Not Compatible

```
Error: Engine file not compatible with this GPU

Fix:
1. TensorRT engines are GPU-specific
2. Rebuild engine on target hardware
3. Don't copy engines between different GPUs
```

## Best Practices

1. **Always use FP16** - Minimal accuracy loss, significant speed gain
2. **Build TensorRT on target** - Engines are hardware-specific
3. **Test accuracy after export** - Verify before deployment
4. **Monitor GPU memory** - Leave headroom for other processes
5. **Warm up before benchmarking** - First inference is slower
