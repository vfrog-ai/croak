# Agent Capabilities Summary

Quick reference for routing decisions based on agent capabilities.

## Router Agent (Dispatcher)

**Role**: Pipeline Coordinator + Request Router

**Capabilities**:
| ID | Name | Description |
|----|------|-------------|
| request_classification | Request Classification | Analyze user intent and determine which specialist agent should handle it |
| state_management | State Management | Track pipeline progress, persist state, and detect inconsistencies |
| next_step_guidance | Next Step Guidance | Suggest logical next action based on current pipeline state |
| agent_handoff | Agent Handoff | Transfer context and relevant state to specialist agents |
| status_reporting | Status Reporting | Summarize pipeline state, completed stages, and pending work |
| project_initialization | Project Initialization | Initialize new CROAK project with config and state files |

**Handles Directly**:
- `status`, `init`, `reset`, `help`, `next`, `history`

---

## Data Agent (Scout)

**Role**: Data Quality Specialist + Dataset Engineer

**Capabilities**:
| ID | Name | Description |
|----|------|-------------|
| data_discovery | Data Discovery | Scan directories recursively, identify images, detect existing annotations |
| quality_validation | Quality Validation | Check image integrity, annotation validity, class balance, and data consistency |
| format_conversion | Format Conversion | Convert between COCO, Pascal VOC, and YOLO annotation formats |
| dataset_splitting | Dataset Splitting | Create stratified train/val/test splits preserving class distribution |
| vfrog_annotation | vfrog Annotation | Trigger and manage vfrog.ai annotation workflow for labeling |
| statistics_generation | Statistics Generation | Compute comprehensive dataset statistics and visualizations |
| data_augmentation_planning | Data Augmentation Planning | Recommend augmentation strategies based on data characteristics |

**Key Commands**:
- `scan`, `validate`, `convert`, `split`, `annotate`, `stats`, `prepare`, `visualize`

---

## Training Agent (Coach)

**Role**: ML Training Specialist + Experiment Design Expert

**Capabilities**:
| ID | Name | Description |
|----|------|-------------|
| architecture_selection | Architecture Selection | Recommend model architecture based on requirements and constraints |
| config_generation | Config Generation | Generate training configuration files with sensible defaults |
| script_generation | Script Generation | Generate training scripts for local or cloud execution |
| gpu_guidance | GPU Guidance | Guide user to provision appropriate GPU environment |
| cost_estimation | Cost Estimation | Estimate training time and compute cost before running |
| experiment_tracking | Experiment Tracking | Setup and integrate experiment tracking (MLflow/W&B) |
| checkpoint_management | Checkpoint Management | Handle checkpoints, resume interrupted training |

**Key Commands**:
- `recommend`, `configure`, `estimate`, `train`, `resume`, `compare`

---

## Evaluation Agent (Judge)

**Role**: Model Analyst + Quality Assessor

**Capabilities**:
| ID | Name | Description |
|----|------|-------------|
| metrics_computation | Metrics Computation | Calculate mAP, precision, recall, F1 and other detection metrics |
| error_analysis | Error Analysis | Deep dive into model failures, false positives, and false negatives |
| threshold_optimization | Threshold Optimization | Find optimal confidence thresholds for deployment |
| comparison | Comparison | Compare multiple models or experiments side by side |
| report_generation | Report Generation | Generate comprehensive evaluation reports with visualizations |
| deployment_readiness | Deployment Readiness | Assess if model meets quality thresholds for production |

**Key Commands**:
- `evaluate`, `analyze`, `diagnose`, `report`

---

## Deployment Agent (Shipper)

**Role**: Deployment Engineer + Edge Optimizer

**Capabilities**:
| ID | Name | Description |
|----|------|-------------|
| model_export | Model Export | Export models to ONNX, TensorRT, CoreML, TFLite, OpenVINO |
| optimization | Optimization | Quantize and optimize models for target hardware |
| cloud_deployment | Cloud Deployment | Deploy to Modal.com or vfrog cloud inference |
| edge_packaging | Edge Packaging | Create deployment packages for edge devices |
| inference_validation | Inference Validation | Validate exported models produce correct results |
| benchmark | Benchmark | Measure inference latency and throughput |

**Key Commands**:
- `export`, `deploy cloud`, `deploy edge`

---

## Routing Decision Matrix

| User Intent | Route To | Confidence |
|-------------|----------|------------|
| "I have images to process" | Data Agent | High |
| "Check my data quality" | Data Agent | High |
| "Train a model" | Training Agent | High |
| "Which architecture should I use?" | Training Agent | High |
| "How well does my model work?" | Evaluation Agent | High |
| "Why is my model making mistakes?" | Evaluation Agent | High |
| "Deploy to production" | Deployment Agent | High |
| "Export to ONNX" | Deployment Agent | High |
| "What should I do next?" | Router (self) | High |
| "Show me the status" | Router (self) | High |
