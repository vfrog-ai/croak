# Data Preparation Checklist

## Pre-Flight Checks

- [ ] Python 3.10+ installed
- [ ] CROAK initialized (`croak init`)
- [ ] vfrog API key configured (`VFROG_API_KEY`)
- [ ] Image directory accessible

## Data Scan

- [ ] All images discovered
- [ ] Supported formats identified (JPG, PNG, WEBP)
- [ ] Image count meets minimum (100+)
- [ ] Existing annotations detected (if any)

## Data Validation

- [ ] All images readable (no corrupt files)
- [ ] Image sizes catalogued
- [ ] Duplicate images identified
- [ ] Annotation format validated (if existing)

## Annotation (vfrog)

- [ ] vfrog project created
- [ ] Images uploaded to vfrog
- [ ] All images annotated
- [ ] Annotations exported in YOLO format
- [ ] Class names consistent

## Class Balance

- [ ] All classes have 50+ instances (recommended)
- [ ] Class imbalance ratio < 10:1 (warning if exceeded)
- [ ] Minority classes identified

## Dataset Splits

- [ ] Train split created (default 80%)
- [ ] Validation split created (default 15%)
- [ ] Test split created (default 5%)
- [ ] Stratification applied (class proportions maintained)
- [ ] No data leakage between splits

## Export

- [ ] data.yaml generated
- [ ] Images copied to split directories
- [ ] Labels copied to split directories
- [ ] Directory structure validated

## Quality Report

- [ ] Statistics computed
- [ ] Quality issues documented
- [ ] Warnings listed
- [ ] Recommendations provided

## Handoff Ready

- [ ] All checks passed (or warnings acknowledged)
- [ ] Handoff artifact generated
- [ ] Ready for Training Agent
