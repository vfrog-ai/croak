# Model Export Formats

## Format Overview

| Format | Extension | Platform | Speed | Use Case |
|--------|-----------|----------|-------|----------|
| PyTorch | .pt | Any | Baseline | Training, dev |
| ONNX | .onnx | Any | 1.2x | Cross-platform |
| TensorRT | .engine | NVIDIA | 2-3x | NVIDIA production |
| CoreML | .mlpackage | Apple | 2x | iOS/macOS |
| TFLite | .tflite | Mobile | 1.5x | Android/iOS |
| OpenVINO | .xml | Intel | 2x | Intel hardware |

## PyTorch (.pt)

### Characteristics
- Native Ultralytics format
- Contains model architecture + weights
- Requires PyTorch to run
- Most flexible for development

### Usage
```python
from ultralytics import YOLO

# Load
model = YOLO('best.pt')

# Inference
results = model('image.jpg')
```

### When to Use
- Development and testing
- When flexibility is priority
- Before deciding on deployment target

## ONNX (.onnx)

### Characteristics
- Open standard format
- Platform independent
- Good balance of portability and speed
- Supported by many runtimes

### Export
```python
model = YOLO('best.pt')
model.export(format='onnx')
```

### Export Options
```python
model.export(
    format='onnx',
    imgsz=640,          # Input resolution
    half=True,          # FP16 precision
    simplify=True,      # Optimize graph
    opset=17,           # ONNX opset version
    dynamic=False       # Fixed input shape
)
```

### Inference with ONNX Runtime
```python
import onnxruntime as ort

session = ort.InferenceSession('best.onnx')
input_name = session.get_inputs()[0].name
outputs = session.run(None, {input_name: preprocessed_image})
```

### When to Use
- Need cross-platform deployment
- Intermediate step to TensorRT
- Non-NVIDIA hardware
- Edge devices without TensorRT

## TensorRT (.engine)

### Characteristics
- NVIDIA-optimized format
- Fastest inference on NVIDIA GPUs
- Hardware-specific (can't transfer between GPUs)
- Supports FP16 and INT8

### Export
```python
model = YOLO('best.pt')
model.export(format='engine')
```

### Export Options
```python
model.export(
    format='engine',
    imgsz=640,
    half=True,          # FP16 (recommended)
    int8=False,         # INT8 quantization
    workspace=4,        # GB for optimization
    batch=1,            # Batch size
    dynamic=False       # Fixed batch
)
```

### Inference
```python
# Ultralytics handles TensorRT loading
model = YOLO('best.engine')
results = model('image.jpg')
```

### When to Use
- NVIDIA GPU deployment
- Maximum inference speed needed
- Production workloads
- Jetson edge devices

### Important Notes
- **Hardware-specific**: Engine built on RTX 3080 won't work on RTX 4080
- **Must rebuild** on each target hardware
- **Version-specific**: TensorRT version must match

## CoreML (.mlpackage)

### Characteristics
- Apple ecosystem format
- Optimized for Apple Neural Engine
- iOS, macOS, watchOS, tvOS

### Export
```python
model = YOLO('best.pt')
model.export(format='coreml')
```

### When to Use
- iOS app development
- macOS applications
- Apple Watch integration

## TFLite (.tflite)

### Characteristics
- TensorFlow Lite format
- Mobile-optimized
- Android and iOS
- Supports quantization

### Export
```python
model = YOLO('best.pt')
model.export(format='tflite')
```

### When to Use
- Android apps
- Mobile-first deployment
- Resource-constrained devices

## OpenVINO (.xml + .bin)

### Characteristics
- Intel-optimized format
- CPU and Intel GPU/VPU
- Good for Intel hardware

### Export
```python
model = YOLO('best.pt')
model.export(format='openvino')
```

### When to Use
- Intel CPUs
- Intel integrated graphics
- Intel Neural Compute Stick

## Export Comparison

### Size (YOLOv8s, FP16)

| Format | File Size |
|--------|-----------|
| PyTorch | 22 MB |
| ONNX | 21 MB |
| TensorRT | 19 MB |
| CoreML | 22 MB |
| TFLite | 21 MB |

### Speed (YOLOv8s, 640x640, RTX 3080)

| Format | Latency | FPS |
|--------|---------|-----|
| PyTorch FP16 | 8ms | 125 |
| ONNX | 7ms | 143 |
| TensorRT FP16 | 4ms | 250 |
| TensorRT INT8 | 3ms | 333 |

## Precision Options

### FP32 (Full Precision)
- Default precision
- Maximum accuracy
- Slowest inference
- Use for: Development, accuracy-critical

### FP16 (Half Precision)
- 16-bit floating point
- Minimal accuracy loss (<0.1% mAP)
- 1.5-2x speedup
- Use for: Most production deployments

### INT8 (Quantized)
- 8-bit integer
- 1-2% accuracy loss
- 2-3x speedup
- Requires calibration data
- Use for: Maximum speed, edge devices

## Export Best Practices

1. **Always verify accuracy after export**
   ```python
   # Compare PyTorch vs exported model
   pt_results = pt_model('test.jpg')
   onnx_results = onnx_model('test.jpg')
   # Compare detections
   ```

2. **Use FP16 by default**
   ```python
   model.export(format='engine', half=True)
   ```

3. **Match training resolution**
   ```python
   # If trained with imgsz=640, export with imgsz=640
   model.export(format='onnx', imgsz=640)
   ```

4. **Test on target hardware**
   - Build TensorRT engines on deployment hardware
   - Benchmark on actual device

5. **Keep original weights**
   - Never delete .pt file
   - Export creates new files
