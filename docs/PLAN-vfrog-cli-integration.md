# Plan: Integrate vfrog CLI with CROAK Agents

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
5. **The knowledge guide is inaccurate** -- `knowledge/deployment/vfrog-guide.md` references
   `pip install vfrog` and `from vfrog import Client`, but the real vfrog CLI is a **Go binary**
   downloaded from GitHub releases (not a Python package).

Each agent should have direct access to the `vfrog` CLI tool through `SecureRunner`, the same
way they already have access to `modal`, `yolo`, and other whitelisted commands.

### Deployment Scope

This plan covers three deployment targets:
- **vfrog** -- Cloud deployment via vfrog platform (annotation + training + inference)
- **Modal** -- Serverless GPU training and inference via Modal.com
- **Edge** -- Local/device export (ONNX, TensorRT, CoreML, etc.)

AWS, GCP, and Azure are out of scope for this phase.

---

## Real vfrog CLI Reference

The vfrog CLI is a **Go binary** (not a Python package). It was audited from the actual source
at `vfrog-ai/vfrog-cli`. Here is the complete command surface:

### Installation

```bash
# macOS (Apple Silicon)
curl -L https://github.com/vfrog-ai/vfrog-cli/releases/latest/download/vfrog-darwin-arm64 -o vfrog
chmod +x vfrog && sudo mv vfrog /usr/local/bin/

# macOS (Intel)
curl -L https://github.com/vfrog-ai/vfrog-cli/releases/latest/download/vfrog-darwin-amd64 -o vfrog
chmod +x vfrog && sudo mv vfrog /usr/local/bin/

# Linux (AMD64)
curl -L https://github.com/vfrog-ai/vfrog-cli/releases/latest/download/vfrog-linux-amd64 -o vfrog
chmod +x vfrog && sudo mv vfrog /usr/local/bin/
```

### Authentication

```bash
vfrog login                                       # Interactive (prompts email + password)
vfrog login --email user@example.com --password x  # Non-interactive (for CI/CD)
```

Auth is **email/password via Supabase**, NOT API-key based for CLI auth.
Tokens stored in `~/.vfrog/config-<environment>.json`.
`VFROG_API_KEY` is only used for the `inference` command.

### Context Hierarchy (must be set in order)

```bash
vfrog config set organisation --organisation_id <uuid>   # Step 1: required for all commands
vfrog config set project --project_id <uuid>             # Step 2: required for most commands
vfrog config set object --object_id <uuid>               # Step 3: required for iteration commands
vfrog config show                                         # Show current config + auth status
```

When `organisation_id` changes, `project_id` is automatically cleared.

### Complete Command Map

| Command | Subcommands | Purpose | Agent |
|---------|-------------|---------|-------|
| `vfrog version` | -- | Print version and environment | All |
| `vfrog login` | -- | Authenticate (email/password) | All |
| `vfrog config` | `show`, `set organisation`, `set project`, `set object` | Manage CLI context | Router |
| `vfrog organisations` | `list` | List user's organisations | Router |
| `vfrog projects` | `list`, `create <name>` | Manage projects | Scout, Router |
| `vfrog dataset_images` | `upload <urls...>`, `list`, `delete` | Manage dataset images (URL upload only) | Scout |
| `vfrog objects` | `create <url>`, `list`, `delete` | Manage product images (what to detect) | Scout |
| `vfrog iterations` | `list`, `create`, `delete`, `ssat`, `halo`, `next`, `restart` | SSAT annotation loop | Scout, Coach |
| `vfrog iteration` | `train` | Train model on iteration data | Coach |
| `vfrog inference` | -- | Run inference on trained model | Shipper, Judge |

**All commands support `--json` flag** for machine-readable output.

### Key Limitations (v0.1)

- **URL-only uploads**: `dataset_images upload` and `objects create` accept URLs, not local files
- **No annotation export command**: There is no `vfrog export` -- annotations are managed via
  the SSAT/HALO workflow on-platform
- **No deploy/staging/production commands**: Deployment is implicit -- once a model is trained
  via `vfrog iteration train`, it's available via `vfrog inference`
- **No `vfrog auth verify`**: Use `vfrog config show --json` and check `authenticated` field

### vfrog's Workflow Model (SSAT)

vfrog uses an **iterative Semi-Supervised Active Training (SSAT)** model, fundamentally different
from traditional annotate-export-train pipelines:

```
1. Create project → Upload dataset images (URLs) → Create objects (product images)
2. Create iteration #1 for an object
3. Run SSAT (auto-annotation using cutout matching for iteration 1)
4. Review/correct in HALO (Human Assisted Labelling of Objects) web UI
5. Train model on iteration #1
6. Create iteration #2 (inherits model from #1)
7. Run SSAT (now uses trained model for inference-based annotation)
8. Review in HALO → Train → Repeat to improve
9. Run inference against trained model
```

This means:
- **Annotation and training are interleaved**, not sequential
- **No separate annotation export step** -- the platform handles it internally
- **Each iteration produces a better model** through the SSAT loop
- **"Objects" are product images** (the reference for what to detect), not detection classes

---

## Current Architecture

```
Agent (Scout/Shipper)
  └─> Python import: croak.integrations.vfrog.VfrogClient
        └─> httpx HTTP calls to https://api.vfrog.ai/v1/*
```

### Files Involved

| File | Role | Issue |
|------|------|-------|
| `src/croak/integrations/vfrog.py` | Custom HTTP client (275 lines) | Reimplements what vfrog CLI provides; wrong API model |
| `src/croak/cli.py:477-482` | `croak annotate` command | Stub -- prints message, does nothing |
| `src/croak/cli.py:981-1013` | `croak deploy cloud` command | Routes to Modal.com, not vfrog |
| `src/croak/core/commands.py:45-63` | `SecureRunner.ALLOWED_COMMANDS` | No `vfrog` entry |
| `agents/data/data.agent.yaml` | Scout agent definition | References `croak annotate` (broken); doesn't know real vfrog commands |
| `agents/training/training.agent.yaml` | Coach agent definition | No vfrog training path; only knows local/Modal |
| `agents/evaluation/evaluation.agent.yaml` | Judge agent definition | No vfrog inference for evaluation |
| `agents/deployment/deployment.agent.yaml` | Shipper agent definition | References `croak deploy cloud` (misrouted to Modal) |
| `agents/router/router.agent.yaml` | Dispatcher agent definition | No awareness of vfrog context setup |
| `installer/src/utils/vfrog-setup.js` | Node.js vfrog utilities | Duplicate API calls via fetch; wrong auth model |
| `workflows/model-deployment/steps/` | Deployment workflow steps | Directory doesn't exist yet |
| `workflows/data-preparation/steps/step-04-annotate.md` | Annotation workflow step | Uses VfrogClient Python code; wrong workflow model |
| `knowledge/deployment/vfrog-guide.md` | vfrog integration guide | References `pip install vfrog` (wrong); uses Python SDK API |

---

## Target Architecture

```
Agent (any agent)
  └─> croak CLI command (croak vfrog setup / croak annotate / croak train --provider vfrog / etc.)
        └─> VfrogCLI wrapper (static methods)
              └─> SecureRunner.run_vfrog()
                    └─> subprocess: vfrog <subcommand> --json
```

### Deployment Target Matrix

| Target | Training | Deployment / Inference | CLI Commands |
|--------|----------|----------------------|--------------|
| **vfrog** | `vfrog iteration train` | `vfrog inference` | vfrog CLI |
| **Modal** | `modal run train.py` | `modal deploy app.py` | modal CLI |
| **Edge** | Local (`yolo train`) | Export (ONNX/TRT/CoreML) | yolo CLI |

### CLI Subcommand Structure (target)

```
croak deploy
  ├── vfrog    # Deploy/test on vfrog (inference endpoint)
  ├── modal    # Deploy on Modal.com (current `cloud` behavior, relocated)
  └── edge     # Export for edge devices (existing)
```

---

## Implementation Plan

### Phase 1: Foundation -- SecureRunner and CLI Wrapper

#### 1.1 Whitelist `vfrog` in SecureRunner

**File**: `src/croak/core/commands.py`

Add `vfrog` to the `ALLOWED_COMMANDS` dict (line 45), matching the **real CLI subcommands**:

```python
ALLOWED_COMMANDS = {
    # ... existing entries ...
    # vfrog.ai CLI (Go binary)
    'vfrog': [
        'version', 'login', 'config', 'organisations', 'projects',
        'dataset_images', 'objects', 'iterations', 'iteration', 'inference',
        'completion',
    ],
}
```

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
    json_output: bool = True,
) -> Dict[str, Any]:
    """Run vfrog CLI command securely.

    Args:
        args: Command arguments (e.g., ['projects', 'list']).
        cwd: Working directory.
        timeout: Timeout in seconds.
        json_output: Append --json flag for machine-readable output.

    Returns:
        Dict with success status, parsed output, and error.
    """
    cmd = ['vfrog'] + args
    if json_output:
        cmd.append('--json')
    try:
        result = cls.run(cmd, cwd=cwd, capture_output=True, timeout=timeout, check=False)
        parsed = None
        if result.stdout and json_output:
            try:
                import json
                parsed = json.loads(result.stdout)
            except json.JSONDecodeError:
                parsed = None
        return {
            'success': result.returncode == 0,
            'output': parsed if parsed else result.stdout,
            'raw': result.stdout,
            'error': result.stderr if result.returncode != 0 else None,
        }
    except CommandExecutionError as e:
        return {'success': False, 'output': None, 'raw': None, 'error': str(e)}
```

Note: `check=False` because we handle non-zero exit codes in the return dict, not via exception.
The `json_output` parameter auto-appends `--json` and attempts to parse the response.

#### 1.3 Replace `VfrogClient` with `VfrogCLI`

**File**: `src/croak/integrations/vfrog.py`

Rewrite the file. Replace the `VfrogClient` class with a `VfrogCLI` class using static methods
that delegate to `SecureRunner.run_vfrog()`.

Key design decisions:
- All methods are `@staticmethod` -- the CLI manages its own auth state in `~/.vfrog/`.
- Every method uses `--json` for machine-parseable output.
- **No `httpx` import** -- the CLI handles all HTTP communication.
- **Auth is login-based** (email/password), not API-key based for CLI operations.
  `VFROG_API_KEY` only applies to the `inference` command.
- Pydantic models updated to match actual vfrog data structures (projects have `title` not `name`,
  organisations have `id`/`name`/`plan_type`, etc.).

```python
import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from croak.core.commands import SecureRunner


class VfrogProject(BaseModel):
    """vfrog project information."""
    id: str
    title: str
    organisation_id: str


class VfrogObject(BaseModel):
    """vfrog object (product image) information."""
    id: str
    label: str
    filename: str
    file_path: str


class VfrogIteration(BaseModel):
    """vfrog iteration information."""
    id: str
    iteration_number: int
    status: str
    trained_status: Optional[str] = None
    model_id: Optional[str] = None


class VfrogCLI:
    """Wrapper around vfrog CLI tool (Go binary).

    The vfrog CLI manages its own auth state in ~/.vfrog/.
    Authentication is email/password via Supabase, NOT API-key based.
    VFROG_API_KEY is only used for the 'inference' command.

    Context hierarchy (must be set in order):
    1. organisation_id (required for all commands)
    2. project_id (required for most commands)
    3. object_id (required for iteration commands)
    """

    # --- Setup & Auth ---

    @staticmethod
    def check_installed() -> bool:
        """Check if vfrog CLI binary is available on PATH."""
        return SecureRunner.check_command_available('vfrog')

    @staticmethod
    def check_authenticated() -> bool:
        """Check if user is logged in by inspecting config."""
        result = SecureRunner.run_vfrog(['config', 'show'])
        if not result['success']:
            return False
        output = result['output']
        if isinstance(output, dict):
            return output.get('authenticated', False)
        return False

    @staticmethod
    def login(email: str, password: str) -> Dict[str, Any]:
        """Login to vfrog platform."""
        return SecureRunner.run_vfrog(
            ['login', '--email', email, '--password', password],
            json_output=False,
        )

    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get current CLI config (org, project, auth status)."""
        return SecureRunner.run_vfrog(['config', 'show'])

    @staticmethod
    def set_organisation(org_id: str) -> Dict[str, Any]:
        """Set the active organisation. Clears project_id."""
        return SecureRunner.run_vfrog(
            ['config', 'set', 'organisation', '--organisation_id', org_id]
        )

    @staticmethod
    def set_project(project_id: str) -> Dict[str, Any]:
        """Set the active project."""
        return SecureRunner.run_vfrog(
            ['config', 'set', 'project', '--project_id', project_id]
        )

    @staticmethod
    def set_object(object_id: str) -> Dict[str, Any]:
        """Set the active object (product image)."""
        return SecureRunner.run_vfrog(
            ['config', 'set', 'object', '--object_id', object_id]
        )

    # --- Organisations ---

    @staticmethod
    def list_organisations() -> Dict[str, Any]:
        """List organisations the user belongs to."""
        return SecureRunner.run_vfrog(['organisations', 'list'])

    # --- Projects ---

    @staticmethod
    def list_projects() -> Dict[str, Any]:
        """List projects in the active organisation."""
        return SecureRunner.run_vfrog(['projects', 'list'])

    @staticmethod
    def create_project(name: str) -> Dict[str, Any]:
        """Create a new project in the active organisation."""
        return SecureRunner.run_vfrog(['projects', 'create', name])

    # --- Dataset Images ---

    @staticmethod
    def upload_dataset_images(urls: List[str]) -> Dict[str, Any]:
        """Upload dataset images from URLs. Local file upload not supported in v0.1."""
        return SecureRunner.run_vfrog(
            ['dataset_images', 'upload'] + urls,
            timeout=600,
        )

    @staticmethod
    def list_dataset_images() -> Dict[str, Any]:
        """List dataset images in the active project."""
        return SecureRunner.run_vfrog(['dataset_images', 'list'])

    @staticmethod
    def delete_dataset_image(image_id: str) -> Dict[str, Any]:
        """Delete a dataset image by ID."""
        return SecureRunner.run_vfrog(
            ['dataset_images', 'delete', '--dataset_image_id', image_id]
        )

    # --- Objects (Product Images) ---

    @staticmethod
    def create_object(url: str, label: str = '', external_id: str = '') -> Dict[str, Any]:
        """Create a new object (product image) from a URL."""
        args = ['objects', 'create', url]
        if label:
            args.extend(['--label', label])
        if external_id:
            args.extend(['--external_id', external_id])
        return SecureRunner.run_vfrog(args)

    @staticmethod
    def list_objects() -> Dict[str, Any]:
        """List objects in the active project."""
        return SecureRunner.run_vfrog(['objects', 'list'])

    @staticmethod
    def delete_object(object_id: str) -> Dict[str, Any]:
        """Delete an object by ID."""
        return SecureRunner.run_vfrog(
            ['objects', 'delete', '--object_id', object_id]
        )

    # --- Iterations (SSAT Loop) ---

    @staticmethod
    def list_iterations(object_id: Optional[str] = None) -> Dict[str, Any]:
        """List iterations for an object."""
        args = ['iterations', 'list']
        if object_id:
            args.extend(['--object_id', object_id])
        return SecureRunner.run_vfrog(args)

    @staticmethod
    def create_iteration(object_id: str, random_count: int = 20) -> Dict[str, Any]:
        """Create a new iteration (selects random dataset images)."""
        return SecureRunner.run_vfrog(
            ['iterations', 'create', object_id, '--random', str(random_count)]
        )

    @staticmethod
    def run_ssat(
        iteration_id: str,
        random_count: int = 0,
        restart: bool = False,
    ) -> Dict[str, Any]:
        """Start SSAT auto-annotation for an iteration.

        - Iteration 1: Uses cutout extraction and matching
        - Iteration 2+: Uses trained model inference

        Default image counts by iteration: #1=20, #2=40, #3+=80.
        Use random_count to override with random selection from project.
        """
        args = ['iterations', 'ssat', '--iteration_id', iteration_id]
        if random_count > 0:
            args.extend(['--random', str(random_count)])
        if restart:
            args.append('--restart')
        return SecureRunner.run_vfrog(args, timeout=600)

    @staticmethod
    def get_halo_url(iteration_id: str) -> Dict[str, Any]:
        """Get HALO (Human Assisted Labelling) URL for an iteration."""
        return SecureRunner.run_vfrog(
            ['iterations', 'halo', '--iteration_id', iteration_id]
        )

    @staticmethod
    def next_iteration(iteration_id: str) -> Dict[str, Any]:
        """Create the next iteration from the current one."""
        return SecureRunner.run_vfrog(
            ['iterations', 'next', '--iteration_id', iteration_id]
        )

    @staticmethod
    def restart_iteration(iteration_id: str) -> Dict[str, Any]:
        """Restart an iteration (delete and recreate)."""
        return SecureRunner.run_vfrog(
            ['iterations', 'restart', '--iteration_id', iteration_id]
        )

    # --- Training (on vfrog platform) ---

    @staticmethod
    def train_iteration(iteration_id: str) -> Dict[str, Any]:
        """Train a model for an iteration on vfrog's infrastructure."""
        return SecureRunner.run_vfrog(
            ['iteration', 'train', '--iteration_id', iteration_id],
            timeout=3600,  # training can take a long time
        )

    # --- Inference ---

    @staticmethod
    def run_inference(
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run inference on an image using a trained vfrog model.

        Args:
            image_path: Local image file path.
            image_url: Image URL.
            api_key: API key (falls back to VFROG_API_KEY env var).
        """
        args = ['inference']
        if api_key:
            args.extend(['--api-key', api_key])
        if image_path:
            args.extend(['--image', image_path])
        elif image_url:
            args.extend(['--image_url', image_url])
        return SecureRunner.run_vfrog(args)
```

#### 1.4 Update `__init__.py` exports

**File**: `src/croak/integrations/__init__.py`

Export `VfrogCLI` instead of (or in addition to) `VfrogClient`.

---

### Phase 2: CLI Commands -- Wire Up croak vfrog/annotate/deploy Subcommands

#### 2.1 Add `croak vfrog` command group

**File**: `src/croak/cli.py`

New command group for vfrog-specific setup that doesn't map to other croak commands:

```python
@main.group()
def vfrog():
    """vfrog platform integration commands."""
    pass

@vfrog.command()
def setup():
    """Interactive vfrog CLI setup (login, select org/project)."""
    # 1. Check vfrog CLI is installed
    # 2. Run vfrog login (prompt email/password)
    # 3. List organisations, let user pick
    # 4. Set organisation
    # 5. List or create project
    # 6. Set project
    # 7. Save vfrog project_id to .croak/config.yaml

@vfrog.command()
def status():
    """Show vfrog config and auth status."""
    # Runs: vfrog config show --json
```

#### 2.2 Implement `croak annotate` (dual-mode: classic + vfrog SSAT)

**File**: `src/croak/cli.py` (lines 476-482)

Replace the stub. The annotation command supports **two workflows** selected via `--method`:

```python
@main.command()
@click.option("--method", type=click.Choice(["vfrog", "classic"]),
              default="vfrog", help="Annotation method")
@click.option("--iteration-id", help="Resume existing vfrog iteration")
@click.option("--object-id", help="Target vfrog object for iteration")
@click.option("--random", "random_count", type=int, default=20,
              help="Random dataset images for SSAT (vfrog only)")
@click.option("--status", is_flag=True, help="Check annotation status only")
@click.option("--halo", is_flag=True, help="Open HALO URL for review (vfrog only)")
@click.option("--format", "ann_format",
              type=click.Choice(["yolo", "coco", "voc"]), default="yolo",
              help="Annotation format (classic only)")
def annotate(method, ...):
    """Annotate dataset images."""
    if method == "vfrog":
        # vfrog SSAT workflow (see below)
        ...
    else:
        # Classic workflow (see below)
        ...
```

**Path A: vfrog SSAT** (`croak annotate --method vfrog`, the default)

1. Check vfrog CLI is installed and authenticated
2. Ensure project context is set (or run `croak vfrog setup`)
3. Upload dataset images to vfrog (URLs from a manifest or hosted images)
4. Create objects (product images -- what to detect)
5. Create iteration #1
6. Run SSAT auto-annotation
7. Print HALO URL for human review
8. Wait for user to complete review
9. Update pipeline state with `annotation_source: "vfrog"`

**Path B: Classic** (`croak annotate --method classic`)

1. Verify images exist in `data/raw/` or configured data directory
2. Print guidance on annotation tools (CVAT, Label Studio, Roboflow, etc.)
3. Prompt user to provide path to exported annotations
4. Validate annotation format (YOLO/COCO/VOC)
5. Copy/convert annotations to `data/processed/`
6. Update pipeline state with `annotation_source: "classic"`

The default is `vfrog` because Coach promotes vfrog's simplicity. But users who
already have annotations or prefer other tools can use `--method classic` and
proceed directly to training with local or Modal providers.

**Important (vfrog path only)**: Since vfrog only accepts image URLs (not local
files in v0.1), CROAK must either:
- (a) Require images to already be hosted (S3, GCS, public URL), or
- (b) Provide a helper to upload local images to a temporary host and pass URLs

This is a known limitation. For v1, we require hosted URLs and document the workaround.

#### 2.3 Restructure `croak deploy` subcommands

**File**: `src/croak/cli.py` (lines 975-1013)

Restructure the `deploy` group to have three explicit targets:

```python
@deploy.command()
def vfrog_deploy(model, name):
    """Deploy/test on vfrog platform (inference endpoint)."""
    # 1. Verify vfrog auth + context
    # 2. Run vfrog inference with test image
    # 3. Report results

@deploy.command()
def modal(model, name, gpu):
    """Deploy to Modal.com serverless endpoint."""
    # Current 'cloud' implementation, relocated here

@deploy.command()
def edge(model, formats):
    """Export for edge devices."""
    # Existing implementation, unchanged
```

The current `croak deploy cloud` becomes `croak deploy modal` (keeping the same code).
`croak deploy vfrog` is new -- it runs `vfrog inference` to test the trained model.

Note: vfrog doesn't have explicit deploy/staging/production commands. Once a model is trained
via `vfrog iteration train`, the inference endpoint is automatically available. So `croak deploy vfrog`
is really "verify that inference works" rather than a traditional deploy.

#### 2.4 Add `croak train --provider` flag

**File**: `src/croak/cli.py`

Extend the existing `croak train` command to accept a `--provider` flag:

```python
@main.command()
@click.option("--provider", type=click.Choice(["local", "modal", "vfrog"]),
              default="local", help="Training provider")
def train(provider):
    """Train model using specified provider."""
    if provider == "vfrog":
        # Runs: vfrog iteration train --iteration_id <id>
        # Requires annotation_source == "vfrog" in pipeline state
        ...
    elif provider == "modal":
        # Existing Modal training path
        # Requires exported annotations (YOLO format) -- works with any annotation_source
        ...
    else:
        # Existing local training path (yolo train)
        # Requires exported annotations (YOLO format) -- works with any annotation_source
        ...
```

**Two training paradigms** (Coach must understand both):

| | Classic (local / Modal) | vfrog SSAT |
|---|---|---|
| **Annotation** | Any tool → export YOLO/COCO → local files | vfrog SSAT iterations → auto-annotation + HALO review |
| **Data lives** | Local disk (`data/processed/`) | vfrog platform |
| **Training runs** | `yolo train` (local) or `modal run` (cloud) | `vfrog iteration train` (platform-managed) |
| **User controls** | Architecture, hyperparams, augmentation, epochs | vfrog handles all config per iteration |
| **Output** | Local `.pt` weights file | Model on vfrog platform (inference endpoint) |
| **Best for** | Full control, custom architectures, local iteration | Simplicity, fast iteration, minimal ML expertise needed |

When `--provider vfrog` is used, training happens **on vfrog's infrastructure**, not locally.
When `--provider local` or `--provider modal` is used, the classic annotate → export → train
pipeline applies. Users can annotate with vfrog SSAT and then export (when available) or
annotate with any tool and train locally/on Modal -- these paths are **not mutually exclusive**.

Coach should **recommend vfrog** for users who are new to ML or want the fastest path to a
working model, while clearly offering local/Modal as the alternative for users who want
full control over architecture, hyperparameters, and training configuration.

---

### Phase 3: Agent YAML Definitions -- Real vfrog CLI Commands

Every agent's YAML needs updating to reflect the real vfrog CLI commands they can execute.

#### 3.1 Update Router Agent (Dispatcher) YAML

**File**: `agents/router/router.agent.yaml`

Add vfrog context management capabilities:

```yaml
capabilities:
  items:
    # ... existing items ...
    - id: "vfrog_setup"
      name: "vfrog Platform Setup"
      description: "Guide user through vfrog CLI login, organisation selection, and project configuration"

menu:
  commands:
    # ... existing commands ...
    - trigger: "vfrog setup"
      aliases:
        - "setup vfrog"
        - "connect vfrog"
        - "vfrog login"
      cli: "croak vfrog setup"
      description: "Interactive vfrog CLI setup (login, select org/project)"
      type: "workflow"
      capability: "vfrog_setup"
      mutates_state: true
      requires_confirmation: false

    - trigger: "vfrog status"
      aliases:
        - "vfrog config"
        - "vfrog info"
      cli: "croak vfrog status"
      description: "Show vfrog auth and config status"
      type: "query"
      capability: "vfrog_setup"
      mutates_state: false
      requires_confirmation: false
```

Add vfrog CLI commands the Router can execute directly:

```yaml
vfrog_commands:
  - "vfrog version"
  - "vfrog config show --json"
  - "vfrog organisations list --json"
  - "vfrog config set organisation --organisation_id <id>"
  - "vfrog projects list --json"
  - "vfrog config set project --project_id <id>"
```

Update guardrails to check vfrog context:

```yaml
guardrails:
  checks:
    # ... existing checks ...
    - id: "vfrog_context_set"
      name: "vfrog Context Configured"
      check: "vfrog_org_and_project_set"
      trigger: "before_vfrog_command"
      condition: "vfrog config show --json returns organisation_id and project_id"
      severity: "error"
      error_message: "vfrog context not configured. Run 'croak vfrog setup' to login and select organisation/project."
```

#### 3.2 Update Data Agent (Scout) YAML

**File**: `agents/data/data.agent.yaml`

Scout supports both annotation methods. Update capability to reflect dual paths:

```yaml
capabilities:
  items:
    - id: "vfrog_annotation"
      name: "vfrog SSAT Annotation"
      description: "Manage vfrog SSAT annotation workflow: upload dataset images, create objects, run iterations with auto-annotation, and guide HALO review. Recommended for ease of use."
    - id: "classic_annotation"
      name: "Classic Annotation Import"
      description: "Import annotations from external tools (CVAT, Label Studio, Roboflow, etc.) in YOLO, COCO, or VOC format for local/Modal training"
```

Update persona principles to promote vfrog but support classic:

```yaml
persona:
  principles: |
    - Data quality > data quantity for detection tasks
    - Always validate before expensive operations (training, annotation)
    - Version datasets like code - you'll thank yourself later
    - Document data decisions for reproducibility
    - vfrog is the easiest path to quality annotations - recommend it first
    - Classic annotation tools work too - support users who prefer them
    - When in doubt, visualize the data
    - Class imbalance is a silent killer - always check
```

Update the annotate command and add new commands for both paths:

```yaml
menu:
  commands:
    - trigger: "annotate"
      aliases:
        - "label"
        - "get labels"
        - "start annotation"
        - "label images"
      cli: "croak annotate"
      description: "Annotate dataset images (defaults to vfrog SSAT; use --method classic for manual tools)"
      type: "workflow"
      workflow: "workflows/data-preparation/steps/step-04-annotate.md"
      capability: "vfrog_annotation"
      mutates_state: true
      requires_confirmation: true

    - trigger: "annotate vfrog"
      aliases:
        - "send to vfrog"
        - "ssat"
        - "vfrog annotate"
      cli: "croak annotate --method vfrog"
      description: "Start vfrog SSAT annotation workflow (upload images, auto-annotate, HALO review)"
      type: "workflow"
      workflow: "workflows/data-preparation/steps/step-04-annotate.md"
      capability: "vfrog_annotation"
      mutates_state: true
      requires_confirmation: true

    - trigger: "annotate classic"
      aliases:
        - "import annotations"
        - "manual annotation"
        - "import labels"
      cli: "croak annotate --method classic"
      description: "Import annotations from external tools (CVAT, Label Studio, Roboflow) in YOLO/COCO/VOC format"
      type: "workflow"
      workflow: "workflows/data-preparation/steps/step-04-annotate.md"
      capability: "classic_annotation"
      mutates_state: true
      requires_confirmation: true

    - trigger: "upload images"
      aliases:
        - "upload to vfrog"
        - "add dataset images"
      cli: "croak vfrog upload"
      description: "Upload dataset images to vfrog project (URL-based)"
      type: "action"
      capability: "vfrog_annotation"
      mutates_state: true
      requires_confirmation: true

    - trigger: "halo"
      aliases:
        - "review annotations"
        - "open halo"
        - "annotation review"
      cli: "croak annotate --halo"
      description: "Open HALO URL for human annotation review (vfrog only)"
      type: "query"
      capability: "vfrog_annotation"
      mutates_state: false
      requires_confirmation: false
```

Add vfrog CLI commands the Scout can execute:

```yaml
vfrog_commands:
  - "vfrog dataset_images upload <urls> --json"
  - "vfrog dataset_images list --json"
  - "vfrog dataset_images delete --dataset_image_id <id>"
  - "vfrog objects create <url> --label <label> --json"
  - "vfrog objects list --json"
  - "vfrog objects delete --object_id <id>"
  - "vfrog iterations list --object_id <id> --json"
  - "vfrog iterations create <object_id> --random <N> --json"
  - "vfrog iterations ssat --iteration_id <id> --json"
  - "vfrog iterations ssat --iteration_id <id> --random <N> --json"
  - "vfrog iterations halo --iteration_id <id> --json"
  - "vfrog iterations next --iteration_id <id> --json"
  - "vfrog iterations restart --iteration_id <id> --json"
  - "vfrog config show --json"
```

Update guardrails:

```yaml
guardrails:
  checks:
    # ... existing checks ...
    - id: "vfrog_cli_installed"
      name: "vfrog CLI Installed"
      check: "vfrog_binary_available"
      trigger: "before_annotation"
      condition: "vfrog binary is available on PATH"
      severity: "error"
      error_message: "vfrog CLI not installed. Download from: https://github.com/vfrog-ai/vfrog-cli/releases"

    - id: "vfrog_authenticated"
      name: "vfrog Authenticated"
      check: "vfrog_login_valid"
      trigger: "before_annotation"
      condition: "vfrog config show --json shows authenticated: true"
      severity: "error"
      error_message: "Not logged in to vfrog. Run 'vfrog login' or 'croak vfrog setup' first."

    - id: "vfrog_project_set"
      name: "vfrog Project Set"
      check: "vfrog_project_context"
      trigger: "before_annotation"
      condition: "vfrog config show --json has non-empty project_id"
      severity: "error"
      error_message: "No vfrog project selected. Run 'croak vfrog setup' to select or create a project."
```

#### 3.3 Update Training Agent (Coach) YAML

**File**: `agents/training/training.agent.yaml`

The Coach must understand and present **two distinct training paradigms** without locking
users into either one. Coach should actively promote vfrog's ease of use while clearly
supporting the classic pipeline for users who want full control.

**Update persona** to reflect dual-path philosophy:

```yaml
persona:
  role: "ML Training Specialist + Experiment Design Expert"
  identity: |
    Senior ML engineer specializing in object detection training.
    Expert in YOLO family, RT-DETR, and training optimization.
    Pragmatic about model selection - recommends proven architectures over shiny new things.
    Knows GPU costs and always estimates before running anything expensive.
    Been burned by irreproducible experiments - now seeds everything religiously.
    Appreciates that vfrog makes annotation and training dead simple for most use cases.
    Also respects users who want full control over their training pipeline.
  communication_style: |
    Data-driven and precise. Speaks in metrics and reproducibility.
    Always provides rationale for recommendations - no black boxes.
    "Here's what I'd do, and here's why..."
    Warns early about common pitfalls and compute costs.
    Celebrates when training goes well, debugs calmly when it doesn't.
    When a user is deciding how to train, presents both paths honestly:
    "vfrog handles the complexity for you -- or if you want full control, we can run locally/on Modal."
  principles: |
    - Two paths to a trained model: vfrog (simple, iterative) or classic (full control)
    - Recommend vfrog first for new users -- annotation + training in one platform, no ML expertise needed
    - Support classic path fully for users who want to choose architecture, hyperparams, and augmentation
    - Start with the smallest model that could work (classic path)
    - Reproducibility is non-negotiable -- seed everything, log everything (classic path)
    - Validate config before expensive training runs
    - Baseline first, then iterate
    - Training time is money - always estimate before running (classic path)
    - Three providers: local GPU, Modal.com (serverless GPU), vfrog (platform-managed)
    - vfrog training uses SSAT iterations - each iteration improves on the last; user doesn't pick architecture
    - Classic path: user controls architecture, hyperparams, epochs, augmentation -- YOLOv8s is a solid default
    - Never force a user into one path -- present both, recommend vfrog for simplicity, respect their choice
```

**Update capabilities** to distinguish both training paths:

```yaml
capabilities:
  summary: "Configure, generate, and guide execution of detection model training via classic pipeline or vfrog SSAT"
  items:
    - id: "architecture_selection"
      name: "Architecture Selection"
      description: "Recommend model architecture based on requirements and constraints (classic path only -- vfrog handles this automatically)"
    - id: "config_generation"
      name: "Config Generation"
      description: "Generate training configuration files with sensible defaults (classic path only)"
    - id: "script_generation"
      name: "Script Generation"
      description: "Generate training scripts for local or Modal execution (classic path only)"
    - id: "gpu_guidance"
      name: "GPU Guidance"
      description: "Guide user to provision appropriate GPU environment (classic path only -- vfrog manages its own GPU)"
    - id: "cost_estimation"
      name: "Cost Estimation"
      description: "Estimate training time and compute cost before running (classic path -- vfrog has its own billing)"
    - id: "experiment_tracking"
      name: "Experiment Tracking"
      description: "Setup and integrate experiment tracking: MLflow/W&B (classic path)"
    - id: "checkpoint_management"
      name: "Checkpoint Management"
      description: "Handle checkpoints, resume interrupted training (classic path)"
    - id: "vfrog_training"
      name: "vfrog Platform Training"
      description: "Train models on vfrog infrastructure via iteration-based SSAT workflow. Annotation and training happen together -- the platform handles architecture, hyperparams, and iteration progression."
    - id: "workflow_selection"
      name: "Training Workflow Selection"
      description: "Help user choose between vfrog (simple, iterative) and classic (full control) training paths based on their needs and experience"
```

**Update menu commands** to make both paths first-class:

```yaml
menu:
  commands:
    # ... existing commands (recommend, configure, estimate, resume, compare) stay as-is ...
    # They apply to the classic path.

    - trigger: "train"
      aliases:
        - "start training"
        - "run training"
        - "begin training"
        - "execute training"
      cli: "croak train"
      description: "Train model (defaults to local; use --provider modal or --provider vfrog)"
      type: "workflow"
      workflow: "workflows/model-training/workflow.yaml"
      capability: "script_generation"
      mutates_state: true
      requires_confirmation: true

    - trigger: "train vfrog"
      aliases:
        - "vfrog train"
        - "train on vfrog"
        - "ssat train"
        - "train simple"
      cli: "croak train --provider vfrog"
      description: "Train model on vfrog platform (simple -- vfrog handles architecture and config)"
      type: "workflow"
      capability: "vfrog_training"
      mutates_state: true
      requires_confirmation: true

    - trigger: "train modal"
      aliases:
        - "modal train"
        - "train cloud"
        - "train on modal"
      cli: "croak train --provider modal"
      description: "Train model on Modal.com (full control -- you choose architecture and hyperparams)"
      type: "workflow"
      workflow: "workflows/model-training/workflow.yaml"
      capability: "script_generation"
      mutates_state: true
      requires_confirmation: true

    - trigger: "train local"
      aliases:
        - "local train"
        - "train on gpu"
        - "train here"
      cli: "croak train --provider local"
      description: "Train model locally (full control -- requires local GPU with 8GB+ VRAM)"
      type: "workflow"
      workflow: "workflows/model-training/workflow.yaml"
      capability: "script_generation"
      mutates_state: true
      requires_confirmation: true

    - trigger: "which training"
      aliases:
        - "how should i train"
        - "training options"
        - "compare training"
        - "vfrog or local"
      cli: "croak recommend --training-path"
      description: "Compare vfrog (simple) vs classic (full control) training and recommend based on your situation"
      type: "query"
      capability: "workflow_selection"
      mutates_state: false
      requires_confirmation: false
```

Add vfrog CLI commands the Coach can execute:

```yaml
vfrog_commands:
  - "vfrog iteration train --iteration_id <id> --json"
  - "vfrog iterations list --object_id <id> --json"
  - "vfrog config show --json"
```

**Update critical actions** to enforce both paths correctly:

```yaml
critical_actions:
  items:
    # ... existing items (verify_dataset, set_seeds, etc.) ...
    # NOTE: set_seeds, configure_tracking, estimate_time apply to classic path only.
    # Add clarifying comments to each:

    - id: "default_modal"
      rule: "DEFAULT to Modal.com for GPU provisioning when local GPU is unavailable (classic path only -- vfrog manages its own GPU)"
      when: "during_gpu_guidance"
      violation: "warning"

    - id: "vfrog_iteration_ready"
      rule: "ALWAYS verify iteration has been through SSAT annotation and HALO review before training on vfrog"
      when: "before_vfrog_training"
      violation: "error"

    - id: "recommend_vfrog_first"
      rule: "ALWAYS present vfrog as the simpler option when user hasn't chosen a training path yet; explain that vfrog handles annotation, architecture, and training in one platform while classic gives full control"
      when: "during_workflow_selection"
      violation: "warning"

    - id: "respect_user_choice"
      rule: "NEVER push vfrog after user has explicitly chosen classic training; support their choice fully"
      when: "after_workflow_selection"
      violation: "warning"

    - id: "no_cross_path_confusion"
      rule: "NEVER mix vfrog and classic concepts in the same recommendation (e.g., don't suggest hyperparameter tuning for vfrog training, or SSAT iterations for local training)"
      when: "during_training_guidance"
      violation: "error"
```

**Update guardrails**:

```yaml
guardrails:
  checks:
    # ... existing checks (dataset_exists, gpu_available, sufficient_data, etc.) ...

    - id: "vfrog_iteration_exists"
      name: "vfrog Iteration Exists"
      check: "vfrog_iteration_for_training"
      trigger: "before_vfrog_training"
      condition: "An iteration with status suitable for training exists"
      severity: "error"
      error_message: "No vfrog iteration ready for training. Run 'croak annotate --method vfrog' to create and annotate an iteration first."

    - id: "classic_annotations_exist"
      name: "Classic Annotations Exist"
      check: "annotation_files_present"
      trigger: "before_classic_training"
      condition: "Annotation files exist in data/processed/ in YOLO format"
      severity: "error"
      error_message: "No annotations found for classic training. Run 'croak annotate --method classic' to import annotations, or try 'croak annotate --method vfrog' for easier annotation with vfrog."

    - id: "provider_matches_annotation"
      name: "Provider Matches Annotation Source"
      check: "annotation_provider_compatibility"
      trigger: "before_training"
      condition: "If provider=vfrog, annotation_source must be 'vfrog'. If provider=local/modal, local annotations must exist."
      severity: "error"
      error_message: "Training provider doesn't match annotation source. vfrog training requires vfrog annotations; local/Modal training requires exported annotation files."
```

#### 3.4 Update Evaluation Agent (Judge) YAML

**File**: `agents/evaluation/evaluation.agent.yaml`

Add vfrog inference for evaluation:

```yaml
capabilities:
  items:
    # ... existing items ...
    - id: "vfrog_inference_eval"
      name: "vfrog Inference Evaluation"
      description: "Evaluate trained vfrog model by running inference and analyzing results"

menu:
  commands:
    # ... existing commands ...
    - trigger: "test vfrog"
      aliases:
        - "vfrog inference"
        - "test vfrog model"
        - "evaluate vfrog"
      cli: "croak evaluate --provider vfrog"
      description: "Evaluate vfrog-trained model via inference endpoint"
      type: "action"
      capability: "vfrog_inference_eval"
      mutates_state: false
      requires_confirmation: false
```

Add vfrog CLI commands the Judge can execute:

```yaml
vfrog_commands:
  - "vfrog inference --api-key <key> --image <path> --json"
  - "vfrog inference --api-key <key> --image_url <url> --json"
  - "vfrog config show --json"
```

#### 3.5 Update Deployment Agent (Shipper) YAML

**File**: `agents/deployment/deployment.agent.yaml`

Restructure cloud deployment to differentiate vfrog vs Modal:

```yaml
capabilities:
  items:
    - id: "cloud_deployment_vfrog"
      name: "vfrog Cloud Deployment"
      description: "Test and verify model inference on vfrog platform endpoint"
    - id: "cloud_deployment_modal"
      name: "Modal Cloud Deployment"
      description: "Deploy to Modal.com serverless endpoint with auto-scaling"
    - id: "edge_deployment"
      name: "Edge Deployment"
      description: "Generate optimized models for edge devices (Jetson, embedded)"
    # ... other existing items ...

menu:
  commands:
    - trigger: "deploy vfrog"
      aliases:
        - "vfrog deploy"
        - "ship to vfrog"
      cli: "croak deploy vfrog"
      description: "Verify model inference on vfrog platform endpoint"
      type: "workflow"
      workflow: "workflows/model-deployment/steps/step-03-cloud.md"
      capability: "cloud_deployment_vfrog"
      mutates_state: true
      requires_confirmation: true

    - trigger: "deploy modal"
      aliases:
        - "modal deploy"
        - "ship to modal"
        - "deploy cloud"
        - "cloud deploy"
      cli: "croak deploy modal"
      description: "Deploy model to Modal.com serverless endpoint"
      type: "workflow"
      capability: "cloud_deployment_modal"
      mutates_state: true
      requires_confirmation: true

    - trigger: "deploy edge"
      aliases:
        - "edge deploy"
        - "deploy local"
        - "ship to edge"
      cli: "croak deploy edge"
      description: "Package model for edge device deployment"
      type: "workflow"
      workflow: "workflows/model-deployment/steps/step-04-edge.md"
      capability: "edge_deployment"
      mutates_state: true
      requires_confirmation: true
```

Add vfrog CLI commands the Shipper can execute:

```yaml
vfrog_commands:
  - "vfrog inference --api-key <key> --image <path> --json"
  - "vfrog inference --api-key <key> --image_url <url> --json"
  - "vfrog config show --json"
```

Update guardrails:

```yaml
guardrails:
  checks:
    - id: "vfrog_credentials"
      name: "vfrog Credentials"
      check: "vfrog_cli_and_auth"
      trigger: "before_vfrog_deploy"
      condition: "vfrog CLI is installed and user is authenticated"
      severity: "error"
      error_message: "vfrog CLI not installed or not authenticated. Install from https://github.com/vfrog-ai/vfrog-cli/releases and run 'vfrog login'."

    - id: "vfrog_api_key_for_inference"
      name: "vfrog API Key for Inference"
      check: "vfrog_api_key_set"
      trigger: "before_vfrog_inference"
      condition: "VFROG_API_KEY environment variable is set"
      severity: "error"
      error_message: "VFROG_API_KEY not set. Required for inference. Get your key at https://platform.vfrog.ai"
```

#### 3.6 Create deployment workflow step files

**Directory**: `workflows/model-deployment/steps/` (does not exist yet)

These filenames must match the agent YAML `workflow:` references:

| File | Purpose | Matches Agent YAML |
|------|---------|-------------------|
| `step-01-optimize.md` | FP16/INT8 quantization, benchmark | deployment.agent.yaml line 77 |
| `step-02-export.md` | Export model, validate with sample inference | deployment.agent.yaml line 91 |
| `step-03-cloud.md` | **vfrog inference verification** (the key file) | deployment.agent.yaml line 105 |
| `step-04-edge.md` | Edge packaging, inference script generation | deployment.agent.yaml line 119 |

The `step-03-cloud.md` file documents the actual vfrog CLI commands for inference testing:

```bash
# Verify vfrog CLI and auth
vfrog version
vfrog config show --json

# Run inference test
vfrog inference --api-key $VFROG_API_KEY --image ./test-image.jpg --json

# Alternative: inference via URL
vfrog inference --api-key $VFROG_API_KEY --image_url https://example.com/test.jpg --json
```

#### 3.7 Update annotation workflow step

**File**: `workflows/data-preparation/steps/step-04-annotate.md`

Complete rewrite to support both annotation methods:

```markdown
# Step 4: Annotate Dataset Images

This step supports two annotation methods. Scout recommends vfrog for its simplicity
but fully supports classic annotation tools.

## Method Selection

Coach/Scout should ask: "Would you like to use vfrog for annotation? It handles
auto-annotation and iterative refinement for you. Or would you prefer to use your
own annotation tool and import the labels?"

Default: vfrog (--method vfrog)

---

## Path A: vfrog SSAT (Recommended)

### Execution Rules
- ALWAYS verify vfrog CLI is installed and authenticated
- ALWAYS verify organisation and project context is set
- WAIT for user to complete HALO review before proceeding
- Record annotation_source as "vfrog" in pipeline state

### Execution Sequence

#### 1. Verify vfrog Setup
VfrogCLI.check_installed()
VfrogCLI.check_authenticated()
VfrogCLI.get_config()  # verify org + project set

#### 2. Upload Dataset Images
VfrogCLI.upload_dataset_images(image_urls)

#### 3. Create Object (Product Image)
VfrogCLI.create_object(product_image_url, label="target-object")
VfrogCLI.set_object(object_id)

#### 4. Create Iteration
VfrogCLI.create_iteration(object_id, random_count=20)

#### 5. Run SSAT Auto-Annotation
VfrogCLI.run_ssat(iteration_id)

#### 6. Guide HALO Review
VfrogCLI.get_halo_url(iteration_id)
# Print URL, instruct user to review and correct annotations in browser

#### 7. Update Pipeline State
# Record iteration_id, object_id, project context
# Set annotation_source: "vfrog"

### Why vfrog?
- Auto-annotation reduces manual work by 80-90%
- HALO review catches errors with human-in-the-loop
- Each iteration improves on the last -- model gets better as you annotate
- No ML expertise needed -- vfrog handles the complexity
- Training is one command away: `croak train --provider vfrog`

---

## Path B: Classic Annotation Import

### Execution Rules
- Support YOLO, COCO, and Pascal VOC annotation formats
- Validate imported annotations before accepting
- Record annotation_source as "classic" in pipeline state

### Execution Sequence

#### 1. Guide User to Annotation Tools
Print supported tools: CVAT, Label Studio, Roboflow, LabelImg, etc.
Link to format documentation.

#### 2. Accept Annotation Path
Prompt user for directory containing annotations.
Accept --format flag (yolo, coco, voc).

#### 3. Validate Annotations
Run DataValidator on imported annotations:
- Format schema validation
- Bounding box sanity checks
- Class name consistency
- Coverage check (annotations vs images)

#### 4. Convert if Needed
If format != yolo, convert to YOLO format for training.
Store in data/processed/.

#### 5. Update Pipeline State
# Set annotation_source: "classic"
# Record format, annotation_path, class list

### When to choose classic?
- You already have annotations from another tool
- You need a specific annotation format not supported by vfrog
- You want full control over the annotation-to-training pipeline
- You plan to train locally or on Modal with custom architecture
```

---

### Phase 4: Knowledge and Installer Updates

#### 4.1 Rewrite vfrog knowledge guide

**File**: `knowledge/deployment/vfrog-guide.md`

Complete rewrite required. The current guide references `pip install vfrog` and a Python SDK
that doesn't match the real CLI. New content:

- **Installation**: Download Go binary from GitHub releases (not pip)
- **Authentication**: Email/password login (not API key for CLI auth)
- **Context setup**: Organisation → Project → Object hierarchy
- **Two annotation/training paths**: Explain both vfrog SSAT and classic, with clear
  guidance on when each is appropriate
- **vfrog SSAT workflow**: Complete iteration-based annotation loop -- position as the
  simpler, recommended path for most users
- **Classic workflow**: How to use external annotation tools and train locally/on Modal --
  position as the full-control path for experienced users
- **Training**: `vfrog iteration train` (platform-managed) vs `yolo train` / `modal run`
- **Inference**: `vfrog inference` with API key
- **CROAK integration**: How `croak annotate --method vfrog|classic`,
  `croak train --provider local|modal|vfrog`, and `croak deploy vfrog|modal|edge` work
- **Limitations**: URL-only uploads, no annotation export, no deploy commands

#### 4.2 Update installer vfrog setup

**File**: `installer/src/utils/vfrog-setup.js`

Replace `fetch()` API calls with CLI invocations:

| Current function | New approach |
|-----------------|--------------|
| `validateVfrogKey()` | `vfrog config show --json` → check `authenticated` |
| `createVfrogProject()` | `vfrog projects create <name> --json` |
| `getVfrogProjectStatus()` | `vfrog projects list --json` + filter |
| `uploadToVfrog()` | `vfrog dataset_images upload <urls> --json` |
| `downloadFromVfrog()` | Remove (no export command in CLI) |

Add `checkVfrogCLI()`: executes `vfrog version`.

#### 4.3 Update installer doctor command

**File**: `installer/src/commands/doctor.js`

Add vfrog CLI checks:
- Binary available on PATH (`vfrog version`)
- Authentication status (`vfrog config show --json`)
- Context configured (organisation and project set)

#### 4.4 Update installer init command

**File**: `installer/src/commands/init.js`

Update vfrog check to verify:
1. CLI binary installed (not Python package)
2. User is logged in
3. Organisation and project are set

#### 4.5 Update Python `croak doctor` command

**File**: `src/croak/cli.py`

Add vfrog checks alongside existing Modal checks:
- `VfrogCLI.check_installed()` -- binary on PATH
- `VfrogCLI.check_authenticated()` -- logged in
- `VfrogCLI.get_config()` -- context configured

---

### Phase 5: Configuration, Dependencies, and Tests

#### 5.1 Update `pyproject.toml`

**File**: `pyproject.toml`

- **Remove** the assumed `vfrog` Python dependency (it's a Go binary, not a pip package)
- Check if `httpx` is used by any other module. If not, move to optional dependencies
- No new Python dependencies needed -- the CLI is invoked via subprocess

#### 5.2 Update `CroakConfig`

**File**: `src/croak/core/config.py`

Update `VfrogConfig` to track vfrog's context hierarchy:

```python
class VfrogConfig(BaseModel):
    api_key_env: str = "VFROG_API_KEY"           # For inference only
    cli_path: Optional[str] = None                # Custom vfrog binary path
    organisation_id: Optional[str] = None         # Cached org ID
    project_id: Optional[str] = None              # Cached project ID
    object_id: Optional[str] = None               # Cached object ID
    current_iteration_id: Optional[str] = None    # Active SSAT iteration
```

#### 5.3 Update pipeline state schema

**File**: `src/croak/core/state.py`

Extend state to track annotation source, provider choices, and vfrog-specific metadata:

```yaml
# In pipeline-state.yaml
annotation:
  source: "vfrog"  # or "classic"
  method: "ssat"   # or "manual" (for classic)
  format: "yolo"   # annotation format (classic path tracks this; vfrog manages internally)
  vfrog_iteration_id: "uuid"    # only when source == "vfrog"
  vfrog_object_id: "uuid"       # only when source == "vfrog"

training:
  provider: "local"  # or "modal" or "vfrog"
  # Classic path fields:
  architecture: "yolov8s"       # only when provider == "local" or "modal"
  experiment_id: "exp-001"      # only when provider == "local" or "modal"
  # vfrog path fields:
  vfrog_iteration_id: "uuid"    # only when provider == "vfrog"

deployment:
  target: "vfrog"  # or "modal" or "edge"
  vfrog_api_key_env: "VFROG_API_KEY"
```

**Validation rule**: If `training.provider == "vfrog"`, then `annotation.source` must be `"vfrog"`.
If `training.provider` is `"local"` or `"modal"`, then local annotation files must exist
(annotation source can be either -- vfrog annotations would need export support, or user
re-annotates locally).

#### 5.4 Add security tests for vfrog whitelist

**File**: `tests/test_security.py`

```python
def test_vfrog_command_allowed():
    """Verify whitelisted vfrog subcommands pass."""
    assert SecureRunner.is_command_allowed(['vfrog', 'projects', 'list'])
    assert SecureRunner.is_command_allowed(['vfrog', 'iterations', 'ssat'])
    assert SecureRunner.is_command_allowed(['vfrog', 'iteration', 'train'])
    assert SecureRunner.is_command_allowed(['vfrog', 'inference'])
    assert SecureRunner.is_command_allowed(['vfrog', 'config', 'show'])

def test_vfrog_dangerous_subcommand_blocked():
    """Verify unknown subcommands are blocked."""
    assert not SecureRunner.is_command_allowed(['vfrog', 'rm'])
    assert not SecureRunner.is_command_allowed(['vfrog', 'exec'])
```

#### 5.5 Add VfrogCLI unit tests

**File**: `tests/test_vfrog_cli.py` (new)

Mock `SecureRunner.run_vfrog()` to test:
- JSON output parsing for all methods
- Error handling for missing CLI binary
- Error handling for failed commands (non-zero exit)
- Correct argument construction (verify `--json` appended, flags correct)
- Auth check via `config show` parsing
- Context hierarchy enforcement (org before project, project before object)

---

### Phase 6: Deprecation and Cleanup

#### 6.1 Deprecate `VfrogClient`

Keep `VfrogClient` in `src/croak/integrations/vfrog.py` with a `DeprecationWarning` during
transition. Remove after one release cycle.

#### 6.2 Assess `httpx` dependency

Grep codebase for `httpx` usage outside of `VfrogClient`. If no other module uses it, move
from core dependencies to an optional group. If the inference test endpoint still needs an
HTTP client (for non-vfrog targets like Modal), keep it as optional.

---

## Sequencing and Dependencies

```
Phase 1 (Foundation)        Phase 2 (CLI Commands)          Phase 3 (Agent YAMLs)
  1.1 SecureRunner ────────> 2.1 croak vfrog group ────────> 3.1 Router YAML
  1.2 run_vfrog method       2.2 croak annotate (dual-mode)  3.2 Scout YAML
  1.3 VfrogCLI wrapper ───> 2.3 deploy restructure ────────> 3.3 Coach YAML
  1.4 __init__.py            2.4 train --provider             3.4 Judge YAML
                                                               3.5 Shipper YAML
                                                               3.6 Deployment steps
                                                               3.7 Annotation step

Phase 4 (Knowledge/Installer)   Phase 5 (Config/Tests)       Phase 6 (Cleanup)
  4.1 vfrog-guide.md rewrite     5.1 pyproject.toml            6.1 Deprecate VfrogClient
  4.2 vfrog-setup.js             5.2 CroakConfig               6.2 Assess httpx dep
  4.3 doctor.js                  5.3 Pipeline state schema
  4.4 init.js                    5.4 Security tests
  4.5 Python croak doctor        5.5 VfrogCLI unit tests
```

- Phases 1 → 2 are strictly sequential
- Phases 3, 4, 5 can proceed in parallel once Phase 2 is complete
- Phase 6 comes last, after a release cycle

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **URL-only image uploads** (v0.1 limitation) | High | Document workaround (host images on S3/GCS first); plan for local upload when vfrog CLI adds support; classic path avoids this entirely |
| **No annotation export from vfrog** | High | Classic path is the escape hatch -- users can annotate with any tool and train locally/Modal. vfrog path is self-contained (annotate + train on platform). Document that vfrog annotations can't currently be exported for local training. |
| **Users confused by two training paths** | Medium | Coach presents a clear decision framework: "Want simplicity? Use vfrog. Want control? Use classic." The `croak recommend --training-path` command helps users choose. |
| **Login requires interactive email/password** | Medium | Support `--email`/`--password` flags for CI/CD; cache auth tokens in `~/.vfrog/` |
| **vfrog CLI version changes** | Medium | Pin minimum version; test against specific releases; wrapper methods are the only coupling point |
| **Breaking change for `VfrogClient` importers** | Medium | Keep deprecated alias during transition (Phase 6.1) |
| **`croak deploy cloud` users who rely on Modal** | Medium | Rename to `croak deploy modal` with clear migration note |
| **vfrog context hierarchy** (org → project → object) adds setup friction | Low | `croak vfrog setup` wizard automates the multi-step flow |
| **No staging/production deploy distinction on vfrog** | Low | Accept that vfrog inference endpoint is "production" once trained; document this |
| **Classic path users miss vfrog benefits** | Low | Coach gently mentions vfrog advantages when users choose classic, but respects their choice without nagging |

---

## Files Changed Summary

### Modified (15 files)

| File | Change |
|------|--------|
| `src/croak/core/commands.py` | Add `vfrog` to whitelist, add `run_vfrog()` method |
| `src/croak/integrations/vfrog.py` | Replace `VfrogClient` with `VfrogCLI` (complete rewrite) |
| `src/croak/integrations/__init__.py` | Update exports |
| `src/croak/cli.py` | Add `croak vfrog` group, rewrite `croak annotate`, restructure `croak deploy`, add `--provider` to `croak train` |
| `src/croak/deployment/deployer.py` | Add `deploy_vfrog()` method (inference test) |
| `src/croak/core/config.py` | Expand `VfrogConfig` with org/project/object/iteration fields |
| `src/croak/core/state.py` | Add provider tracking to pipeline state |
| `agents/router/router.agent.yaml` | Add vfrog setup capability and commands |
| `agents/data/data.agent.yaml` | Rewrite annotation capability for SSAT; add vfrog CLI commands |
| `agents/training/training.agent.yaml` | Add vfrog training provider; add vfrog CLI commands |
| `agents/evaluation/evaluation.agent.yaml` | Add vfrog inference evaluation; add vfrog CLI commands |
| `agents/deployment/deployment.agent.yaml` | Split cloud_deployment into vfrog/modal; add vfrog CLI commands |
| `knowledge/deployment/vfrog-guide.md` | Complete rewrite for real CLI |
| `installer/src/utils/vfrog-setup.js` | Replace fetch calls with CLI invocations |
| `installer/src/commands/init.js` | Update vfrog detection (binary, not pip) |
| `pyproject.toml` | Remove assumed vfrog pip dependency; assess httpx |
| `workflows/data-preparation/steps/step-04-annotate.md` | Rewrite for SSAT workflow |

### Created (5 files)

| File | Purpose |
|------|---------|
| `workflows/model-deployment/steps/step-01-optimize.md` | Model optimization step |
| `workflows/model-deployment/steps/step-02-export.md` | Model export step |
| `workflows/model-deployment/steps/step-03-cloud.md` | vfrog inference verification step |
| `workflows/model-deployment/steps/step-04-edge.md` | Edge deployment step |
| `tests/test_vfrog_cli.py` | VfrogCLI wrapper unit tests |

### Deleted (after Phase 6)

| File | Reason |
|------|--------|
| `VfrogClient` class in `vfrog.py` | Replaced by `VfrogCLI`; deprecated first |

---

## Concept Mapping: Old Plan vs Real CLI

| Old Plan Assumed | Reality | Impact |
|-----------------|---------|--------|
| `pip install vfrog` | Go binary from GitHub releases | Installation docs, doctor checks |
| `VFROG_API_KEY` for all auth | Email/password login; API key only for inference | Auth flow, guardrails |
| `vfrog project create --name --task-type --classes` | `vfrog projects create "Name"` (title only) | VfrogCLI wrapper, annotate workflow |
| `vfrog upload --dir` (local files) | `vfrog dataset_images upload <urls>` (URLs only) | Major workflow change |
| `vfrog export --format yolo` | No export command | vfrog SSAT is self-contained; classic path uses external annotation tools with local export |
| `vfrog deploy create/staging/production` | No deploy commands; inference auto-available | Deploy workflow simplified |
| `vfrog status` | `vfrog config show` | Status checks |
| `vfrog auth verify` | `vfrog config show` → check `authenticated` | Auth validation |
| `vfrog test --endpoint` | `vfrog inference --api-key --image` | Inference testing |
| Traditional annotate → export → train (only path) | Two paths: vfrog SSAT (simple) OR classic annotate → export → train (full control) | Users choose; Coach recommends vfrog but supports both |
| Single project concept | Org → Project → Object → Iteration hierarchy | Context management |
| vfrog is required for all training | vfrog is one of three providers (local, Modal, vfrog) | Users are never locked in; classic path works without vfrog |
