# Annotation Formats

## Overview

CROAK uses YOLO format internally. This guide covers conversion from common formats.

| Format | Origin | File Type | Coordinates |
|--------|--------|-----------|-------------|
| YOLO | Ultralytics | .txt | Normalized center |
| COCO | Microsoft | .json | Absolute corner |
| Pascal VOC | ImageNet | .xml | Absolute corner |

## YOLO Format (Primary)

### Structure

One `.txt` file per image, same name:
```
image001.jpg  →  image001.txt
image002.jpg  →  image002.txt
```

### Format

```
class_id x_center y_center width height
class_id x_center y_center width height
...
```

- `class_id`: Integer starting at 0
- `x_center, y_center`: Box center (0-1, normalized)
- `width, height`: Box dimensions (0-1, normalized)

### Example

Image: 640×480 pixels
Object: Person at box (100, 120, 200, 300) [x1, y1, x2, y2]

```
# Calculate normalized values
x_center = (100 + 200) / 2 / 640 = 0.234
y_center = (120 + 300) / 2 / 480 = 0.438
width = (200 - 100) / 640 = 0.156
height = (300 - 120) / 480 = 0.375

# YOLO format
0 0.234 0.438 0.156 0.375
```

### data.yaml

```yaml
path: /path/to/dataset
train: images/train
val: images/val
test: images/test

nc: 3  # number of classes
names:
  0: person
  1: car
  2: bicycle
```

## COCO Format

### Structure

Single JSON file for entire dataset:
```
annotations/
  instances_train.json
  instances_val.json
```

### Format

```json
{
  "images": [
    {
      "id": 1,
      "file_name": "image001.jpg",
      "width": 640,
      "height": 480
    }
  ],
  "annotations": [
    {
      "id": 1,
      "image_id": 1,
      "category_id": 1,
      "bbox": [100, 120, 100, 180],
      "area": 18000,
      "iscrowd": 0
    }
  ],
  "categories": [
    {"id": 1, "name": "person"},
    {"id": 2, "name": "car"}
  ]
}
```

- `bbox`: [x_min, y_min, width, height] in pixels
- `category_id`: Starts at 1 (not 0)

### COCO to YOLO Conversion

```python
import json
from pathlib import Path

def coco_to_yolo(coco_json_path, output_dir):
    with open(coco_json_path) as f:
        coco = json.load(f)

    # Build lookups
    images = {img['id']: img for img in coco['images']}
    categories = {cat['id']: cat['name'] for cat in coco['categories']}

    # Group annotations by image
    img_annotations = {}
    for ann in coco['annotations']:
        img_id = ann['image_id']
        if img_id not in img_annotations:
            img_annotations[img_id] = []
        img_annotations[img_id].append(ann)

    # Convert each image
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for img_id, img_info in images.items():
        img_w, img_h = img_info['width'], img_info['height']
        label_file = output_dir / f"{Path(img_info['file_name']).stem}.txt"

        lines = []
        for ann in img_annotations.get(img_id, []):
            # COCO bbox: [x_min, y_min, width, height]
            x_min, y_min, w, h = ann['bbox']

            # Convert to YOLO format
            x_center = (x_min + w / 2) / img_w
            y_center = (y_min + h / 2) / img_h
            width = w / img_w
            height = h / img_h

            # COCO categories start at 1, YOLO at 0
            class_id = ann['category_id'] - 1

            lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

        with open(label_file, 'w') as f:
            f.write('\n'.join(lines))
```

## Pascal VOC Format

### Structure

One XML file per image:
```
Annotations/
  image001.xml
  image002.xml
```

### Format

```xml
<annotation>
  <folder>images</folder>
  <filename>image001.jpg</filename>
  <size>
    <width>640</width>
    <height>480</height>
    <depth>3</depth>
  </size>
  <object>
    <name>person</name>
    <bndbox>
      <xmin>100</xmin>
      <ymin>120</ymin>
      <xmax>200</xmax>
      <ymax>300</ymax>
    </bndbox>
  </object>
</annotation>
```

- Coordinates are absolute pixels
- Uses corner coordinates (xmin, ymin, xmax, ymax)

### VOC to YOLO Conversion

```python
import xml.etree.ElementTree as ET
from pathlib import Path

def voc_to_yolo(voc_xml_path, output_path, class_names):
    tree = ET.parse(voc_xml_path)
    root = tree.getroot()

    # Get image size
    size = root.find('size')
    img_w = int(size.find('width').text)
    img_h = int(size.find('height').text)

    lines = []
    for obj in root.findall('object'):
        class_name = obj.find('name').text
        if class_name not in class_names:
            continue
        class_id = class_names.index(class_name)

        bbox = obj.find('bndbox')
        xmin = float(bbox.find('xmin').text)
        ymin = float(bbox.find('ymin').text)
        xmax = float(bbox.find('xmax').text)
        ymax = float(bbox.find('ymax').text)

        # Convert to YOLO
        x_center = (xmin + xmax) / 2 / img_w
        y_center = (ymin + ymax) / 2 / img_h
        width = (xmax - xmin) / img_w
        height = (ymax - ymin) / img_h

        lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
```

## Conversion Summary

### To YOLO from COCO

```python
# bbox: [x_min, y_min, w, h]
x_center = (x_min + w/2) / img_w
y_center = (y_min + h/2) / img_h
width = w / img_w
height = h / img_h
class_id = category_id - 1  # COCO starts at 1
```

### To YOLO from VOC

```python
# bbox: [xmin, ymin, xmax, ymax]
x_center = (xmin + xmax) / 2 / img_w
y_center = (ymin + ymax) / 2 / img_h
width = (xmax - xmin) / img_w
height = (ymax - ymin) / img_h
```

### From YOLO to Absolute

```python
# Reverse conversion (for visualization)
x_min = (x_center - width/2) * img_w
y_min = (y_center - height/2) * img_h
x_max = (x_center + width/2) * img_w
y_max = (y_center + height/2) * img_h
```

## Validation

After conversion, verify:

```python
def validate_yolo_labels(label_dir):
    issues = []

    for label_file in Path(label_dir).glob('*.txt'):
        with open(label_file) as f:
            for line_num, line in enumerate(f, 1):
                parts = line.strip().split()

                if len(parts) != 5:
                    issues.append(f"{label_file}:{line_num} - Expected 5 values")
                    continue

                class_id, x, y, w, h = parts
                x, y, w, h = float(x), float(y), float(w), float(h)

                if not (0 <= x <= 1 and 0 <= y <= 1):
                    issues.append(f"{label_file}:{line_num} - Center out of range")

                if not (0 < w <= 1 and 0 < h <= 1):
                    issues.append(f"{label_file}:{line_num} - Size out of range")

    return issues
```

## Using CROAK Convert

```bash
# Convert COCO to YOLO
croak convert --from coco --to yolo

# Convert VOC to YOLO
croak convert --from voc --to yolo
```
