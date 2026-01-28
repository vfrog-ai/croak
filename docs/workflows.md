# CROAK Workflows

Workflows define sequences of agent actions that accomplish complex tasks. CROAK provides built-in workflows and supports custom workflow definitions.

## Built-in Workflows

### Full Pipeline (`full-pipeline`)

The complete ML pipeline from raw data to deployment:

```
Data Agent → Training Agent → Evaluation Agent → Deployment Agent
```

Steps:
1. `validate` - Validate dataset quality
2. `split` - Create train/val/test splits
3. `configure` - Generate training configuration
4. `train` - Train the model
5. `evaluate` - Evaluate on test set
6. `export` - Export to deployment format
7. `deploy` - Deploy to target

### Quick Train (`quick-train`)

Fast path for pre-prepared datasets:

```
Training Agent → Evaluation Agent
```

Steps:
1. `train` - Train with default configuration
2. `evaluate` - Quick evaluation

### Iterate (`iterate`)

For model improvement iterations:

```
Evaluation Agent → Training Agent → Evaluation Agent
```

Steps:
1. `analyze` - Analyze current model errors
2. `configure` - Adjust training based on analysis
3. `train` - Retrain model
4. `evaluate` - Evaluate improvements

## Workflow Execution

### Running a Workflow

```bash
# Run the full pipeline
croak workflow full-pipeline

# Run quick training
croak workflow quick-train

# Check workflow status
croak status
```

### Programmatic Execution

```python
from croak.workflows.executor import WorkflowExecutor

executor = WorkflowExecutor(project_dir)

# Load workflow
workflow = executor.load_workflow("full-pipeline")

# Get ready steps
ready_steps = executor.get_ready_steps(workflow, completed=[])

# Execute a step
for step in ready_steps:
    # Execute step logic...
    executor.complete_step(workflow.id, step.id, artifacts={...})

# Check status
status = executor.get_workflow_status("full-pipeline")
print(f"Progress: {status['progress_percent']}%")
```

## Custom Workflows

Create custom workflows in `.croak/workflows/`:

```yaml
# .croak/workflows/my-workflow.yaml
id: my-workflow
name: My Custom Workflow
description: A custom workflow for my use case

steps:
  - id: step1
    name: Validate Data
    agent: data-agent
    command: validate
    depends_on: []

  - id: step2
    name: Split Data
    agent: data-agent
    command: split
    depends_on: [step1]
    parameters:
      train_ratio: 0.9
      val_ratio: 0.1

  - id: step3
    name: Train Model
    agent: training-agent
    command: train
    depends_on: [step2]
    parameters:
      epochs: 50
      architecture: yolov8n
```

### Step Configuration

Each step supports:

| Field | Description | Required |
|-------|-------------|----------|
| `id` | Unique identifier | Yes |
| `name` | Human-readable name | Yes |
| `agent` | Agent to execute step | Yes |
| `command` | Command to run | Yes |
| `depends_on` | List of prerequisite step IDs | Yes |
| `parameters` | Command parameters | No |
| `timeout` | Timeout in seconds | No |
| `retry` | Number of retries on failure | No |

### Parallel Steps

Steps with no dependencies can run in parallel:

```yaml
steps:
  - id: export-onnx
    name: Export ONNX
    agent: deployment-agent
    command: export
    depends_on: [train]
    parameters:
      format: onnx

  - id: export-tflite
    name: Export TFLite
    agent: deployment-agent
    command: export
    depends_on: [train]  # Same dependency
    parameters:
      format: tflite

  - id: deploy
    name: Deploy
    agent: deployment-agent
    command: deploy
    depends_on: [export-onnx, export-tflite]  # Waits for both
```

## Workflow State

Workflow progress is tracked in `.croak/pipeline-state.yaml`:

```yaml
workflow_progress:
  full-pipeline:
    - validate
    - split
    - configure
    # training in progress...

workflow_artifacts:
  full-pipeline:
    validate:
      validation_result: passed
    split:
      data_yaml: /path/to/data.yaml
```

### Resuming Workflows

Workflows can be resumed after interruption:

```bash
# Check what was completed
croak status

# Resume from where it left off
croak workflow full-pipeline --resume
```

## Error Handling

### Step Failures

When a step fails:

1. The workflow pauses at that step
2. Error details are logged
3. Dependent steps are blocked

```bash
# View error details
croak status --verbose

# Retry failed step
croak workflow full-pipeline --retry-failed

# Skip failed step (if recoverable)
croak workflow full-pipeline --skip step-id
```

### Rollback

For critical failures:

```bash
# Reset workflow to beginning
croak reset --workflow full-pipeline

# Reset entire pipeline state
croak reset
```

## Workflow Hooks

Add custom logic at workflow events:

```yaml
# .croak/workflows/my-workflow.yaml
hooks:
  before_workflow:
    - script: ./scripts/setup.sh

  after_step:
    - step: train
      script: ./scripts/notify.sh

  on_error:
    - script: ./scripts/alert.sh

  after_workflow:
    - script: ./scripts/cleanup.sh
```

## Monitoring

### Progress Tracking

```python
executor = WorkflowExecutor(project_dir)
status = executor.get_workflow_status("full-pipeline")

print(f"Workflow: {status['workflow_id']}")
print(f"Progress: {status['progress_percent']:.1f}%")
print(f"Completed: {status['completed_steps']}/{status['total_steps']}")
print(f"Current step: {status.get('current_step', 'None')}")
```

### Notifications

Configure notifications in config:

```yaml
# .croak/config.yaml
notifications:
  slack:
    webhook: https://hooks.slack.com/...
    events: [workflow_complete, step_failed]

  email:
    to: team@example.com
    events: [workflow_complete]
```

## Best Practices

1. **Keep steps atomic**: Each step should do one thing well
2. **Use dependencies wisely**: Only add necessary dependencies
3. **Handle errors gracefully**: Plan for step failures
4. **Log everything**: Use verbose logging for debugging
5. **Test incrementally**: Test individual steps before full workflows

## See Also

- [Agents](agents.md) - Agent capabilities
- [API Reference](api-reference.md) - Programmatic usage
