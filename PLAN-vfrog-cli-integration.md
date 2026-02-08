# Plan: Migrate vfrog Integration from API to CLI

## Problem Statement

The current vfrog integration in CROAK uses a custom HTTP API client (`VfrogClient` in
`src/croak/integrations/vfrog.py`) that directly calls `https://api.vfrog.ai/v1` endpoints
via `httpx`. This is the wrong approach because:

1. **Agents can't execute vfrog operations independently** -- they must go through the Python
   API client, which couples them to the internal integration code.
2. **The CLI commands are broken or stubbed** -- `croak annotate` prints a placeholder message;
   `croak deploy cloud` routes to Modal.com instead of vfrog (contradicting the agent YAML
   definitions).
3. **The `SecureRunner` command whitelist doesn't include `vfrog`** -- so no agent can safely
   execute vfrog CLI commands through the established command execution infrastructure.
4. **Duplicated logic** -- the Node.js installer (`installer/src/utils/vfrog-setup.js`) also
   reimplements the same API calls via `fetch`, creating two parallel API clients to maintain.
5. **The knowledge guide already references the official CLI** -- `knowledge/deployment/vfrog-guide.md`
   mentions `pip install vfrog` and `from vfrog import Client`, indicating an official CLI/SDK exists.

Each agent should have direct access to the `vfrog` CLI tool through `SecureRunner`, the same
way they already have access to `modal`, `yolo`, and other whitelisted commands.

---

## Current Architecture

```
Agent (Scout/Shipper)
  └─> Python import: croak.integrations.vfrog.VfrogClient
        └─> httpx HTTP calls to https://api.vfrog.ai/v1/*
```

### Files involved

| File | Role | Issue |
|------|------|-------|
| `src/croak/integrations/vfrog.py` | Custom HTTP client (275 lines) | Reimplements what vfrog CLI provides |
| `src/croak/cli.py:477-482` | `croak annotate` command | Stub -- prints message, does nothing |
| `src/croak/cli.py:981-1013` | `croak deploy cloud` command | Routes to Modal.com, not vfrog |
| `src/croak/core/commands.py:45-63` | `SecureRunner.ALLOWED_COMMANDS` | No `vfrog` entry |
| `agents/data/data.agent.yaml` | Scout agent definition | References `croak annotate` (broken) |
| `agents/deployment/deployment.agent.yaml` | Shipper agent definition | References `croak deploy cloud` (misrouted) |
| `installer/src/utils/vfrog-setup.js` | Node.js vfrog utilities | Duplicate API calls via fetch |
| `workflows/model-deployment/steps/` | Deployment workflow steps | Directory doesn't exist yet |
| `workflows/data-preparation/steps/step-04-annotate.md` | Annotation workflow step | Uses VfrogClient Python code |
| `knowledge/deployment/vfrog-guide.md` | vfrog integration guide | Already mentions CLI, but code uses API |

---

## Target Architecture

```
Agent (Scout/Shipper)
  └─> croak CLI command (croak annotate / croak deploy cloud)
        └─> VfrogCLI wrapper (static methods)
              └─> SecureRunner.run_vfrog()
                    └─> subprocess: vfrog <subcommand> --json
```

---

## Implementation Plan

### Phase 1: Foundation -- SecureRunner and CLI Wrapper

#### 1.1 Whitelist `vfrog` in SecureRunner

**File**: `src/croak/core/commands.py`

Add `vfrog` to the `ALLOWED_COMMANDS` dict (line 45), following the pattern established by
`modal`:

```python
ALLOWED_COMMANDS = {
    # ... existing entries ...
    # vfrog.ai CLI
    'vfrog': ['project', 'create', 'upload', 'export', 'deploy',
              'status', 'test', 'auth', '--version'],
}
```

Subcommand coverage mapping:

| vfrog CLI command | Replaces VfrogClient method |
|-------------------|-----------------------------|
| `vfrog project create` | `create_project()` |
| `vfrog upload` | `upload_images()` |
| `vfrog status` | `get_project_status()` |
| `vfrog export` | `export_annotations()` |
| `vfrog deploy create` | `create_deployment()` |
| `vfrog deploy staging` | `deploy_to_staging()` |
| `vfrog deploy production` | `deploy_to_production()` |
| `vfrog test` | `test_endpoint()` |
| `vfrog auth verify` | API key validation |

#### 1.2 Add `run_vfrog` method to SecureRunner

**File**: `src/croak/core/commands.py`

Add a convenience method modeled on the existing `run_modal` (line 243):

```python
@classmethod
def run_vfrog(
    cls,
    args: List[str],
    cwd: Optional[Path] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """Run vfrog CLI command securely."""
    cmd = ['vfrog'] + args
    try:
        result = cls.run(cmd, cwd=cwd, capture_output=True, timeout=timeout)
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.returncode != 0 else None,
        }
    except CommandExecutionError as e:
        return {'success': False, 'output': None, 'error': str(e)}
```

#### 1.3 Replace `VfrogClient` with `VfrogCLI`

**File**: `src/croak/integrations/vfrog.py`

Rewrite the file. Keep the Pydantic models (`VfrogProject`, `VfrogDeployment`) for typed
return values. Replace the `VfrogClient` class with a `VfrogCLI` class using static methods
that delegate to `SecureRunner.run_vfrog()`.

Key design decisions:
- All methods are `@staticmethod` -- the CLI reads `VFROG_API_KEY` from the environment,
  so no instance state is needed.
- Every method appends `--json` to get machine-parseable output.
- `upload_images` takes an `image_dir` path instead of a list of `Path` objects -- the CLI
  handles directory traversal.
- The `httpx` import is removed entirely.

```python
class VfrogCLI:
    """Wrapper around vfrog CLI tool."""

    @staticmethod
    def check_installed() -> bool:
        return SecureRunner.check_command_available('vfrog')

    @staticmethod
    def check_authenticated() -> bool:
        result = SecureRunner.run_vfrog(['auth', 'verify'])
        return result['success']

    @staticmethod
    def create_project(name, task_type='detection', classes=None) -> VfrogProject:
        args = ['project', 'create', '--name', name, '--task-type', task_type]
        if classes:
            args.extend(['--classes', ','.join(classes)])
        args.append('--json')
        result = SecureRunner.run_vfrog(args)
        # parse JSON output into VfrogProject ...

    @staticmethod
    def upload_images(project_id, image_dir, batch_size=50) -> dict:
        args = ['upload', '--project', project_id, '--dir', str(image_dir),
                '--batch-size', str(batch_size), '--json']
        result = SecureRunner.run_vfrog(args, timeout=600)
        # ...

    @staticmethod
    def export_annotations(project_id, format='yolo', output_dir=None) -> dict:
        args = ['export', '--project', project_id, '--format', format, '--json']
        if output_dir:
            args.extend(['--output', str(output_dir)])
        result = SecureRunner.run_vfrog(args)
        # ...

    @staticmethod
    def create_deployment(name, model_path, class_names) -> VfrogDeployment:
        args = ['deploy', 'create', '--name', name, '--model', str(model_path),
                '--classes', ','.join(class_names), '--json']
        result = SecureRunner.run_vfrog(args, timeout=600)
        # ...

    @staticmethod
    def deploy_to_staging(deployment_id) -> VfrogDeployment:
        # ...

    @staticmethod
    def deploy_to_production(deployment_id) -> VfrogDeployment:
        # ...

    @staticmethod
    def test_endpoint(endpoint_url, image_path) -> dict:
        # ...
```

#### 1.4 Update `__init__.py` exports

**File**: `src/croak/integrations/__init__.py`

Export `VfrogCLI` instead of (or in addition to) `VfrogClient`.

---

### Phase 2: CLI Commands -- Wire Up `croak annotate` and `croak deploy cloud`

#### 2.1 Implement `croak annotate`

**File**: `src/croak/cli.py` (lines 476-482)

Replace the stub with a full implementation:

1. Check vfrog CLI is installed (`VfrogCLI.check_installed()`)
2. Check authentication (`VfrogCLI.check_authenticated()`)
3. Load project config to get class names
4. Create a vfrog project (`VfrogCLI.create_project()`)
5. Upload images from `data/raw/` (`VfrogCLI.upload_images()`)
6. Print the project URL and annotation instructions
7. Update pipeline state with `vfrog_project_id`

Add Click options:
- `--project-id` -- resume with existing vfrog project
- `--classes` -- comma-separated class names (overrides config)
- `--input-dir` -- image directory (default: `data/raw`)
- `--output-dir` -- annotation output (default: `data/annotations`)
- `--export-format` -- annotation format (default: `yolo`)
- `--status` -- check annotation status only
- `--export-only` -- export annotations without creating project

#### 2.2 Re-route `croak deploy cloud` to vfrog

**File**: `src/croak/cli.py` (lines 981-1013)

Change the `cloud` subcommand from Modal.com to vfrog:

1. Check vfrog CLI is installed and authenticated
2. Create a deployment (`VfrogCLI.create_deployment()`)
3. Deploy to staging (`VfrogCLI.deploy_to_staging()`)
4. Run smoke test (`VfrogCLI.test_endpoint()`)
5. Optionally promote to production (`VfrogCLI.deploy_to_production()`)
6. Update pipeline state with deployment info

Preserve the Modal.com path by adding `croak deploy modal` as a new subcommand under the
`deploy` group, moving the current `cloud` implementation there.

Updated options for `croak deploy cloud`:
- Keep `--model` and `--name`
- Remove `--gpu` (not applicable for vfrog)
- Add `--staging-only` flag
- Add `--skip-test` flag
- Add `--promote` flag (promote existing staging deployment)

#### 2.3 Add `deploy_vfrog` to `ModelDeployer`

**File**: `src/croak/deployment/deployer.py`

Add a `deploy_vfrog()` method alongside the existing `deploy_modal()`:

```python
def deploy_vfrog(
    self,
    model_path: str,
    deployment_name: str,
    class_names: list[str],
    auto_promote: bool = False,
) -> Dict[str, Any]:
    """Deploy model to vfrog.ai platform via CLI."""
    # ...
```

---

### Phase 3: Agent Definitions and Workflow Steps

#### 3.1 Update Data Agent (Scout) YAML

**File**: `agents/data/data.agent.yaml`

- Update `vfrog_annotation` capability description (line 57) to mention CLI execution
- Add a guardrail check for vfrog CLI installation alongside API key check

#### 3.2 Update Deployment Agent (Shipper) YAML

**File**: `agents/deployment/deployment.agent.yaml`

- Update `cloud_deployment` capability description (line 52) to mention CLI
- Update `vfrog_credentials` guardrail (lines 237-243) to check CLI installation:
  ```yaml
  condition: "vfrog CLI is installed and VFROG_API_KEY environment variable is set"
  error_message: "vfrog CLI not installed or API key not set. Install: pip install vfrog. Set: export VFROG_API_KEY=..."
  ```

#### 3.3 Create deployment workflow step files

**Directory**: `workflows/model-deployment/steps/` (does not exist yet)

Referenced by `workflows/model-deployment/workflow.yaml` but the files are missing. Create:

| File | Purpose |
|------|---------|
| `step-01-init.md` | Verify evaluation handoff, determine deployment target |
| `step-02-optimize.md` | FP16/INT8 quantization, benchmark |
| `step-03-export.md` | Export model, validate with sample inference |
| `step-04a-deploy-cloud.md` | **vfrog CLI deployment workflow** (the key file) |
| `step-04b-deploy-edge.md` | Edge packaging, inference script generation |
| `step-05-validate.md` | Smoke test, latency check, class verification |

The `step-04a-deploy-cloud.md` file is the most critical. It should document the vfrog CLI
commands that agents execute:

```bash
vfrog --version                                    # verify installed
vfrog auth verify                                  # verify credentials
vfrog deploy create --name <name> --model <path> --classes <list> --json
vfrog deploy staging --id <deployment_id> --json
vfrog test --endpoint <url> --image <path> --json
vfrog deploy production --id <deployment_id> --json
```

#### 3.4 Update annotation workflow step

**File**: `workflows/data-preparation/steps/step-04-annotate.md`

Replace all `VfrogClient` Python code snippets with `VfrogCLI` equivalents:

```python
# Before (API-based):
from croak.integrations.vfrog import VfrogClient
client = VfrogClient(api_key=api_key)
project = client.create_project(name, task_type="detection", classes=classes)

# After (CLI-based):
from croak.integrations.vfrog import VfrogCLI
project = VfrogCLI.create_project(name, task_type="detection", classes=classes)
```

---

### Phase 4: Knowledge and Installer Updates

#### 4.1 Update vfrog knowledge guide

**File**: `knowledge/deployment/vfrog-guide.md`

- Add a "CLI Usage" section showing direct `vfrog` CLI commands
- Update Python examples to use `VfrogCLI` wrapper
- Add a "CROAK Integration" section explaining how `croak annotate` and `croak deploy cloud`
  wrap the CLI
- Mark direct API/curl sections as "advanced"

#### 4.2 Update installer vfrog setup

**File**: `installer/src/utils/vfrog-setup.js`

Replace `fetch()` API calls with CLI invocations (via `child_process.execSync` or `execa`):

| Current function | Current approach | New approach |
|-----------------|-----------------|--------------|
| `validateVfrogKey()` | `fetch('https://api.vfrog.ai/v1/auth/verify')` | `vfrog auth verify` |
| `createVfrogProject()` | `fetch('https://api.vfrog.ai/v1/projects')` | `vfrog project create --json` |
| `getVfrogProjectStatus()` | `fetch('https://api.vfrog.ai/v1/projects/{id}')` | `vfrog status --project <id> --json` |
| `uploadToVfrog()` | Placeholder | `vfrog upload --project <id> --dir <path> --json` |
| `downloadFromVfrog()` | Placeholder | `vfrog export --project <id> --format <fmt> --json` |

Add new `checkVfrogCLI()` function: executes `vfrog --version`.

#### 4.3 Update installer doctor command

**File**: `installer/src/commands/doctor.js`

Add vfrog CLI check to the integrations section (alongside Modal check).

#### 4.4 Update installer init command

**File**: `installer/src/commands/init.js`

Enhance vfrog check (line 138) to verify both CLI installation and API key.

---

### Phase 5: Configuration, Dependencies, and Tests

#### 5.1 Update `pyproject.toml`

**File**: `pyproject.toml`

- Add `vfrog` optional dependency: `vfrog = ["vfrog>=1.0.0"]`
- Verify whether `httpx` is used by any other module besides `VfrogClient`. If not, move it
  from core `dependencies` to an optional group.
- Update `all` extras to include `vfrog`

#### 5.2 Update `CroakConfig`

**File**: `src/croak/core/config.py`

Add CLI path field to `VfrogConfig`:

```python
class VfrogConfig(BaseModel):
    api_key_env: str = "VFROG_API_KEY"
    project_id: Optional[str] = None
    cli_path: Optional[str] = None  # custom vfrog CLI path if not on PATH
```

#### 5.3 Add security tests for vfrog whitelist

**File**: `tests/test_security.py`

Add test cases:
- `test_vfrog_command_allowed` -- verify whitelisted subcommands pass
- `test_vfrog_dangerous_subcommand_blocked` -- verify non-whitelisted subcommands are blocked
- `test_run_vfrog_returns_structured_result` -- verify output dict structure

#### 5.4 Add VfrogCLI integration tests

New test file or extension of existing tests. Mock `SecureRunner.run_vfrog()` to test:
- JSON output parsing
- Error handling for missing CLI
- Error handling for failed commands
- Correct argument construction for each method

---

### Phase 6: Deprecation and Cleanup

#### 6.1 Deprecate `VfrogClient`

During a transition period, keep `VfrogClient` in `src/croak/integrations/vfrog.py` with a
`DeprecationWarning`. Remove after one release cycle.

#### 6.2 Remove `httpx` core dependency

After confirming no other module uses `httpx` directly, remove it from core dependencies in
`pyproject.toml`.

---

## Sequencing and Dependencies

```
Phase 1 (Foundation)        Phase 2 (CLI Commands)        Phase 3 (Agents/Workflows)
  1.1 SecureRunner ────────> 2.1 croak annotate ─────────> 3.1 Data Agent YAML
  1.2 run_vfrog method       2.2 croak deploy cloud        3.2 Deployment Agent YAML
  1.3 VfrogCLI wrapper ───> 2.3 ModelDeployer ───────────> 3.3 Deployment step files
  1.4 __init__.py                                           3.4 Annotation step file

Phase 4 (Knowledge/Installer)   Phase 5 (Config/Tests)     Phase 6 (Cleanup)
  4.1 vfrog-guide.md             5.1 pyproject.toml          6.1 Deprecate VfrogClient
  4.2 vfrog-setup.js             5.2 CroakConfig             6.2 Remove httpx dep
  4.3 doctor.js                  5.3 Security tests
  4.4 init.js                    5.4 VfrogCLI tests
```

- Phases 1 → 2 are strictly sequential (Phase 2 depends on Phase 1)
- Phases 3, 4, 5 can proceed in parallel once Phase 2 is complete
- Phase 6 comes last, after a release cycle

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| vfrog CLI has different subcommand names than assumed | High | Design `VfrogCLI` with a mapping layer so subcommand names can be adjusted in one place |
| vfrog CLI doesn't support `--json` output | Medium | Build a parser that handles both JSON and text output, with JSON preferred |
| Breaking change for users importing `VfrogClient` | Medium | Keep deprecated alias during transition (Phase 6.1) |
| `croak deploy cloud` users who rely on Modal | Medium | Preserve Modal path as `croak deploy modal` subcommand |
| `httpx` used by other modules (not just VfrogClient) | Low | Grep codebase before removing; keep as optional dep if needed |

---

## Files Changed Summary

### Modified (12 files)

| File | Change |
|------|--------|
| `src/croak/core/commands.py` | Add `vfrog` to whitelist, add `run_vfrog()` method |
| `src/croak/integrations/vfrog.py` | Replace `VfrogClient` with `VfrogCLI` |
| `src/croak/integrations/__init__.py` | Update exports |
| `src/croak/cli.py` | Implement `croak annotate`, reroute `croak deploy cloud` |
| `src/croak/deployment/deployer.py` | Add `deploy_vfrog()` method |
| `src/croak/core/config.py` | Add `cli_path` to `VfrogConfig` |
| `agents/data/data.agent.yaml` | Update capability description and guardrails |
| `agents/deployment/deployment.agent.yaml` | Update guardrails for CLI check |
| `knowledge/deployment/vfrog-guide.md` | Add CLI sections, update Python examples |
| `installer/src/utils/vfrog-setup.js` | Replace fetch calls with CLI invocations |
| `installer/src/commands/init.js` | Check CLI installation during init |
| `pyproject.toml` | Add `vfrog` optional dependency |
| `workflows/data-preparation/steps/step-04-annotate.md` | Replace VfrogClient with VfrogCLI |

### Created (6 files)

| File | Purpose |
|------|---------|
| `workflows/model-deployment/steps/step-01-init.md` | Deployment init step |
| `workflows/model-deployment/steps/step-02-optimize.md` | Model optimization step |
| `workflows/model-deployment/steps/step-03-export.md` | Model export step |
| `workflows/model-deployment/steps/step-04a-deploy-cloud.md` | vfrog cloud deployment step |
| `workflows/model-deployment/steps/step-04b-deploy-edge.md` | Edge deployment step |
| `workflows/model-deployment/steps/step-05-validate.md` | Deployment validation step |
