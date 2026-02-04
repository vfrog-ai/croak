# Model Deployment Checklist

## Pre-Deployment Checks

- [ ] Evaluation workflow complete
- [ ] deployment_ready == true
- [ ] Model weights accessible
- [ ] Recommended threshold available

## Target Selection

- [ ] Deployment target chosen (cloud/edge/both)
- [ ] Target requirements understood
- [ ] Infrastructure available

## Cloud Deployment (vfrog)

- [ ] vfrog API credentials verified
- [ ] Model uploaded
- [ ] Serving configuration set
- [ ] Staging deployment created
- [ ] Smoke tests passed on staging
- [ ] Production deployment created
- [ ] Endpoint URL documented
- [ ] API key secured

## Edge Deployment

- [ ] Target format selected (ONNX/TensorRT/CUDA)
- [ ] Optimization level selected (FP32/FP16/INT8)
- [ ] Model exported successfully
- [ ] Export validated with sample inference
- [ ] Inference script generated
- [ ] Requirements documented
- [ ] Benchmark results recorded

## Model Optimization

- [ ] Precision selection made
- [ ] Quantization applied (if INT8)
- [ ] Size reduction achieved
- [ ] Accuracy preservation verified

## Validation

- [ ] Smoke tests executed
- [ ] Inference working correctly
- [ ] Latency within target
- [ ] All classes detected
- [ ] Accuracy matches evaluation

## Documentation

- [ ] Endpoint/model path documented
- [ ] Usage examples provided
- [ ] API documentation (if cloud)
- [ ] Inference script documented (if edge)

## Rollback Plan

- [ ] Original model preserved
- [ ] Rollback procedure documented
- [ ] Previous version accessible

## Completion

- [ ] Deployment validated
- [ ] User notified of success
- [ ] Monitoring instructions provided
