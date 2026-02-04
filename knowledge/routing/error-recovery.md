# Error Recovery Guide

This document describes how to recover from common pipeline errors and state issues.

## State File Issues

### Problem: "CROAK not initialized"
**Symptom**: Commands fail with "CROAK not initialized" message.

**Cause**: No `.croak/` directory found in current or parent directories.

**Recovery**:
```bash
croak init --name "my-project"
```

---

### Problem: "Pipeline state file missing or corrupted"
**Symptom**: Commands fail to read state, or state shows unexpected values.

**Cause**: `.croak/pipeline-state.yaml` deleted, corrupted, or has invalid YAML.

**Recovery**:
```bash
croak reset  # Creates fresh state file
```

**Note**: This preserves config but resets all progress tracking.

---

### Problem: "State version mismatch"
**Symptom**: Warning about state file version not matching CROAK version.

**Cause**: State file created with older CROAK version.

**Recovery**:
1. Try continuing - newer versions usually handle old state files
2. If issues persist: `croak reset`

---

### Problem: "State inconsistency detected"
**Symptom**: Current stage doesn't match completed stages.

**Cause**: Manual state file editing or interrupted operations.

**Recovery**:
```bash
croak reset  # Start fresh
# OR manually fix .croak/pipeline-state.yaml
```

---

## Data Issues

### Problem: "No images found"
**Symptom**: `croak scan` finds 0 images.

**Cause**:
- Wrong directory path
- Images in unsupported format
- Images in nested subdirectories

**Recovery**:
1. Verify path: `ls data/raw/`
2. Check formats (jpg, jpeg, png, bmp, webp supported)
3. Use recursive scan: `croak scan data/raw --recursive`

---

### Problem: "Validation failed - corrupt images"
**Symptom**: Validation reports corrupt or unreadable files.

**Recovery**:
1. Review list of corrupt files in validation report
2. Remove or replace corrupt files
3. Re-run: `croak validate`

---

### Problem: "Annotation coverage too low"
**Symptom**: Validation fails with < 95% annotation coverage.

**Recovery**:
1. Upload unannotated images to vfrog: `croak annotate`
2. OR remove unannotated images from dataset
3. Re-run: `croak validate`

---

### Problem: "Class imbalance severe"
**Symptom**: Warning about class ratio > 10:1.

**Recovery**:
1. Collect more samples of underrepresented classes
2. OR use class weights during training (Coach will configure)
3. OR merge similar classes if semantically appropriate

---

## Training Issues

### Problem: "Dataset not ready for training"
**Symptom**: `croak train` fails, says data not prepared.

**Recovery**:
```bash
croak prepare  # Run full data pipeline first
```

---

### Problem: "No GPU detected"
**Symptom**: Warning about missing GPU, training would be slow.

**Recovery**:
1. Use cloud GPU (recommended):
   ```bash
   croak train --cloud  # Uses Modal.com
   ```
2. OR proceed with CPU (very slow):
   ```bash
   croak train --local --cpu
   ```

---

### Problem: "Training interrupted"
**Symptom**: Training stopped unexpectedly (crash, timeout, user interrupt).

**Recovery**:
```bash
croak resume  # Finds latest checkpoint automatically
# OR specify checkpoint:
croak resume --checkpoint training/experiments/exp1/weights/last.pt
```

---

### Problem: "Out of memory (OOM)"
**Symptom**: CUDA out of memory error during training.

**Recovery**:
1. Reduce batch size:
   ```bash
   croak train --batch-size 8
   ```
2. Use smaller model:
   ```bash
   croak train --architecture yolov8n
   ```
3. Use cloud GPU with more VRAM:
   ```bash
   croak train --cloud --gpu A100
   ```

---

## Evaluation Issues

### Problem: "No model to evaluate"
**Symptom**: `croak evaluate` fails, no model found.

**Recovery**:
1. Check training completed: `croak status`
2. Specify model path explicitly:
   ```bash
   croak evaluate --model path/to/weights/best.pt
   ```

---

### Problem: "Metrics look wrong"
**Symptom**: mAP is 0 or unrealistically high/low.

**Cause**:
- Test set too small
- Class mismatch between model and test data
- Wrong confidence threshold

**Recovery**:
1. Check test set: `croak stats --split test`
2. Verify classes match
3. Try different threshold:
   ```bash
   croak evaluate --conf 0.1
   ```

---

## Deployment Issues

### Problem: "Export failed"
**Symptom**: Model export to target format fails.

**Cause**:
- Missing dependencies for format
- Model architecture incompatible with format
- Insufficient disk space

**Recovery**:
1. Check dependencies: `croak doctor`
2. Try different format: `croak export --format onnx`
3. Check disk space: `df -h`

---

### Problem: "Modal deployment failed"
**Symptom**: `croak deploy cloud` errors.

**Recovery**:
1. Check Modal auth:
   ```bash
   modal token show
   # If expired:
   modal setup
   ```
2. Check Modal dashboard for errors
3. Try manual deploy:
   ```bash
   modal deploy deployment/cloud/modal-app.py
   ```

---

## General Recovery Steps

### When All Else Fails

1. **Check status**:
   ```bash
   croak status
   croak doctor
   ```

2. **Review logs**:
   ```bash
   cat .croak/logs/latest.log
   ```

3. **Soft reset** (keeps config and data):
   ```bash
   croak reset
   ```

4. **Hard reset** (start completely fresh):
   ```bash
   rm -rf .croak/
   croak init --name "my-project"
   ```

5. **Get help**:
   - `croak help`
   - GitHub issues: https://github.com/vfrog-ai/croak/issues

---

## Prevention Tips

1. **Don't manually edit state files** - Use CLI commands
2. **Don't interrupt training** - Use `Ctrl+C` once, wait for checkpoint
3. **Run `croak doctor` periodically** - Catches issues early
4. **Keep backups of `.croak/`** - Especially before major operations
5. **Use `--dry-run` flags** - Preview destructive operations
