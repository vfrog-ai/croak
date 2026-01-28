# Step 4: Setup Training Environment

## Execution Rules
- 🐸 DEFAULT to Modal.com for GPU provisioning
- ✅ ALWAYS check for local GPU first
- 💰 ALWAYS show cost estimate before cloud training

## Your Task
Set up GPU compute environment for training.

## Execution Sequence

### 1. Check Local GPU

```python
import subprocess

def check_local_gpu() -> dict:
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            gpus = []
            for line in lines:
                name, memory = line.split(',')
                gpus.append({
                    'name': name.strip(),
                    'memory_mb': int(memory.strip().split()[0])
                })
            return {'available': True, 'gpus': gpus}
    except:
        pass
    return {'available': False, 'gpus': []}
```

### 2. Present Options

```
🎯 Training Environment Setup

═══════════════════════════════════════════════════
LOCAL GPU STATUS
═══════════════════════════════════════════════════

{if local_gpu_available}
✅ Found local GPU(s):
   {gpu_name} ({memory_gb}GB VRAM)

You can train locally or use cloud GPU.
{else}
❌ No local GPU detected.
   Cloud GPU required for training.
{/if}

═══════════════════════════════════════════════════
RECOMMENDED: MODAL.COM
═══════════════════════════════════════════════════

Modal.com offers serverless GPU compute:
• Free $30 credits for new accounts
• Pay-per-second billing (no idle costs)
• No setup headaches
• GPU options: T4, A10G, A100

{if local_gpu_available}
═══════════════════════════════════════════════════
COMPARISON
═══════════════════════════════════════════════════

              Local           Modal (T4)      Modal (A10G)
──────────────────────────────────────────────────────────
Speed         {local_speed}   ~1.5x faster    ~2x faster
Cost          Free            ~$2-4           ~$4-8
Setup         None            5 min           5 min
Ties up PC    Yes             No              No

{/if}

Where do you want to train?
[1] Modal.com (recommended)
{if local_gpu_available}[2] Local GPU{/if}
[3] Other (Colab, RunPod, etc.)

Choice: ___
```

### 3. Modal.com Setup

If Modal selected:

```python
def setup_modal() -> bool:
    # Check if Modal is installed
    try:
        import modal
        print("✅ Modal package installed")
    except ImportError:
        print("Installing Modal...")
        subprocess.run(['pip', 'install', 'modal'], check=True)

    # Check authentication
    result = subprocess.run(['modal', 'token', 'show'], capture_output=True)
    if result.returncode != 0:
        print("Modal not authenticated. Opening browser...")
        subprocess.run(['modal', 'token', 'new'])

    return True
```

Modal setup flow:
```
🎯 Setting up Modal.com

Step 1: Install Modal CLI
  pip install modal ✅

Step 2: Authenticate
  Running: modal token new

  This will open your browser to authenticate.
  Log in with your Modal account (or create one - it's free).

  Waiting for authentication... ✅

Step 3: Verify credits
  Checking account status...

  ✅ Modal authenticated!
  Credits remaining: ${credits}

You're ready to train on Modal GPUs!
```

### 4. Local GPU Setup

If local selected:
```
🎯 Local GPU Training

Using: {gpu_name} ({memory_gb}GB)

Checking requirements:
  ✅ CUDA available
  ✅ PyTorch with CUDA support
  ✅ Sufficient VRAM for {architecture}

⚠️ Notes:
  • Training will use this machine
  • Other GPU tasks may be slower
  • Don't close the terminal during training

Ready to proceed with local training.
```

### 5. Generate Training Script

For Modal:
```python
modal_script = f'''
"""
CROAK Training Script for Modal.com
Experiment: {experiment_id}
Generated: {timestamp}
"""

import modal

app = modal.App("croak-{experiment_id}")

training_image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "ultralytics>=8.0.0",
    "torch>=2.0.0",
    "torchvision>=0.15.0",
    "mlflow>=2.0.0"
)

@app.function(
    gpu="T4",
    timeout=4 * 3600,  # 4 hours
    image=training_image,
    mounts=[
        modal.Mount.from_local_dir("./data/processed", remote_path="/data"),
        modal.Mount.from_local_file("{config_path}", remote_path="/config.yaml")
    ]
)
def train():
    from ultralytics import YOLO

    # Load model
    model = YOLO("{architecture}.pt")

    # Train
    results = model.train(
        data="/data/data.yaml",
        cfg="/config.yaml",
        project="/results",
        name="{experiment_id}"
    )

    return results

@app.local_entrypoint()
def main():
    result = train.remote()
    print(f"Training complete! Results: {{result}}")
'''

script_path = Path(f"training/scripts/train-{experiment_id}.py")
script_path.write_text(modal_script)
```

For local:
```python
local_script = f'''
"""
CROAK Local Training Script
Experiment: {experiment_id}
"""

from ultralytics import YOLO
import yaml

# Load config
with open("{config_path}") as f:
    config = yaml.safe_load(f)

# Load model
model = YOLO("{architecture}.pt")

# Train
results = model.train(**config)

print(f"Training complete!")
print(f"Best model: {{results.save_dir}}/weights/best.pt")
'''
```

### 6. Cost Estimate

```
🎯 Training Cost Estimate

Configuration:
  Architecture: {architecture}
  Dataset: {num_images} images
  Epochs: {epochs}
  Batch size: {batch_size}

Estimated training time: ~{hours} hours

{if modal}
Modal.com pricing:
  GPU       Rate/hr    Est. Cost
  ────────────────────────────────
  T4        $0.59      ~${cost_t4}
  A10G      $1.10      ~${cost_a10g}
  A100      $2.78      ~${cost_a100}

  Recommended: T4 (sufficient for this training)

Free credits: ${credits} remaining
{else if local}
Cost: Free (using local GPU)
{/if}

Note: Actual time may vary. Early stopping may reduce time.
```

### 7. Update Pipeline State

```yaml
training:
  environment:
    provider: "{modal|local|other}"
    gpu_type: "{gpu_type}"
    estimated_hours: {hours}
    estimated_cost: {cost}
  script_path: "{script_path}"
```

## Outputs

- `compute_provider`: Modal / local / other
- `gpu_config`: GPU type and configuration

## Completion

> "✅ Environment ready!
>
> Provider: {provider}
> GPU: {gpu_type}
> Estimated time: ~{hours} hours
> Estimated cost: ${cost}
>
> Training script: {script_path}
>
> Ready to start training?
>
> Run: `croak train` to begin"

WAIT for user before loading step-05-execute.md
