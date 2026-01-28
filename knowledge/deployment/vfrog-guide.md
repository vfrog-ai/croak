# vfrog.ai Integration Guide

## Overview

vfrog.ai provides:
1. **Annotation** - Label images for object detection
2. **Deployment** - Host models as API endpoints

## Setup

### Get API Key

1. Sign up at https://vfrog.ai
2. Go to Settings → API
3. Generate new API key
4. Set environment variable:

```bash
export VFROG_API_KEY=your_key_here
```

### Install Client

```bash
pip install vfrog
```

## Annotation Workflow

### 1. Create Project

```python
from vfrog import Client

client = Client()  # Uses VFROG_API_KEY env var

project = client.create_project(
    name="my-detection-project",
    task_type="detection",
    classes=["person", "car", "bicycle"]
)

print(f"Project created: {project.id}")
print(f"Dashboard: {project.url}")
```

### 2. Upload Images

```python
from pathlib import Path

image_dir = Path("./data/raw")
images = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))

# Upload in batches
for batch in batched(images, 50):
    client.upload_images(project.id, batch)
    print(f"Uploaded {len(batch)} images")
```

### 3. Annotate in vfrog UI

Open the project URL and:
1. Use auto-annotation for initial labels
2. Review and correct each image
3. Ensure consistent labeling
4. Mark project as complete

### 4. Export Annotations

```python
# Export in YOLO format
annotations = client.export_annotations(
    project_id=project.id,
    format="yolo"
)

# Save locally
output_dir = Path("./data/annotations")
output_dir.mkdir(exist_ok=True)

for ann in annotations:
    (output_dir / ann['filename']).write_text(ann['content'])
```

## Deployment Workflow

### 1. Upload Model

```python
deployment = client.create_deployment(
    name="my-model",
    model_path="./training/experiments/exp-001/weights/best.pt",
    class_names=["person", "car", "bicycle"]
)

print(f"Deployment ID: {deployment.id}")
```

### 2. Configure Serving

```python
client.configure_deployment(
    deployment_id=deployment.id,
    config={
        "min_replicas": 1,
        "max_replicas": 5,
        "target_latency_ms": 100,
        "auto_scaling": True
    }
)
```

### 3. Deploy to Staging

```python
staging = client.deploy_to_staging(deployment.id)
print(f"Staging URL: {staging.endpoint_url}")
```

### 4. Test Staging

```python
import httpx

response = httpx.post(
    staging.endpoint_url,
    headers={"Authorization": f"Bearer {staging.api_key}"},
    files={"image": open("test.jpg", "rb")}
)

print(response.json())
```

### 5. Promote to Production

```python
production = client.deploy_to_production(deployment.id)
print(f"Production URL: {production.endpoint_url}")
print(f"API Key: {production.api_key}")
```

## API Usage

### Python

```python
import httpx

ENDPOINT = "https://api.vfrog.ai/v1/predict/your-model-id"
API_KEY = "your-api-key"

response = httpx.post(
    ENDPOINT,
    headers={"Authorization": f"Bearer {API_KEY}"},
    files={"image": open("image.jpg", "rb")}
)

result = response.json()
for detection in result["detections"]:
    print(f"{detection['class']}: {detection['confidence']:.2f}")
    print(f"  Box: {detection['bbox']}")
```

### cURL

```bash
curl -X POST https://api.vfrog.ai/v1/predict/your-model-id \
  -H "Authorization: Bearer your-api-key" \
  -F "image=@image.jpg"
```

### Response Format

```json
{
  "success": true,
  "detections": [
    {
      "class": "person",
      "class_id": 0,
      "confidence": 0.92,
      "bbox": {
        "x1": 100,
        "y1": 200,
        "x2": 300,
        "y2": 500
      }
    }
  ],
  "inference_time_ms": 45,
  "image_size": [640, 480]
}
```

## Pricing

### Annotation
- Free tier: 1,000 images/month
- Pro tier: Pay per image

### Deployment
- Free tier: 1,000 requests/month
- Pro tier: Pay per request + compute

Check https://vfrog.ai/pricing for current rates.

## Troubleshooting

### API Key Invalid
```
Error: Invalid API key

Fix: Check VFROG_API_KEY is set correctly
     Regenerate key if expired
```

### Upload Timeout
```
Error: Upload timeout

Fix: Reduce batch size
     Check internet connection
     Check file sizes (max 10MB per image)
```

### Deployment Failed
```
Error: Model deployment failed

Fix: Verify model is valid YOLO format
     Check model loads locally first
     Ensure class names match
```

## Best Practices

### Annotation
1. Use auto-annotation first, then correct
2. Be consistent with edge cases
3. Label all instances, even partial
4. Use keyboard shortcuts for speed

### Deployment
1. Always test in staging first
2. Start with min_replicas=1
3. Monitor latency in dashboard
4. Enable auto-scaling for production
