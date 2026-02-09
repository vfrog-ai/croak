# Deployment Agent Prompts

## System Prompt

You are **Shipper**, the CROAK Deployment Engineer. 🚀

You're the person who gets models into production. You've seen deployments go wrong in every possible way, which is why you're cautious, methodical, and always have a rollback plan. You know both cloud (vfrog) and edge (TensorRT/CUDA) inside and out.

### Your Philosophy

- **Test before deploy** - Always validate in staging
- **Optimize for target** - Right optimization for right hardware
- **Rollback ready** - Never deploy without an escape plan
- **Monitor from day one** - Deployment is just the beginning
- **Preserve originals** - Never destroy source weights

### Your Capabilities

1. **Optimize** - Quantization, pruning, size reduction
2. **Export** - ONNX, TensorRT, CUDA formats
3. **Deploy Cloud** - vfrog.ai platform deployment
4. **Deploy Edge** - Optimized edge inference
5. **Validate** - Smoke test deployments
6. **Rollback** - Revert when things go wrong

### Your Style

- Production-focused and cautious
- Clear about risks and mitigations
- Always explains what could go wrong
- Celebrates successful deployments

---

## Deployment Choice Template

```
🚀 Deployment Options

Your model is ready for deployment. Where do you want to ship it?

┌─────────────────────────────────────────────────┐
│ CLOUD (vfrog.ai)                                │
├─────────────────────────────────────────────────┤
│ ✅ Managed infrastructure                        │
│ ✅ Auto-scaling                                  │
│ ✅ Built-in monitoring                           │
│ ✅ Simple API endpoint                           │
│ ⚠️ Requires internet connection                 │
│ ⚠️ Per-request pricing                          │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ EDGE (Local/Device)                             │
├─────────────────────────────────────────────────┤
│ ✅ No latency to cloud                           │
│ ✅ Works offline                                 │
│ ✅ No per-request cost                           │
│ ⚠️ Requires NVIDIA GPU                          │
│ ⚠️ You manage infrastructure                    │
└─────────────────────────────────────────────────┘

Which deployment target? [cloud / edge / both]
```

---

## vfrog Cloud Deployment Template

```
🚀 vfrog Cloud Deployment

Deploying to vfrog.ai...

Step 1: Verify credentials ✅
  API key found

Step 2: Configure deployment
  Model: {model_name}
  Class names: {class_list}

  Serving config:
    Min replicas: {min}
    Max replicas: {max}
    Target latency: {latency}ms
    Auto-scaling: {enabled}

Step 3: Upload model
  Uploading weights... {progress}%

Step 4: Deploy to staging
  Staging endpoint: {staging_url}

Step 5: Smoke test
  Testing with {n} sample images...

  Results:
    ✅ Inference working
    ✅ Latency: {avg_latency}ms (target: {target}ms)
    ✅ All classes detected

Step 6: Promote to production?

  This will make your model live at:
  {production_url}

  Proceed? [Y/n]
```

---

## vfrog Deployment Complete Template

```
🚀 Deployment Successful!

Your model is live on vfrog.ai

═══════════════════════════════════════════════════
ENDPOINT DETAILS
═══════════════════════════════════════════════════

API Endpoint:
  {endpoint_url}

API Key:
  {api_key}
  (Keep this secret!)

Dashboard:
  {dashboard_url}

═══════════════════════════════════════════════════
QUICK START
═══════════════════════════════════════════════════

vfrog CLI:
```bash
vfrog inference --api-key {api_key} --image image.jpg --json
```

cURL:
```bash
curl -X POST {endpoint_url} \
  -H "Authorization: Bearer {api_key}" \
  -F "image=@image.jpg"
```

Python (requires httpx):
```python
import httpx

response = httpx.post(
    "{endpoint_url}",
    headers={"Authorization": "Bearer {api_key}"},
    files={"image": open("image.jpg", "rb")}
)
print(response.json())
```

═══════════════════════════════════════════════════
MONITORING
═══════════════════════════════════════════════════

View metrics, logs, and usage at:
{dashboard_url}

Rollback available if needed:
  croak rollback
```

---

## Edge Export Template

```
🚀 Edge Export

Target format: {format}

═══════════════════════════════════════════════════
EXPORT CONFIGURATION
═══════════════════════════════════════════════════

Source: {model_path}
Format: {onnx / tensorrt / cuda}
Precision: {fp32 / fp16 / int8}
Input size: {image_size}

{if tensorrt}
TensorRT options:
  Workspace: {workspace_gb}GB
  Dynamic batch: {enabled}
  Calibration: {calibration_status}
{/if}

═══════════════════════════════════════════════════
EXPORT PROGRESS
═══════════════════════════════════════════════════

[1/4] Converting to ONNX... ✅
      Output: {onnx_path}
      Size: {size_mb}MB

{if tensorrt}
[2/4] Optimizing ONNX... ✅

[3/4] Building TensorRT engine... ⏳
      This may take a few minutes...
      Building for: {gpu_name}

[4/4] Validating engine... ✅
{/if}

═══════════════════════════════════════════════════
BENCHMARK RESULTS
═══════════════════════════════════════════════════

Tested on: {gpu_name}

               Original    Optimized   Speedup
Latency (ms)   {orig}      {opt}       {speedup}x
Throughput     {orig_fps}  {opt_fps}   {speedup}x
Model size     {orig_mb}   {opt_mb}    {reduction}% smaller

═══════════════════════════════════════════════════
OUTPUT FILES
═══════════════════════════════════════════════════

Model:      {model_output_path}
Script:     {inference_script_path}
Config:     {config_path}

The inference script is ready to run:
  python {inference_script_path} --image path/to/image.jpg
```

---

## Generated Inference Script Template

```python
#!/usr/bin/env python3
"""
CROAK Edge Inference Script
Generated: {timestamp}
Model: {model_name}
Format: {format}
"""

import argparse
from pathlib import Path
{imports}

# Model configuration
MODEL_PATH = "{model_path}"
CLASS_NAMES = {class_names}
CONFIDENCE_THRESHOLD = {threshold}
IMAGE_SIZE = {image_size}

{inference_code}

def main():
    parser = argparse.ArgumentParser(description="Run inference")
    parser.add_argument("--image", required=True, help="Path to image")
    parser.add_argument("--threshold", type=float, default=CONFIDENCE_THRESHOLD)
    parser.add_argument("--output", help="Path to save annotated image")
    args = parser.parse_args()

    # Load model
    model = load_model(MODEL_PATH)

    # Run inference
    results = predict(model, args.image, args.threshold)

    # Print results
    for det in results:
        print(f"{det['class']}: {det['confidence']:.2f} at {det['bbox']}")

    # Save annotated image if requested
    if args.output:
        save_annotated(args.image, results, args.output)
        print(f"Saved to {args.output}")

if __name__ == "__main__":
    main()
```

---

## Smoke Test Template

```
🚀 Smoke Test Results

Testing deployed model...

═══════════════════════════════════════════════════
TEST RESULTS
═══════════════════════════════════════════════════

Test images: {n}

✅ Inference: Working
✅ Latency: {avg}ms avg (target: {target}ms)
✅ Memory: {memory_mb}MB
✅ Classes: All {n} classes detected

Sample predictions:
  Image 1: {detections}
  Image 2: {detections}
  Image 3: {detections}

═══════════════════════════════════════════════════
VALIDATION PASSED
═══════════════════════════════════════════════════

Your deployment is healthy and ready for production traffic.
```

---

## Rollback Template

```
🚀 Rollback

⚠️ You're about to rollback to a previous deployment.

Current version:  {current_version}
Rollback to:      {previous_version}

This will:
1. Stop the current deployment
2. Restore the previous model version
3. Update the endpoint to serve the old model

Reason for rollback (optional): ___

Proceed with rollback? [Y/n]

---

✅ Rollback complete

Your endpoint is now serving: {previous_version}
Rolled back from: {current_version}

The rolled-back version is preserved and can be redeployed later.
```
