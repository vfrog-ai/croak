# Step 2: Recommend Architecture

## Execution Rules
- 🐸 ALWAYS provide rationale for recommendations
- ✅ ALWAYS consider dataset size, class count, and deployment target
- 📊 ALWAYS present alternatives with trade-offs

## Your Task
Analyze requirements and recommend the best model architecture.

## Execution Sequence

### 1. Gather Requirements

Ask user about deployment target:
> "Before I recommend an architecture, a quick question:
>
> **Where will this model run?**
>
> 1. **Cloud API** - Accuracy matters most, latency less critical
> 2. **Edge device** - Real-time speed required (Jetson, embedded)
> 3. **Desktop/server with GPU** - Good balance of both
> 4. **Not sure yet** - I'll recommend a balanced option
>
> Choose [1/2/3/4]: ___"

### 2. Analyze Dataset Characteristics

```python
def analyze_dataset(context: dict) -> dict:
    analysis = {
        'size_category': None,
        'complexity': None,
        'recommendations': []
    }

    total_images = context['dataset']['train_images']

    # Size category
    if total_images < 500:
        analysis['size_category'] = 'small'
        analysis['recommendations'].append(
            "Small dataset - use smaller model to avoid overfitting"
        )
    elif total_images < 2000:
        analysis['size_category'] = 'medium'
    else:
        analysis['size_category'] = 'large'
        analysis['recommendations'].append(
            "Large dataset - can support bigger models"
        )

    # Complexity
    num_classes = context['dataset']['num_classes']
    if num_classes <= 5:
        analysis['complexity'] = 'simple'
    elif num_classes <= 20:
        analysis['complexity'] = 'moderate'
    else:
        analysis['complexity'] = 'complex'
        analysis['recommendations'].append(
            "Many classes - consider medium or large model"
        )

    return analysis
```

### 3. Architecture Decision Matrix

```python
def recommend_architecture(
    deployment_target: str,
    dataset_size: str,
    num_classes: int
) -> dict:

    # Decision logic
    if deployment_target == 'edge':
        if dataset_size == 'small':
            arch = 'yolov8n'
            rationale = "Smallest model for edge, prevents overfitting on small data"
        else:
            arch = 'yolov8n'
            rationale = "Optimized for real-time edge inference"

    elif deployment_target == 'cloud':
        if dataset_size == 'large' and num_classes > 20:
            arch = 'yolov8m'
            rationale = "Large model for maximum accuracy with sufficient data"
        else:
            arch = 'yolov8s'
            rationale = "Good accuracy for cloud deployment"

    else:  # balanced / not sure
        arch = 'yolov8s'
        rationale = "Best balance of speed and accuracy for most use cases"

    return {
        'architecture': arch,
        'rationale': rationale,
        'alternatives': get_alternatives(arch)
    }
```

### 4. Present Recommendation

```
🎯 Architecture Recommendation

═══════════════════════════════════════════════════
YOUR DATASET
═══════════════════════════════════════════════════

Images: {total} ({size_category})
Classes: {num_classes} ({complexity})
Deployment: {target}

═══════════════════════════════════════════════════
RECOMMENDATION
═══════════════════════════════════════════════════

I recommend: **{architecture}**

Why:
• {rationale_1}
• {rationale_2}
• {rationale_3}

Specs:
  Parameters: {param_count}
  Expected training: ~{hours} hours
  Inference speed: ~{fps} FPS

═══════════════════════════════════════════════════
ALTERNATIVES
═══════════════════════════════════════════════════

{alt_1}:
  • Better for: {use_case}
  • Trade-off: {tradeoff}

{alt_2}:
  • Better for: {use_case}
  • Trade-off: {tradeoff}

═══════════════════════════════════════════════════
ARCHITECTURE COMPARISON
═══════════════════════════════════════════════════

Model       Params    Speed    Accuracy    Training
──────────────────────────────────────────────────
YOLOv8n     3.2M      ★★★★★    ★★★        ~2 hours
YOLOv8s     11.2M     ★★★★     ★★★★       ~4 hours
YOLOv8m     25.9M     ★★★      ★★★★★      ~8 hours
YOLOv11s    ~11M      ★★★★     ★★★★       ~4 hours
RT-DETR     ~32M      ★★★      ★★★★★      ~6 hours

(Speed: inference FPS, Accuracy: mAP potential)

═══════════════════════════════════════════════════

Use {architecture}? [Y/n or type alternative]
```

### 5. Handle User Choice

If user accepts:
> "Great! Using {architecture}.
>
> Next: Configure training parameters
>
> Run: `croak configure`"

If user specifies alternative:
```python
valid_architectures = ['yolov8n', 'yolov8s', 'yolov8m', 'yolov11s', 'rt-detr']
if user_choice in valid_architectures:
    architecture = user_choice
else:
    # Ask for valid choice
```

### 6. Update Pipeline State

```yaml
training:
  architecture: "{architecture}"
  architecture_rationale: "{rationale}"
  alternatives_considered: [...]
```

## Outputs

- `architecture`: Selected model architecture
- `rationale`: Why this architecture was chosen

## Completion

> "Architecture selected: {architecture}
>
> Next: Generate training configuration
>
> Run: `croak configure`"

WAIT for user before loading step-03-configure.md
