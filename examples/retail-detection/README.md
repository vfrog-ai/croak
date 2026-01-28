# Example: Retail Product Detection

This example demonstrates using CROAK to build a retail product detection model.

## Scenario

You're building a system to detect products on retail shelves for inventory management.

## Prerequisites

- Python 3.10+
- vfrog.ai account (for annotation)
- ~200 images of retail shelves

## Quick Start

### 1. Initialize Project

```bash
cd retail-detection
croak init --name "retail-product-detection"
```

### 2. Add Your Images

```bash
# Copy your images to data/raw/
cp /path/to/your/images/*.jpg data/raw/
```

### 3. Prepare Data

```bash
# Scan images
croak scan data/raw

# Validate quality
croak validate

# Annotate with vfrog (opens browser)
croak annotate

# Create splits
croak split
```

### 4. Train Model

```bash
# Get architecture recommendation
croak recommend

# Configure and train
croak train
```

### 5. Evaluate

```bash
# Run evaluation
croak evaluate

# View detailed report
croak report
```

### 6. Deploy

```bash
# Deploy to vfrog cloud
croak deploy cloud

# OR export for edge
croak export --format tensorrt
```

## Expected Results

With ~500 annotated images and 5 product classes:
- Training time: ~4 hours on T4
- Expected mAP@50: 0.70-0.85
- Inference speed: ~30 FPS on edge device

## Project Structure

```
retail-detection/
├── .croak/
│   ├── config.yaml
│   └── pipeline-state.yaml
├── data/
│   ├── raw/                    # Your original images
│   ├── annotations/            # From vfrog
│   └── processed/              # Training-ready dataset
├── training/
│   ├── configs/
│   └── experiments/
├── evaluation/
│   └── reports/
└── deployment/
    ├── cloud/
    └── edge/
```

## Classes

Example class definitions:
1. `soda_can`
2. `water_bottle`
3. `snack_bag`
4. `cereal_box`
5. `produce_item`

## Tips

- Ensure good lighting in images
- Include empty shelf sections for negative samples
- Label partially visible products
- Maintain consistent camera angle if possible
