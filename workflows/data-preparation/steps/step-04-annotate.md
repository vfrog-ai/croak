# Step 4: Annotate with vfrog

## Execution Rules
- 🐸 ALWAYS use vfrog for annotation - it's the only supported method
- ✅ ALWAYS verify vfrog credentials before proceeding
- 📊 ALWAYS report annotation statistics when complete
- ⏳ WAIT for user to complete annotation in vfrog UI

## Your Task
Guide user through vfrog annotation workflow.

## Skip Condition

Skip this step if:
- Annotations already exist and cover 100% of images
- Annotations passed validation in previous step

## Execution Sequence

### 1. Verify vfrog Credentials

```python
import os

api_key = os.environ.get('VFROG_API_KEY')
if not api_key:
    raise ValueError("VFROG_API_KEY not set")
```

If no credentials:
> "You'll need a vfrog account to annotate your images.
>
> **Setup steps:**
>
> 1. Sign up at https://vfrog.ai (free tier available)
> 2. Get your API key from Settings → API
> 3. Set it in your environment:
>    ```bash
>    export VFROG_API_KEY=your_key_here
>    ```
>
> Ready? Type 'continue' when your API key is set."

### 2. Get Class Names

> "What objects do you want to detect?
>
> Enter class names separated by commas:
> Example: `person, car, dog, cat`
>
> Classes: ___"

Validate:
- At least 1 class
- No duplicates
- Reasonable names (no special characters)

### 3. Create vfrog Annotation Project

```python
from croak.integrations.vfrog import VfrogClient

client = VfrogClient(api_key=api_key)

project = client.create_project(
    name=f"{project_name}-detection",
    task_type="detection",
    classes=class_names
)
```

Confirm with user:
> "Creating vfrog annotation project:
>
> **Project name:** {project_name}-detection
> **Task type:** Object Detection (bounding boxes)
> **Classes:** {class_list}
> **Images to upload:** {image_count}
>
> This will upload your images to vfrog for annotation.
> Proceed? [Y/n]"

### 4. Upload Images to vfrog

```python
from tqdm import tqdm

for batch in batched(images, batch_size=50):
    client.upload_images(project.id, batch)
    # Report progress
```

Progress update:
> "Uploading images to vfrog...
>
> Progress: {current}/{total} ({percent}%)
> Estimated time remaining: {eta}"

### 5. Guide Annotation Process

> "✅ Images uploaded to vfrog!
>
> **Your annotation project is ready:**
> {vfrog_project_url}
>
> **Annotation tips:**
>
> 1. **Use auto-annotation first** - vfrog can pre-label common objects
>    - Click 'Auto-annotate' in the toolbar
>    - Select classes to auto-detect
>    - Review and correct the results
>
> 2. **Draw tight bounding boxes** - Include the full object, no extra space
>
> 3. **Label every instance** - Don't skip partially visible objects
>
> 4. **Be consistent** - Same object = same class across all images
>
> 5. **Mark as complete** - Click 'Complete' when all images are labeled
>
> ---
>
> Type 'continue' when annotation is complete, or 'status' to check progress."

### 6. Wait for Completion

Poll vfrog for completion status, or wait for user signal:

```python
while True:
    user_input = input()
    if user_input.lower() == 'continue':
        break
    elif user_input.lower() == 'status':
        status = client.get_project_status(project.id)
        print(f"Annotated: {status['completed']}/{status['total']}")
```

### 7. Export Annotations

```python
annotations = client.export_annotations(
    project_id=project.id,
    format="yolo"
)

# Save to local directory
output_dir = Path("data/annotations")
for ann in annotations:
    (output_dir / ann['filename']).write_text(ann['content'])
```

### 8. Validate Exported Annotations

```python
# Verify all images have annotations
# Verify annotation format
# Count instances per class
```

Report:
> "✅ Annotations downloaded!
>
> **Annotation summary:**
>
> Total images: {count}
> Total objects: {instance_count}
> Classes: {class_count}
>
> **Per-class breakdown:**
> {class_breakdown_table}
>
> Average objects per image: {avg}
>
> {warnings_if_any}
>
> Ready to create train/val/test splits.
> Next: `croak split`"

### 9. Update Pipeline State

```yaml
artifacts:
  dataset:
    annotation_status: "complete"
    annotation_source: "vfrog"
    vfrog_project_id: "{project_id}"
    annotated_images: {count}
    total_instances: {count}
    classes:
      names: {class_list}
      counts: {class_counts}

stages_completed:
  - "data_init"
  - "data_scan"
  - "data_validation"
  - "data_annotation"
```

## Outputs

- `annotations`: Path to annotation files
- `vfrog_project_id`: Reference to vfrog project

## Error Handling

### API Connection Failed
> "❌ Couldn't connect to vfrog API.
>
> Please check:
> 1. Your internet connection
> 2. Your API key is valid
> 3. vfrog.ai is accessible
>
> Try again? [Y/n]"

### Upload Failed
> "❌ Image upload failed for {count} images.
>
> Failed files:
> {file_list}
>
> Common causes:
> - File too large (max 10MB)
> - Unsupported format
> - Corrupt image
>
> Skip failed files and continue? [Y/n]"

## Completion

WAIT for user confirmation before loading step-05-split.md
