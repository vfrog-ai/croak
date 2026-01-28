# Modal.com GPU Setup Guide

## Why Modal?

Modal.com is CROAK's default GPU provider because:
- **Free $30 credits** for new accounts (~15 training runs)
- **No setup hassle** - just pip install and go
- **Pay-per-second** - no idle costs
- **Simple API** - Python-native, no cloud console

## Quick Start

### 1. Install Modal CLI

```bash
pip install modal
```

### 2. Authenticate

```bash
modal token new
```

This opens your browser. Sign in (or create account) and authorize.

### 3. Verify Setup

```bash
modal run --help
```

You're ready to train!

## GPU Options

| GPU | VRAM | Rate/hr | Best For |
|-----|------|---------|----------|
| T4 | 16GB | $0.59 | Most training |
| A10G | 24GB | $1.10 | Larger batches |
| A100 (40GB) | 40GB | $2.78 | Big models |
| H100 | 80GB | $4.76 | Maximum speed |

### Recommendation

**Start with T4** - sufficient for YOLOv8n/s/m with batch=16

## Training Script Structure

### Basic Modal Script

```python
import modal

app = modal.App("croak-training")

# Define the training image
training_image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "ultralytics>=8.0.0",
    "torch>=2.0.0",
    "torchvision>=0.15.0",
    "mlflow>=2.0.0",
    "pyyaml"
)

@app.function(
    gpu="T4",
    timeout=4 * 3600,  # 4 hours max
    image=training_image,
)
def train(data_yaml: str, config: dict):
    from ultralytics import YOLO

    model = YOLO('yolov8s.pt')
    results = model.train(
        data=data_yaml,
        epochs=config['epochs'],
        batch=config['batch'],
        imgsz=config['imgsz'],
        project='/results',
        name=config['experiment_id']
    )

    return {
        'mAP50': results.results_dict['metrics/mAP50(B)'],
        'best_model': str(results.save_dir / 'weights' / 'best.pt')
    }

@app.local_entrypoint()
def main():
    config = {
        'epochs': 100,
        'batch': 16,
        'imgsz': 640,
        'experiment_id': 'exp-001'
    }
    result = train.remote('/data/data.yaml', config)
    print(f"Training complete: {result}")
```

### With Data Upload

```python
import modal
from pathlib import Path

app = modal.App("croak-training")

# Mount local data directory
data_mount = modal.Mount.from_local_dir(
    "./data/processed",
    remote_path="/data"
)

@app.function(
    gpu="T4",
    timeout=4 * 3600,
    image=training_image,
    mounts=[data_mount]
)
def train():
    from ultralytics import YOLO

    model = YOLO('yolov8s.pt')
    results = model.train(
        data='/data/data.yaml',
        epochs=100,
        batch=16,
        imgsz=640
    )
    return results
```

### Download Results

```python
import modal

app = modal.App("croak-training")

# Create a volume for persistent storage
volume = modal.Volume.from_name("croak-results", create_if_missing=True)

@app.function(
    gpu="T4",
    volumes={"/results": volume}
)
def train():
    from ultralytics import YOLO

    model = YOLO('yolov8s.pt')
    results = model.train(
        data='/data/data.yaml',
        project='/results',
        name='exp-001'
    )

    # Results are saved to volume
    volume.commit()
    return results

# Download results locally
@app.local_entrypoint()
def download():
    # Access volume contents
    pass
```

## Running Training

### Execute Training

```bash
modal run train.py
```

### Monitor Progress

Training output streams to your terminal in real-time.

### Run in Background

```bash
modal run --detach train.py
```

Check status:
```bash
modal app logs croak-training
```

## Cost Estimation

### Formula

```
Cost = GPU_rate × hours

T4 example:
$0.59/hr × 4 hours = $2.36
```

### Typical Training Costs

| Model | Dataset | Epochs | GPU | Time | Cost |
|-------|---------|--------|-----|------|------|
| YOLOv8n | 500 imgs | 100 | T4 | 1hr | $0.59 |
| YOLOv8s | 1000 imgs | 100 | T4 | 2hr | $1.18 |
| YOLOv8s | 2000 imgs | 150 | T4 | 4hr | $2.36 |
| YOLOv8m | 5000 imgs | 200 | A10G | 8hr | $8.80 |

### Free Credits

- New accounts: $30 free
- Enough for ~15-50 training runs
- No credit card required to start

## Configuration Options

### Timeout

```python
@app.function(
    gpu="T4",
    timeout=4 * 3600  # 4 hours in seconds
)
```

Increase for longer training runs.

### Memory

```python
@app.function(
    gpu="T4",
    memory=16384  # MB of system RAM
)
```

### Multiple GPUs

```python
@app.function(
    gpu=modal.gpu.A100(count=2)  # 2x A100s
)
```

## Troubleshooting

### "No GPU available"

```
Error: No GPU capacity available

Fix: Try a different GPU type or wait
     modal.gpu.any() uses any available
```

### Timeout Errors

```
Error: Function timed out

Fix: Increase timeout
     timeout=8 * 3600  # 8 hours
```

### Out of Memory

```
Error: CUDA out of memory

Fix:
1. Reduce batch size
2. Use larger GPU (T4 → A10G)
3. Reduce image size
```

### Upload Slow

```
Large dataset uploads slowly

Fix:
1. Compress data before upload
2. Use modal.Volume for persistent storage
3. Store data in cloud bucket
```

## Best Practices

1. **Start with T4** - upgrade only if needed
2. **Use volumes** for repeated experiments (avoid re-upload)
3. **Set reasonable timeouts** - don't pay for idle
4. **Monitor costs** in Modal dashboard
5. **Download results** before they expire (24hr default)

## Checking Credits

```bash
# View account status
modal profile current

# Or check dashboard
# https://modal.com/settings
```

## Alternative: Local GPU

If you have a local NVIDIA GPU (8GB+ VRAM):

```python
# Skip Modal, run directly
from ultralytics import YOLO

model = YOLO('yolov8s.pt')
model.train(data='data.yaml', epochs=100)
```

Pros:
- Free
- No upload time

Cons:
- Slower than cloud GPUs
- Ties up your machine
