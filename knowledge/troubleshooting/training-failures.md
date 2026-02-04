# Training Failures and Solutions

This guide covers common training issues, their symptoms, causes, and solutions.

## Memory Issues

### CUDA Out of Memory (OOM)

**Symptoms**:
```
RuntimeError: CUDA out of memory. Tried to allocate X MiB
```

**Causes**:
- Batch size too large
- Model too large for GPU
- Image size too large
- Memory leak from previous run

**Solutions**:

1. **Reduce batch size** (most common fix):
   ```bash
   croak train --batch-size 8  # Default is 16
   ```

2. **Use smaller model**:
   ```bash
   croak train --architecture yolov8n  # nano instead of small
   ```

3. **Reduce image size**:
   ```bash
   croak train --imgsz 480  # Default is 640
   ```

4. **Clear GPU memory**:
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

5. **Use gradient accumulation** (simulate larger batch):
   ```yaml
   # In training config
   accumulate: 4  # Effective batch = batch_size * accumulate
   ```

6. **Enable mixed precision** (FP16):
   ```bash
   croak train --half
   ```

**GPU Memory Guide**:
| GPU VRAM | Max Batch (YOLOv8s, 640) |
|----------|--------------------------|
| 8GB      | 8-12                     |
| 12GB     | 16-24                    |
| 24GB     | 32-48                    |
| 40GB+    | 64+                      |

---

### CPU Memory Exhaustion

**Symptoms**:
- System becomes unresponsive
- Process killed by OS
- "Killed" or SIGKILL in logs

**Causes**:
- Too many data loader workers
- Caching entire dataset in RAM
- Memory leak

**Solutions**:
1. Reduce workers: `--workers 2`
2. Disable caching: `--cache false`
3. Monitor with `htop` during training

---

## Training Instability

### Loss Explodes (NaN/Inf)

**Symptoms**:
```
Loss: nan or inf
Training stops or produces garbage
```

**Causes**:
- Learning rate too high
- Bad data (corrupt images, invalid annotations)
- Numerical instability

**Solutions**:

1. **Lower learning rate**:
   ```bash
   croak train --lr0 0.001  # Default is 0.01
   ```

2. **Check data quality**:
   ```bash
   croak validate --strict
   ```

3. **Use warmup epochs**:
   ```yaml
   warmup_epochs: 5
   warmup_momentum: 0.8
   ```

4. **Gradient clipping**:
   ```yaml
   max_grad_norm: 10.0
   ```

---

### Loss Doesn't Decrease

**Symptoms**:
- Loss stays flat for many epochs
- Metrics don't improve
- Model outputs same predictions for all inputs

**Causes**:
- Learning rate too low
- Model capacity insufficient
- Data problem (all same class, bad labels)
- Bug in data loading

**Solutions**:

1. **Increase learning rate**:
   ```bash
   croak train --lr0 0.02
   ```

2. **Use larger model**:
   ```bash
   croak train --architecture yolov8m
   ```

3. **Check data variety**:
   ```bash
   croak stats
   croak visualize --samples 50
   ```

4. **Verify data loading**:
   - Check augmentations aren't too aggressive
   - Ensure labels match images

---

### Validation Loss Increasing (Overfitting)

**Symptoms**:
- Training loss decreases
- Validation loss increases after initial decrease
- Gap between train and val metrics grows

**Causes**:
- Dataset too small
- Model too large
- Training too long
- Insufficient augmentation

**Solutions**:

1. **Early stopping**:
   ```yaml
   patience: 20  # Stop if no improvement for 20 epochs
   ```

2. **Stronger augmentation**:
   ```yaml
   augment: True
   hsv_h: 0.015
   hsv_s: 0.7
   hsv_v: 0.4
   degrees: 10
   translate: 0.1
   scale: 0.5
   fliplr: 0.5
   mosaic: 1.0
   ```

3. **Regularization**:
   ```yaml
   dropout: 0.1
   weight_decay: 0.0005
   ```

4. **Use smaller model or more data**

---

## Environment Issues

### CUDA Version Mismatch

**Symptoms**:
```
CUDA error: no kernel image is available for execution
RuntimeError: CUDA driver version is insufficient
```

**Solutions**:
1. Check versions:
   ```bash
   nvidia-smi
   python -c "import torch; print(torch.version.cuda)"
   ```
2. Install matching PyTorch:
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cu118
   ```

---

### GPU Not Detected

**Symptoms**:
```
CUDA available: False
Training falls back to CPU
```

**Solutions**:
1. Check NVIDIA driver:
   ```bash
   nvidia-smi
   ```
2. Check PyTorch CUDA:
   ```python
   import torch
   print(torch.cuda.is_available())
   print(torch.cuda.device_count())
   ```
3. Reinstall CUDA-enabled PyTorch
4. Use cloud GPU:
   ```bash
   croak train --cloud
   ```

---

### Multi-GPU Issues

**Symptoms**:
- Only one GPU used
- Hanging during distributed init
- NCCL errors

**Solutions**:
1. Specify device:
   ```bash
   croak train --device 0,1  # Use GPU 0 and 1
   ```
2. Check NCCL:
   ```bash
   export NCCL_DEBUG=INFO
   ```
3. Use single GPU if issues persist

---

## Checkpoint Issues

### Can't Resume Training

**Symptoms**:
```
FileNotFoundError: Checkpoint not found
State dict mismatch
```

**Causes**:
- Checkpoint deleted or moved
- Model architecture changed
- Different YOLO version

**Solutions**:
1. Find checkpoint:
   ```bash
   find training/experiments -name "*.pt"
   ```
2. Specify correct path:
   ```bash
   croak resume --checkpoint path/to/last.pt
   ```
3. Start fresh if architecture changed

---

### Checkpoint Corrupted

**Symptoms**:
```
RuntimeError: PytorchStreamReader failed
pickle.UnpicklingError
```

**Causes**:
- Training interrupted during save
- Disk full during save
- File system corruption

**Solutions**:
1. Use earlier checkpoint (epoch_N.pt)
2. Use `last.pt` if `best.pt` corrupted
3. Start fresh training

---

## Performance Issues

### Training Too Slow

**Symptoms**:
- GPU utilization < 80%
- Long gaps between batches
- ETA much longer than expected

**Causes**:
- Data loading bottleneck
- Small batch size
- Slow storage

**Solutions**:

1. **Increase workers**:
   ```bash
   croak train --workers 8
   ```

2. **Enable caching** (if RAM available):
   ```yaml
   cache: ram  # or 'disk'
   ```

3. **Use SSD storage**

4. **Increase batch size** (if GPU allows)

5. **Pre-process images**:
   - Resize to training size
   - Convert to efficient format

---

### Metrics Not Logged

**Symptoms**:
- MLflow/W&B not receiving data
- Empty experiment dashboard
- Metrics only in console

**Solutions**:
1. Check tracker config:
   ```yaml
   project: my-project
   name: experiment-1
   ```
2. Verify API keys:
   ```bash
   wandb login
   mlflow ui
   ```
3. Check network connectivity

---

## Diagnostic Commands

```bash
# Check GPU status
nvidia-smi -l 1

# Monitor training
tail -f training/experiments/latest/train.log

# Check system resources
htop

# Verify CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Test data loading
croak validate --benchmark
```

## Quick Reference

| Issue | First Thing to Try |
|-------|-------------------|
| OOM | Reduce batch size by half |
| NaN loss | Lower learning rate to 0.001 |
| No improvement | Check data with `croak validate` |
| Overfitting | Enable early stopping, more augmentation |
| Slow training | Increase workers, enable caching |
| Can't resume | Find checkpoint with `find` |
