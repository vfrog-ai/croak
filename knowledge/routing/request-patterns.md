# Request Patterns for Agent Routing

This document defines keyword patterns and intent signals for routing user requests to the appropriate specialist agent.

## Data Agent (Scout) Patterns

Route to Data Agent when the request involves:

### Keywords
- `scan`, `discover`, `find images`, `list images`
- `validate`, `check`, `quality`, `verify data`
- `annotate`, `label`, `vfrog`, `annotation`
- `split`, `partition`, `train test split`
- `convert`, `format`, `coco`, `yolo`, `voc`
- `statistics`, `stats`, `data info`
- `prepare`, `data pipeline`

### Intent Signals
- User mentions image files, directories, or datasets
- Questions about data quality or annotation coverage
- Requests involving annotation formats
- Concerns about class balance or data distribution

## Training Agent (Coach) Patterns

Route to Training Agent when the request involves:

### Keywords
- `train`, `training`, `start training`
- `model`, `architecture`, `yolo`, `detr`
- `recommend`, `suggest model`, `which model`
- `configure`, `config`, `hyperparameters`
- `estimate`, `cost`, `time`, `how long`
- `resume`, `checkpoint`, `continue training`
- `gpu`, `modal`, `cloud training`
- `experiment`, `compare runs`

### Intent Signals
- User wants to train a model
- Questions about model selection or architecture
- Concerns about training time or cost
- GPU or compute-related queries
- Experiment tracking questions

## Evaluation Agent (Judge) Patterns

Route to Evaluation Agent when the request involves:

### Keywords
- `evaluate`, `evaluation`, `test model`
- `metrics`, `mAP`, `precision`, `recall`, `F1`
- `analyze`, `errors`, `failures`, `mistakes`
- `diagnose`, `why isn't it working`, `debug model`
- `report`, `evaluation report`
- `performance`, `accuracy`, `how good`
- `threshold`, `confidence`

### Intent Signals
- User wants to assess model performance
- Questions about specific metrics
- Debugging model behavior
- Understanding model failures
- Comparing model versions

## Deployment Agent (Shipper) Patterns

Route to Deployment Agent when the request involves:

### Keywords
- `deploy`, `deployment`, `ship`, `release`
- `export`, `onnx`, `tensorrt`, `coreml`, `tflite`
- `cloud`, `edge`, `production`
- `optimize`, `quantize`, `compress`
- `inference`, `serve`, `api`
- `benchmark`, `latency`, `throughput`

### Intent Signals
- User wants to use the model in production
- Questions about model formats
- Edge device deployment
- Performance optimization for inference
- API or service deployment

## Ambiguous Requests

When a request could go to multiple agents, use these tiebreakers:

1. **Check pipeline state first** - Route to the agent for the current stage
2. **Earlier stage wins** - If between data and training, choose data
3. **Ask one clarifying question** - "Are you asking about X or Y?"
4. **Default by stage**:
   - No data prepared → Data Agent
   - Data ready, no model → Training Agent
   - Model trained → Evaluation Agent
   - Model evaluated → Deployment Agent

## Router-Only Requests

Handle these directly without routing:

- `status`, `state`, `where am i`
- `help`, `commands`, `what can you do`
- `next`, `what should I do`
- `history`, `what did I do`
- `init`, `initialize`, `setup`
- `reset`, `start over`
