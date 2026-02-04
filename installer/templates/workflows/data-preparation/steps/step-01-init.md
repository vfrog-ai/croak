# Step 1: Initialize Data Pipeline

## Execution Rules
- 🐸 ALWAYS check for existing CROAK configuration
- ✅ ALWAYS verify vfrog API key is available
- 📊 ALWAYS set up directory structure before proceeding

## Your Task
Initialize the data preparation pipeline and verify prerequisites.

## Execution Sequence

### 1. Check CROAK Initialization

```python
from pathlib import Path

croak_config = Path(".croak/config.yaml")
if not croak_config.exists():
    # Prompt user to run croak init
```

If not initialized:
> "CROAK isn't initialized in this directory yet. Let's set it up:
>
> ```
> croak init
> ```
>
> This creates the project structure and configuration files."

### 2. Verify vfrog Credentials

```python
import os
api_key = os.environ.get('VFROG_API_KEY')
```

If no API key:
> "You'll need a vfrog API key for annotation. Here's how to get one:
>
> 1. Sign up at https://vfrog.ai (free tier available)
> 2. Go to Settings → API
> 3. Generate a new API key
> 4. Set it in your environment:
>    ```
>    export VFROG_API_KEY=your_key_here
>    ```
>
> Type 'continue' when ready."

### 3. Get Data Directory

Ask user for image location:
> "Where are your images located?
>
> Default: `./data/raw`
>
> Enter path or press Enter for default: ___"

Validate path exists and is accessible.

### 4. Create Directory Structure

```python
directories = [
    "data/raw",
    "data/annotations",
    "data/processed/images/train",
    "data/processed/images/val",
    "data/processed/images/test",
    "data/processed/labels/train",
    "data/processed/labels/val",
    "data/processed/labels/test",
]
```

### 5. Update Pipeline State

```yaml
current_stage: "data_preparation"
stages_completed:
  - "data_init"
```

## Outputs

- `data_directory`: Path to image source
- `project_config`: Updated configuration

## Completion

✅ Prerequisites verified
✅ Directory structure created
✅ Ready for data scan

> "Setup complete! Let's scan your images.
>
> Next: `croak scan {data_directory}`"

WAIT for user before loading step-02-scan.md
