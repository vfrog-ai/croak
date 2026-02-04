# Model Evaluation Checklist

## Pre-Evaluation Checks

- [ ] Training workflow complete
- [ ] Model artifact available
- [ ] Best weights file exists
- [ ] Test dataset available (separate from train/val)

## Metrics Computation

- [ ] Evaluation run on TEST set (not validation)
- [ ] mAP@50 computed
- [ ] mAP@50-95 computed
- [ ] Precision computed
- [ ] Recall computed
- [ ] F1 score computed
- [ ] Per-class AP computed

## Slice Analysis

- [ ] Performance by class analyzed
- [ ] Performance by object size (small/medium/large)
- [ ] Best/worst performing classes identified
- [ ] Size-related issues flagged

## Error Analysis

- [ ] False positives identified
- [ ] False negatives identified
- [ ] Misclassifications analyzed
- [ ] Error patterns documented

## Threshold Analysis

- [ ] Precision-recall curve generated
- [ ] Multiple thresholds tested
- [ ] Optimal threshold recommended
- [ ] Threshold rationale documented

## Visualizations

- [ ] Confusion matrix generated
- [ ] PR curves generated
- [ ] Sample predictions (good and bad)
- [ ] Class distribution visualization

## Diagnosis (if issues found)

- [ ] Root cause analysis performed
- [ ] Improvement recommendations made
- [ ] Priority actions identified

## Report Generation

- [ ] Comprehensive report created
- [ ] Metrics contextualized
- [ ] Actionable insights provided
- [ ] Deployment readiness assessed

## Deployment Recommendation

- [ ] Deployment ready: YES / NO / WITH CAVEATS
- [ ] Recommended threshold documented
- [ ] Warnings listed
- [ ] Improvement suggestions provided

## Handoff Ready

- [ ] All artifacts present
- [ ] Handoff artifact generated
- [ ] Ready for Deployment Agent
