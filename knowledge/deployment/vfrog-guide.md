# vfrog CLI Integration Guide

## Overview

vfrog is a platform for object detection annotation and training. CROAK integrates
with the **vfrog CLI** -- a Go binary that manages authentication, dataset images,
objects, iterations, training, and inference.

vfrog provides two capabilities that CROAK uses:

1. **Annotation + Training (SSAT)** -- Iterative auto-annotation and platform-managed
   training. Recommended for users who want simplicity.
2. **Inference** -- Run predictions against a trained vfrog model endpoint.

## Installation

The vfrog CLI is a standalone Go binary. It is NOT a Python package.

### Download

Download the latest release for your platform:

```
https://github.com/vfrog/vfrog-cli/releases
```

### Install

**macOS / Linux:**
```bash
# Download (adjust URL for your OS/arch)
chmod +x vfrog
sudo mv vfrog /usr/local/bin/

# Verify
vfrog version
```

**Windows:**
```
Download vfrog.exe and add its directory to your PATH.
```

### Verify Installation

```bash
vfrog version
```

If this prints a version string, the CLI is installed correctly.

## Authentication

The vfrog CLI uses **email/password authentication** via Supabase. This is NOT
API-key based -- the CLI stores auth tokens in `~/.vfrog/`.

### Login

```bash
vfrog login --email user@example.com --password yourpassword
```

Or via CROAK:

```bash
croak vfrog setup
```

This interactive command handles login, organisation selection, and project selection.

### Check Auth Status

```bash
vfrog config show --json
```

Returns JSON with `authenticated: true/false` plus the current context.

### API Key (Inference Only)

The `VFROG_API_KEY` environment variable is only needed for the `vfrog inference`
command. It is NOT used for CLI authentication.

```bash
export VFROG_API_KEY=your_key_here
```

Get your API key at https://platform.vfrog.ai.

## Context Hierarchy

The vfrog CLI uses a hierarchical context that must be set in order:

```
Organisation
  └── Project
       └── Object (product image)
            └── Iteration (SSAT annotation + training cycle)
```

### Set Context

```bash
# 1. Set organisation (required for all commands)
vfrog config set organisation --organisation_id <uuid>

# 2. Set project (required for most commands)
vfrog config set project --project_id <uuid>

# 3. Set object (required for iteration commands)
vfrog config set object --object_id <uuid>
```

### View Current Context

```bash
vfrog config show --json
```

Returns:
```json
{
  "authenticated": true,
  "organisation_id": "uuid-here",
  "project_id": "uuid-here",
  "object_id": "uuid-here-or-empty"
}
```

## Two Paths: vfrog SSAT vs Classic

CROAK supports two parallel annotation and training workflows. Users are never
locked into one path.

### Path A: vfrog SSAT (Recommended for Simplicity)

vfrog handles annotation, training, and iteration for you:

1. Upload dataset images (URLs)
2. Create an object (reference/product image)
3. Create an iteration → SSAT auto-annotates
4. Review in HALO (web UI)
5. Train on vfrog platform
6. Create next iteration → model improves

**Best for:** New users, fast prototyping, when you don't need to choose
architecture or hyperparameters.

### Path B: Classic (Full Control)

Use external annotation tools and train locally or on Modal.com:

1. Annotate with CVAT, Label Studio, Roboflow, or LabelImg
2. Import annotations (`croak annotate --method classic`)
3. Choose architecture (YOLOv8, RT-DETR, etc.)
4. Train locally or on Modal.com
5. Full control over hyperparameters, augmentation, epochs

**Best for:** Experienced ML engineers, custom architectures, when you need
full control over the training pipeline.

## vfrog SSAT Workflow (Detailed)

### 1. Upload Dataset Images

vfrog CLI v0.1 requires **image URLs** (not local files). Images must be
accessible via public or pre-signed URLs.

```bash
vfrog dataset_images upload <url1> <url2> ... --json
```

List uploaded images:
```bash
vfrog dataset_images list --json
```

Delete an image:
```bash
vfrog dataset_images delete --dataset_image_id <uuid>
```

### 2. Create Object (Product Image)

The object is the reference image of what you want to detect:

```bash
vfrog objects create <image_url> --label "target-object" --json
```

List objects:
```bash
vfrog objects list --json
```

### 3. Create Iteration

An iteration selects a subset of dataset images for annotation:

```bash
vfrog iterations create <object_id> --random 20 --json
```

Default image counts by iteration: #1=20, #2=40, #3+=80.

### 4. Run SSAT Auto-Annotation

SSAT (Semi-Supervised Active Training) auto-annotates the iteration images:

```bash
vfrog iterations ssat --iteration_id <uuid> --json
```

- **Iteration 1:** Uses cutout extraction and matching (no model yet)
- **Iteration 2+:** Uses the trained model from the previous iteration

Override random count:
```bash
vfrog iterations ssat --iteration_id <uuid> --random 40 --json
```

### 5. HALO Review

HALO (Human Assisted Labelling of Objects) is vfrog's web UI for reviewing
and correcting auto-annotations:

```bash
vfrog iterations halo --iteration_id <uuid> --json
```

Returns a URL to open in the browser. Review the annotations, fix any mistakes,
then return to CROAK.

### 6. Train on vfrog Platform

After HALO review, train the model on vfrog's infrastructure:

```bash
vfrog iteration train --iteration_id <uuid> --json
```

vfrog manages architecture, hyperparameters, and GPU allocation. You don't
configure these -- the platform handles it.

### 7. Next Iteration

Create the next iteration to improve the model:

```bash
vfrog iterations next --iteration_id <uuid> --json
```

Each subsequent iteration uses the trained model for better auto-annotation.

### 8. Restart Iteration

If an iteration needs to be redone:

```bash
vfrog iterations restart --iteration_id <uuid> --json
```

## Inference

Run predictions against a trained vfrog model using the API key:

```bash
# From local file
vfrog inference --api-key <key> --image /path/to/image.jpg --json

# From URL
vfrog inference --api-key <key> --image_url https://example.com/image.jpg --json
```

The `--api-key` flag can be omitted if `VFROG_API_KEY` is set.

## CROAK Integration

### Setup

```bash
croak vfrog setup    # Interactive login + org/project selection
croak vfrog status   # Show current CLI config and auth status
```

### Annotation

```bash
croak annotate                 # Defaults to vfrog SSAT
croak annotate --method vfrog  # Explicit vfrog SSAT
croak annotate --method classic # External tools + import
```

### Training

```bash
croak train --provider vfrog   # Platform-managed (uses SSAT iterations)
croak train --provider local   # Local GPU (classic path, YOLOv8/RT-DETR)
croak train --provider modal   # Modal.com serverless GPU (classic path)
```

### Deployment

```bash
croak deploy vfrog             # Verify inference on vfrog endpoint
croak deploy modal             # Deploy to Modal.com serverless
croak deploy edge              # Export for edge devices (ONNX/TensorRT)
```

### Health Check

```bash
croak doctor                   # Checks vfrog CLI, auth, and context
```

## Python API (CROAK Internal)

CROAK wraps the vfrog CLI via `VfrogCLI` in `src/croak/integrations/vfrog.py`:

```python
from croak.integrations.vfrog import VfrogCLI

# Setup checks
VfrogCLI.check_installed()      # Binary on PATH?
VfrogCLI.check_authenticated()  # Logged in?
VfrogCLI.get_config()           # Current context

# Dataset images
VfrogCLI.upload_dataset_images(['https://...', 'https://...'])
VfrogCLI.list_dataset_images()

# Objects
VfrogCLI.create_object('https://...', label='my-product')
VfrogCLI.list_objects()

# Iterations
VfrogCLI.create_iteration(object_id, random_count=20)
VfrogCLI.run_ssat(iteration_id)
VfrogCLI.get_halo_url(iteration_id)
VfrogCLI.train_iteration(iteration_id)
VfrogCLI.next_iteration(iteration_id)

# Inference
VfrogCLI.run_inference(image_path='/path/to/image.jpg')
```

All methods return `{'success': bool, 'output': ..., 'error': ...}`.

## Known Limitations (CLI v0.1)

| Limitation | Impact | Workaround |
|-----------|--------|------------|
| **URL-only uploads** | Cannot upload local files directly | Host images on S3/GCS and use pre-signed URLs |
| **No annotation export** | Cannot download annotations as YOLO/COCO files | Use vfrog SSAT path end-to-end; for classic path, use external tools |
| **No deploy commands** | Cannot deploy models via CLI | Use `vfrog inference` to verify; deploy via CROAK to Modal or edge |
| **No model download** | Cannot download trained weights | Use vfrog inference endpoint; for local models, use classic training |
| **Platform-managed training** | No control over architecture or hyperparams | Use classic path (`--provider local` or `--provider modal`) for full control |

## Troubleshooting

### vfrog CLI Not Found

```
Error: vfrog CLI not found

Fix:
1. Download from https://github.com/vfrog/vfrog-cli/releases
2. Make executable: chmod +x vfrog
3. Move to PATH: sudo mv vfrog /usr/local/bin/
4. Verify: vfrog version
```

### Not Authenticated

```
Error: Not logged in to vfrog

Fix:
1. Run: croak vfrog setup
2. Or manually: vfrog login --email user@example.com --password yourpass
```

### Context Not Set

```
Error: Organisation/project not configured

Fix:
1. Run: croak vfrog setup (interactive)
2. Or manually:
   vfrog config set organisation --organisation_id <uuid>
   vfrog config set project --project_id <uuid>
```

### Upload Fails

```
Error: Failed to upload dataset images

Fix:
1. Ensure URLs are publicly accessible or pre-signed
2. Check that project context is set
3. Verify authentication: vfrog config show --json
```

### API Key Invalid (Inference)

```
Error: VFROG_API_KEY not set or invalid

Fix:
1. Get your API key from https://platform.vfrog.ai
2. Set: export VFROG_API_KEY=your_key_here
Note: API key is only needed for inference, not for CLI auth.
```
