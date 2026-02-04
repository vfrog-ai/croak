# Step 2: Scan Data Directory

## Execution Rules
- 🐸 ALWAYS report total image count and formats
- ✅ ALWAYS check for existing annotations
- ⚠️ ALWAYS warn if image count < 100

## Your Task
Discover all images and existing annotations in the data directory.

## Execution Sequence

### 1. Scan for Images

```python
from pathlib import Path
import imghdr

SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}

def scan_images(directory: Path) -> dict:
    images = []
    for path in directory.rglob('*'):
        if path.suffix.lower() in SUPPORTED_FORMATS:
            images.append(path)
    return images
```

### 2. Analyze Image Properties

For each image, collect:
- File path
- Format
- Dimensions (width, height)
- File size

```python
from PIL import Image

def get_image_info(path: Path) -> dict:
    with Image.open(path) as img:
        return {
            'path': str(path),
            'format': img.format,
            'size': img.size,
            'file_size': path.stat().st_size
        }
```

### 3. Check for Existing Annotations

Look for annotation files:
- YOLO format: `.txt` files with same name as images
- COCO format: `annotations.json` or `instances_*.json`
- Pascal VOC: `.xml` files

```python
def detect_annotation_format(directory: Path) -> str:
    # Check for YOLO txt files
    # Check for COCO json
    # Check for VOC xml
    return detected_format or None
```

### 4. Report Findings

```
📊 Data Scan Results

Directory: {path}

═══════════════════════════════════════════════════
IMAGES FOUND
═══════════════════════════════════════════════════

Total: {count} images

By format:
  JPG:  {count}
  PNG:  {count}
  Other: {count}

Size range:
  Smallest: {min_w}x{min_h}
  Largest:  {max_w}x{max_h}
  Median:   {med_w}x{med_h}

File sizes:
  Total: {total_mb} MB
  Average: {avg_kb} KB per image

═══════════════════════════════════════════════════
EXISTING ANNOTATIONS
═══════════════════════════════════════════════════

{if found}
Format detected: {format}
Coverage: {percent}% of images
Classes found: {class_list}
{else}
No existing annotations found.
Images will need to be annotated via vfrog.
{/if}

═══════════════════════════════════════════════════
ASSESSMENT
═══════════════════════════════════════════════════

{if count < 100}
⚠️ Warning: Only {count} images found.
   Object detection typically needs 100+ images for decent results.
   Consider collecting more data.
{else}
✅ Image count looks good for training.
{/if}
```

### 5. Update Pipeline State

```yaml
artifacts:
  dataset:
    path: {directory}
    total_images: {count}
    formats: {format_breakdown}
    existing_annotations: {format or null}

stages_completed:
  - "data_init"
  - "data_scan"
```

## Outputs

- `image_inventory`: List of all images with metadata
- `existing_annotations`: Annotation format if found, null otherwise

## Completion

> "Scan complete! Found {count} images.
>
> Next step: Validate data quality
>
> Run: `croak validate`"

WAIT for user before loading step-03-validate.md
