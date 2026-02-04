# Common Workflows

This document describes typical user workflows and their stage sequences to help anticipate user needs.

## Workflow 1: New Project from Scratch

**Scenario**: User has raw images, no annotations, wants to train a detector.

**Typical Sequence**:
```
1. croak init                    # Initialize project
2. [User adds images to data/raw/]
3. croak scan data/raw           # Discover images
4. croak annotate                # Send to vfrog for labeling
5. [Wait for annotations]
6. croak validate                # Check data quality
7. croak split                   # Create train/val/test
   -- OR --
   croak prepare                 # Run full data pipeline
8. croak recommend               # Get architecture suggestion
9. croak estimate                # Check cost/time
10. croak train                  # Train model
11. croak evaluate               # Assess performance
12. croak export --format onnx   # Export for deployment
```

**Duration**: Days to weeks (annotation is the bottleneck)

**Common Issues**:
- Insufficient images (< 100)
- Class imbalance
- Poor annotation quality

---

## Workflow 2: Pre-annotated Dataset

**Scenario**: User has images with existing COCO/VOC/YOLO annotations.

**Typical Sequence**:
```
1. croak init
2. [User adds images + annotations]
3. croak scan data/raw           # Detect existing annotations
4. croak validate                # Check format and quality
5. croak convert --to yolo       # Convert if needed
6. croak split
7. croak train
8. croak evaluate
9. croak deploy
```

**Duration**: Hours to days

**Common Issues**:
- Format conversion errors
- Annotation schema mismatches
- Missing class mappings

---

## Workflow 3: Iterate on Existing Model

**Scenario**: User trained a model, wants to improve it.

**Typical Sequence**:
```
1. croak evaluate                # Check current performance
2. croak analyze                 # Understand failures
3. croak diagnose                # Get improvement suggestions

   # Option A: More/better data
4a. [User adds more images]
5a. croak scan data/raw
6a. croak annotate               # Label new images
7a. croak prepare
8a. croak train                  # Retrain with more data

   # Option B: Different architecture
4b. croak recommend              # Try different model
5b. croak train --architecture yolov8m
6b. croak evaluate
7b. croak compare                # Compare experiments
```

**Duration**: Hours to days per iteration

**Common Issues**:
- Diminishing returns on more data
- Overfitting with larger models
- Class-specific failures

---

## Workflow 4: Quick Prototype

**Scenario**: User wants fast results to validate approach.

**Typical Sequence**:
```
1. croak init
2. [User adds ~100 images]
3. croak scan data/raw
4. croak annotate                # Minimal annotations
5. croak prepare
6. croak train --epochs 50       # Fewer epochs
7. croak evaluate
```

**Duration**: Hours

**Common Issues**:
- Unrealistic expectations from small data
- Underfitting with few epochs

---

## Workflow 5: Deploy to Edge

**Scenario**: User needs model on embedded device.

**Typical Sequence**:
```
1. [After training and evaluation]
2. croak export --format onnx
3. croak export --format tflite --half    # Quantized
4. croak deploy edge
5. [Test on target device]
6. [If too slow] croak recommend --edge   # Smaller architecture
7. croak train --architecture yolov8n
8. croak evaluate
9. croak export --format tflite --half
```

**Duration**: Hours

**Common Issues**:
- Model too large for device
- Accuracy drops after quantization
- Missing edge runtime dependencies

---

## Workflow 6: Deploy to Cloud

**Scenario**: User wants API endpoint for inference.

**Typical Sequence**:
```
1. [After training and evaluation]
2. croak deploy cloud --name my-detector
3. [Test endpoint]
4. [Monitor usage]
```

**Duration**: Minutes

**Common Issues**:
- Modal.com authentication
- Cold start latency
- Cost management

---

## Workflow Shortcuts

For experienced users, these single commands run multi-step workflows:

| Command | Steps Included |
|---------|----------------|
| `croak prepare` | validate → split |
| `croak train` | configure → estimate → execute |

---

## User Journey Patterns

### The Explorer
- Asks lots of questions before starting
- Wants to understand each step
- Route: Provide detailed explanations, suggest `croak help`

### The Rusher
- Wants fastest path to results
- Skips optional steps
- Route: Suggest workflow shortcuts, warn about skipped validations

### The Perfectionist
- Wants best possible metrics
- Iterates many times
- Route: Emphasize `croak analyze`, `croak compare`

### The Deployer
- Already has a model
- Just wants to ship it
- Route: Jump straight to Deployment Agent
