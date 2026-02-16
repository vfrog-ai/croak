# Step 4: Annotate Dataset Images

This step supports two annotation methods. Scout recommends vfrog for its simplicity
but fully supports classic annotation tools.

## Method Selection

Scout should ask: "Would you like to use vfrog for annotation? It handles
auto-annotation and iterative refinement for you. Or would you prefer to use your
own annotation tool and import the labels?"

Default: vfrog (`--method vfrog`)

## Skip Condition

Skip this step if:
- Annotations already exist and cover 100% of images
- Annotations passed validation in previous step

---

## Path A: vfrog SSAT (Recommended)

### Execution Rules
- ALWAYS verify vfrog CLI is installed and authenticated
- ALWAYS verify organisation and project context is set
- WAIT for user to complete HALO review before proceeding
- Record annotation_source as "vfrog" in pipeline state

### Execution Sequence

#### 1. Verify vfrog Setup

```python
from croak.integrations.vfrog import VfrogCLI

VfrogCLI.check_installed()       # vfrog binary on PATH
VfrogCLI.check_authenticated()   # logged in via vfrog login
VfrogCLI.get_config()            # verify org + project set
```

If not set up:
> "You'll need the vfrog CLI to annotate your images.
>
> **Setup steps:**
>
> 1. Install the CLI from https://github.com/vfrog-ai/vfrog-cli/releases
> 2. Run `croak vfrog setup` to login and select your organisation/project
>
> Ready? Run `croak vfrog setup` to get started."

#### 2. Upload Dataset Images

```python
# Upload from local directory
VfrogCLI.upload_dataset_images(directory="data/raw")

# Or upload individual files
VfrogCLI.upload_dataset_images(file_path="/path/to/image.jpg")

# Or upload from URLs
VfrogCLI.upload_dataset_images(urls=["https://example.com/img.jpg"])
```

#### 3. Create Object (Product Image)

```python
# From URL
VfrogCLI.create_object(url=product_image_url, label="target-object")

# Or from local file
VfrogCLI.create_object(file_path="/path/to/product.jpg", label="target-object")

VfrogCLI.set_object(object_id)
```

The object is the reference image of what you want to detect.

#### 4. Create Iteration

```python
VfrogCLI.create_iteration(object_id, random_count=20)
```

Default image counts by iteration: #1=20, #2=40, #3+=80.

#### 5. Run SSAT Auto-Annotation

```python
VfrogCLI.run_ssat(iteration_id)
```

SSAT (Semi-Supervised Active Training):
- Iteration 1: Uses cutout extraction and matching
- Iteration 2+: Uses trained model inference for auto-annotation

#### 6. Check SSAT Progress

```python
# Check iteration status
VfrogCLI.get_iteration_status(iteration_id)

# Or watch until complete
VfrogCLI.get_iteration_status(iteration_id, watch=True)
```

#### 7. Guide HALO Review

```python
halo_result = VfrogCLI.get_halo_url(iteration_id)
```

> "Your images have been auto-annotated!
>
> **Review in HALO:** {halo_url}
>
> Open this URL in your browser to review and correct the annotations.
> HALO is vfrog's annotation review tool -- it shows you the auto-annotations
> so you can fix any mistakes before training.
>
> When you're done reviewing, come back and we'll start training."

#### 8. Export Annotations (Optional)

```python
# Export to YOLO format for local training
VfrogCLI.export_yolo(iteration_id, output_dir="./data/processed")
```

#### 9. Update Pipeline State

```yaml
annotation_source: "vfrog"
vfrog_iteration_id: "{iteration_id}"
vfrog_object_id: "{object_id}"
```

### Why vfrog?
- Auto-annotation reduces manual work by 80-90%
- HALO review catches errors with human-in-the-loop
- Each iteration improves on the last -- model gets better as you annotate
- No ML expertise needed -- vfrog handles the complexity
- Training is one command away: `croak train --provider vfrog`

---

## Path B: Classic Annotation Import

### Execution Rules
- Support YOLO, COCO, and Pascal VOC annotation formats
- Validate imported annotations before accepting
- Record annotation_source as "classic" in pipeline state

### Execution Sequence

#### 1. Guide User to Annotation Tools

> "You can use any annotation tool that exports YOLO, COCO, or VOC format:
>
> **Recommended tools:**
> - **CVAT** -- Open source, powerful, supports YOLO export
> - **Label Studio** -- Flexible, supports many formats
> - **Roboflow** -- Cloud-based, easy to use
> - **LabelImg** -- Simple desktop tool for YOLO/VOC
>
> Annotate your images in data/raw/ with your preferred tool,
> then export the annotations."

#### 2. Accept Annotation Path

```python
annotations_path = click.prompt("Path to annotation files", type=click.Path(exists=True))
```

Accept `--format` flag: yolo (default), coco, voc.

#### 3. Validate Annotations

Run DataValidator on imported annotations:
- Format schema validation
- Bounding box sanity checks (positive area, within image bounds)
- Class name consistency
- Coverage check (annotations vs images)

#### 4. Copy to Project

```python
import shutil
for f in annotation_files:
    shutil.copy2(f, root / "data" / "annotations" / f.name)
```

#### 5. Update Pipeline State

```yaml
annotation_source: "classic"
annotation_format: "{format}"
```

### After Classic Annotation

> "Annotations imported!
>
> Next steps:
> 1. Validate: `croak validate`
> 2. Split: `croak split`
> 3. Train: `croak train --provider local` (or `--provider modal`)"

---

## Outputs

- `annotation_source`: "vfrog" or "classic"
- `annotations`: Path to annotation files (classic) or iteration reference (vfrog)
- `vfrog_iteration_id`: Reference to vfrog iteration (vfrog path only)

## Error Handling

### vfrog CLI Not Installed
> "vfrog CLI not found. Install from: https://github.com/vfrog-ai/vfrog-cli/releases
>
> Or use classic annotation: `croak annotate --method classic`"

### vfrog Not Authenticated
> "Not logged in to vfrog. Run `croak vfrog setup` first.
>
> Or use classic annotation: `croak annotate --method classic`"

### No Annotation Files Found (Classic)
> "No {format} annotation files found in {path}.
>
> Make sure you exported annotations in the correct format.
> Expected extensions: .txt (YOLO), .json (COCO), .xml (VOC)"

## Completion

WAIT for user confirmation before loading step-05-split.md
