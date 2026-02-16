"""vfrog.ai platform integration via CLI.

The vfrog CLI is a Go binary that manages its own auth state in ~/.vfrog/.
Authentication is email/password via Supabase, NOT API-key based for CLI auth.
VFROG_API_KEY is only used for the 'inference' command.

Context hierarchy (must be set in order):
1. organisation_id (required for all commands)
2. project_id (required for most commands)
3. object_id (required for iteration commands)
"""

import re
import warnings
from typing import Optional, List, Dict, Any

from pydantic import BaseModel

from croak.core.commands import SecureRunner


def _sanitize_arg(value: str, name: str, allow_path: bool = False) -> str:
    """Prevent argument injection by rejecting values that look like flags.

    Args:
        value: The argument value to sanitize.
        name: Name of the argument (for error messages).
        allow_path: If True, allow file system paths (which may start with / or drive letter).
    """
    if value.startswith('-'):
        raise ValueError(f"{name} must not start with '-': {value!r}")
    return value


def _sanitize_url(url: str) -> str:
    """Validate URL format and prevent argument injection."""
    if url.startswith('-'):
        raise ValueError(f"URL must not start with '-': {url!r}")
    if not re.match(r'^https?://', url):
        raise ValueError(f"URL must use http:// or https:// scheme: {url!r}")
    return url


# --- Pydantic Models (matching real vfrog data structures) ---


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


# --- CLI Wrapper ---


class VfrogCLI:
    """Wrapper around vfrog CLI tool (Go binary).

    All methods are static -- the CLI manages its own auth state in ~/.vfrog/.
    Every method that queries data uses --json for machine-parseable output.
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
        """Login to vfrog platform.

        Args:
            email: Account email address.
            password: Account password.

        Returns:
            Dict with success status and output.
        """
        return SecureRunner.run_vfrog(
            ['login', '--email', email, '--password', password],
            json_output=False,
        )

    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get current CLI config (org, project, object, auth status)."""
        return SecureRunner.run_vfrog(['config', 'show'])

    @staticmethod
    def set_organisation(org_id: str) -> Dict[str, Any]:
        """Set the active organisation. Clears project_id automatically.

        Args:
            org_id: Organisation UUID.
        """
        return SecureRunner.run_vfrog(
            ['config', 'set', 'organisation', '--organisation_id', org_id]
        )

    @staticmethod
    def set_project(project_id: str) -> Dict[str, Any]:
        """Set the active project.

        Args:
            project_id: Project UUID.
        """
        return SecureRunner.run_vfrog(
            ['config', 'set', 'project', '--project_id', project_id]
        )

    @staticmethod
    def set_object(object_id: str) -> Dict[str, Any]:
        """Set the active object (product image).

        Args:
            object_id: Object UUID.
        """
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
        """Create a new project in the active organisation.

        Args:
            name: Project title.
        """
        return SecureRunner.run_vfrog(['projects', 'create', name])

    # --- Dataset Images ---

    @staticmethod
    def upload_dataset_images(
        urls: Optional[List[str]] = None,
        file_path: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload dataset images from URLs, a local file, or a directory.

        Args:
            urls: List of image URLs to upload.
            file_path: Local image file path to upload.
            directory: Local directory of images to upload.
        """
        args = ['dataset_images', 'upload']
        if directory:
            args.extend(['--dir', _sanitize_arg(directory, 'directory', allow_path=True)])
        elif file_path:
            args.extend(['--file', _sanitize_arg(file_path, 'file_path', allow_path=True)])
        elif urls:
            validated = [_sanitize_url(u) for u in urls]
            args.extend(validated)
        else:
            raise ValueError("One of urls, file_path, or directory must be provided")
        return SecureRunner.run_vfrog(args, timeout=600)

    @staticmethod
    def list_dataset_images() -> Dict[str, Any]:
        """List dataset images in the active project."""
        return SecureRunner.run_vfrog(['dataset_images', 'list'])

    @staticmethod
    def delete_dataset_image(image_id: str) -> Dict[str, Any]:
        """Delete a dataset image by ID.

        Args:
            image_id: Dataset image UUID.
        """
        return SecureRunner.run_vfrog(
            ['dataset_images', 'delete', '--dataset_image_id', _sanitize_arg(image_id, 'image_id')]
        )

    # --- Objects (Product Images) ---

    @staticmethod
    def create_object(
        url: Optional[str] = None,
        label: str = '',
        external_id: str = '',
        file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new object (product image) from a URL or local file.

        Args:
            url: URL of the product/reference image.
            label: Optional label for the object.
            external_id: Optional external identifier.
            file_path: Local file path of the product image.
        """
        args = ['objects', 'create']
        if file_path:
            args.extend(['--file', _sanitize_arg(file_path, 'file_path', allow_path=True)])
        elif url:
            args.append(_sanitize_url(url))
        else:
            raise ValueError("One of url or file_path must be provided")
        if label:
            args.extend(['--label', _sanitize_arg(label, 'label')])
        if external_id:
            args.extend(['--external_id', _sanitize_arg(external_id, 'external_id')])
        return SecureRunner.run_vfrog(args)

    @staticmethod
    def list_objects() -> Dict[str, Any]:
        """List objects in the active project."""
        return SecureRunner.run_vfrog(['objects', 'list'])

    @staticmethod
    def delete_object(object_id: str) -> Dict[str, Any]:
        """Delete an object by ID.

        Args:
            object_id: Object UUID.
        """
        return SecureRunner.run_vfrog(
            ['objects', 'delete', '--object_id', _sanitize_arg(object_id, 'object_id')]
        )

    # --- Iterations (SSAT Loop) ---

    @staticmethod
    def list_iterations(object_id: Optional[str] = None) -> Dict[str, Any]:
        """List iterations for an object.

        Args:
            object_id: Optional object UUID to filter by.
        """
        args = ['iterations', 'list']
        if object_id:
            args.extend(['--object_id', _sanitize_arg(object_id, 'object_id')])
        return SecureRunner.run_vfrog(args)

    @staticmethod
    def create_iteration(
        object_id: str,
        random_count: int = 20,
    ) -> Dict[str, Any]:
        """Create a new iteration (selects random dataset images).

        Args:
            object_id: Object UUID to create iteration for.
            random_count: Number of random dataset images to include.
        """
        return SecureRunner.run_vfrog(
            ['iterations', 'create', _sanitize_arg(object_id, 'object_id'), '--random', str(random_count)]
        )

    @staticmethod
    def run_ssat(
        iteration_id: str,
        random_count: int = 0,
        restart: bool = False,
        industry: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start SSAT auto-annotation for an iteration.

        - Iteration 1: Uses cutout extraction and matching
        - Iteration 2+: Uses trained model inference

        Default image counts by iteration: #1=20, #2=40, #3+=80.
        Use random_count to override with random selection from project.

        Args:
            iteration_id: Iteration UUID.
            random_count: Override random image count (0 = use defaults).
            restart: Whether to restart the SSAT process.
            industry: Optional industry hint for better annotation context.
        """
        args = ['iterations', 'ssat', '--iteration_id', _sanitize_arg(iteration_id, 'iteration_id')]
        if random_count > 0:
            args.extend(['--random', str(random_count)])
        if restart:
            args.append('--restart')
        if industry:
            args.extend(['--industry', _sanitize_arg(industry, 'industry')])
        return SecureRunner.run_vfrog(args, timeout=600)

    @staticmethod
    def get_halo_url(iteration_id: str) -> Dict[str, Any]:
        """Get HALO (Human Assisted Labelling of Objects) URL for an iteration.

        Args:
            iteration_id: Iteration UUID.
        """
        return SecureRunner.run_vfrog(
            ['iterations', 'halo', '--iteration_id', _sanitize_arg(iteration_id, 'iteration_id')]
        )

    @staticmethod
    def next_iteration(iteration_id: str) -> Dict[str, Any]:
        """Create the next iteration from the current one.

        Args:
            iteration_id: Current iteration UUID.
        """
        return SecureRunner.run_vfrog(
            ['iterations', 'next', '--iteration_id', _sanitize_arg(iteration_id, 'iteration_id')]
        )

    @staticmethod
    def restart_iteration(iteration_id: str) -> Dict[str, Any]:
        """Restart an iteration (delete and recreate).

        Args:
            iteration_id: Iteration UUID to restart.
        """
        return SecureRunner.run_vfrog(
            ['iterations', 'restart', '--iteration_id', _sanitize_arg(iteration_id, 'iteration_id')]
        )

    @staticmethod
    def get_iteration_status(iteration_id: str, watch: bool = False) -> Dict[str, Any]:
        """Get the status of an iteration.

        Args:
            iteration_id: Iteration UUID.
            watch: If True, poll until iteration completes (longer timeout).
        """
        args = ['iterations', 'status', '--iteration_id', _sanitize_arg(iteration_id, 'iteration_id')]
        if watch:
            args.append('--watch')
        return SecureRunner.run_vfrog(args, timeout=600 if watch else 300)

    @staticmethod
    def deploy_iteration(iteration_id: str) -> Dict[str, Any]:
        """Deploy a trained iteration model.

        Args:
            iteration_id: Iteration UUID (must have completed training).
        """
        return SecureRunner.run_vfrog(
            ['iterations', 'deploy', '--iteration_id', _sanitize_arg(iteration_id, 'iteration_id')]
        )

    @staticmethod
    def get_annotations(iteration_id: str) -> Dict[str, Any]:
        """Get annotations for an iteration.

        Args:
            iteration_id: Iteration UUID.
        """
        return SecureRunner.run_vfrog(
            ['iterations', 'annotations', '--iteration_id', _sanitize_arg(iteration_id, 'iteration_id')]
        )

    @staticmethod
    def export_yolo(iteration_id: str, output_dir: str = "./export") -> Dict[str, Any]:
        """Export iteration annotations in YOLO format.

        Args:
            iteration_id: Iteration UUID.
            output_dir: Output directory for exported files.
        """
        return SecureRunner.run_vfrog(
            ['export', 'yolo', '--iteration_id', _sanitize_arg(iteration_id, 'iteration_id'),
             '--output', output_dir],
            timeout=600,
        )

    # --- Training (on vfrog platform) ---

    @staticmethod
    def train_iteration(iteration_id: str) -> Dict[str, Any]:
        """Train a model for an iteration on vfrog's infrastructure.

        Args:
            iteration_id: Iteration UUID (must have completed SSAT + HALO review).
        """
        return SecureRunner.run_vfrog(
            ['iterations', 'train', '--iteration_id', _sanitize_arg(iteration_id, 'iteration_id')],
            timeout=3600,
        )

    # --- Inference ---

    @staticmethod
    def run_inference(
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run inference on an image using a trained vfrog model.

        Requires VFROG_API_KEY env var or explicit api_key parameter.

        Args:
            image_path: Local image file path.
            image_url: Image URL.
            api_key: API key (falls back to VFROG_API_KEY env var).
        """
        args = ['inference']
        if api_key:
            args.extend(['--api-key', api_key])
        if image_path:
            args.extend(['--image', _sanitize_arg(image_path, 'image_path')])
        elif image_url:
            args.extend(['--image_url', _sanitize_url(image_url)])
        return SecureRunner.run_vfrog(args)


# --- Deprecated alias ---


class VfrogClient:
    """Deprecated: Use VfrogCLI instead.

    The old VfrogClient used httpx to call the vfrog REST API directly.
    The new VfrogCLI wraps the vfrog Go binary via SecureRunner.
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "VfrogClient is deprecated and will be removed in a future release. "
            "Use VfrogCLI instead, which wraps the vfrog CLI binary.",
            DeprecationWarning,
            stacklevel=2,
        )
        raise NotImplementedError(
            "VfrogClient has been replaced by VfrogCLI. "
            "Install the vfrog CLI binary and use VfrogCLI static methods instead. "
            "See: https://github.com/vfrog-ai/vfrog-cli/releases"
        )
