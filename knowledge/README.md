# CROAK Knowledge Base

This directory contains reference documentation used by CROAK agents to provide accurate, context-aware guidance.

## Directory Structure

```
knowledge/
├── architectures/          # Model architecture details
│   ├── architecture-selection.md
│   └── yolo-family.md
│
├── training/               # Training guidance
│   ├── hyperparameter-guide.md
│   └── common-training-issues.md
│
├── evaluation/             # Evaluation and metrics
│   ├── detection-metrics.md
│   └── performance-debugging.md
│
├── deployment/             # Deployment guides
│   ├── vfrog-guide.md
│   ├── edge-deployment.md
│   └── export-formats.md
│
├── data/                   # Data preparation
│   ├── data-quality-checklist.md
│   └── annotation-formats.md
│
└── gpu-setup/              # Compute setup
    └── gpu-setup-modal.md
```

## Priority Files (v1.0)

These 12 files are essential for v1.0 launch:

1. `architecture-selection.md` - Model selection decision framework
2. `yolo-family.md` - YOLO v8/v11 architecture documentation
3. `hyperparameter-guide.md` - Training parameter guidance
4. `common-training-issues.md` - Training troubleshooting
5. `detection-metrics.md` - Metric explanations
6. `performance-debugging.md` - Model failure diagnosis
7. `vfrog-guide.md` - vfrog platform integration
8. `edge-deployment.md` - TensorRT/CUDA deployment
9. `export-formats.md` - ONNX/TensorRT conversion
10. `gpu-setup-modal.md` - Modal.com setup
11. `data-quality-checklist.md` - Data validation
12. `annotation-formats.md` - YOLO/COCO/VOC formats

## Usage

Agents reference these files when:
- Making recommendations
- Explaining concepts
- Troubleshooting issues
- Providing deployment guidance

Files are written in Markdown and designed to be:
- Concise but comprehensive
- Actionable with specific recommendations
- Up-to-date with 2025/2026 best practices
