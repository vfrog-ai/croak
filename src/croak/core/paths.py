"""Secure path handling for CROAK.

Provides path validation to prevent:
- Path traversal attacks (../)
- Arbitrary file access outside project
- Dangerous file types
- Oversized files
"""

from pathlib import Path
from typing import Optional, Set
import os


# Allowed file extensions by category
ALLOWED_IMAGES = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif'}
ALLOWED_MODELS = {'.pt', '.pth', '.onnx', '.engine', '.tflite', '.torchscript'}
ALLOWED_CONFIGS = {'.yaml', '.yml', '.json', '.toml'}
ALLOWED_LABELS = {'.txt', '.json', '.xml'}
ALLOWED_SCRIPTS = {'.py', '.sh'}

# Size limits (in bytes)
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_MODEL_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
MAX_CONFIG_SIZE = 1 * 1024 * 1024  # 1MB
MAX_LABEL_SIZE = 10 * 1024 * 1024  # 10MB


class PathValidationError(ValueError):
    """Raised when path validation fails."""
    pass


class PathValidator:
    """Validate and sanitize file paths.

    Security features:
    - Prevents path traversal attacks
    - Enforces file type restrictions
    - Enforces file size limits
    - Sanitizes filenames
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize path validator.

        Args:
            project_root: Root directory for the project. Defaults to cwd.
        """
        self.project_root = (project_root or Path.cwd()).resolve()

    def validate_within_project(self, path: Path) -> Path:
        """Ensure path is within project directory (prevent traversal).

        Args:
            path: Path to validate.

        Returns:
            Resolved absolute path.

        Raises:
            PathValidationError: If path is outside project directory.
        """
        # Resolve to absolute path
        if not path.is_absolute():
            path = self.project_root / path
        resolved = path.resolve()

        # Check if within project
        try:
            resolved.relative_to(self.project_root)
        except ValueError:
            raise PathValidationError(
                f"Path '{path}' is outside project directory. "
                f"All paths must be within '{self.project_root}'"
            )

        return resolved

    def validate_file_type(
        self,
        path: Path,
        allowed: Set[str],
        category: str = "file"
    ) -> Path:
        """Validate file extension.

        Args:
            path: Path to validate.
            allowed: Set of allowed extensions (with leading dot).
            category: Category name for error messages.

        Returns:
            The validated path.

        Raises:
            PathValidationError: If extension not allowed.
        """
        ext = path.suffix.lower()
        if ext not in allowed:
            raise PathValidationError(
                f"Invalid {category} type: '{ext}'. "
                f"Allowed: {', '.join(sorted(allowed))}"
            )
        return path

    def validate_file_size(
        self,
        path: Path,
        max_size: int,
        category: str = "file"
    ) -> Path:
        """Validate file size.

        Args:
            path: Path to validate.
            max_size: Maximum allowed size in bytes.
            category: Category name for error messages.

        Returns:
            The validated path.

        Raises:
            FileNotFoundError: If file doesn't exist.
            PathValidationError: If file exceeds size limit.
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        size = path.stat().st_size
        if size > max_size:
            size_mb = size / 1024 / 1024
            max_mb = max_size / 1024 / 1024
            raise PathValidationError(
                f"{category.title()} too large: {size_mb:.1f}MB. "
                f"Maximum: {max_mb:.1f}MB"
            )
        return path

    def validate_image(self, path: Path) -> Path:
        """Full validation for image files.

        Args:
            path: Path to validate.

        Returns:
            Validated absolute path.
        """
        path = Path(path)
        self.validate_within_project(path)
        self.validate_file_type(path, ALLOWED_IMAGES, "image")
        if path.exists():
            self.validate_file_size(path, MAX_IMAGE_SIZE, "image")
        return path.resolve()

    def validate_model(self, path: Path) -> Path:
        """Full validation for model files.

        Args:
            path: Path to validate.

        Returns:
            Validated absolute path.
        """
        path = Path(path)
        self.validate_within_project(path)
        self.validate_file_type(path, ALLOWED_MODELS, "model")
        if path.exists():
            self.validate_file_size(path, MAX_MODEL_SIZE, "model")
        return path.resolve()

    def validate_config(self, path: Path) -> Path:
        """Full validation for config files.

        Args:
            path: Path to validate.

        Returns:
            Validated absolute path.
        """
        path = Path(path)
        self.validate_within_project(path)
        self.validate_file_type(path, ALLOWED_CONFIGS, "config")
        if path.exists():
            self.validate_file_size(path, MAX_CONFIG_SIZE, "config")
        return path.resolve()

    def validate_label(self, path: Path) -> Path:
        """Full validation for label/annotation files.

        Args:
            path: Path to validate.

        Returns:
            Validated absolute path.
        """
        path = Path(path)
        self.validate_within_project(path)
        self.validate_file_type(path, ALLOWED_LABELS, "label")
        if path.exists():
            self.validate_file_size(path, MAX_LABEL_SIZE, "label")
        return path.resolve()

    def validate_directory(self, path: Path, must_exist: bool = True) -> Path:
        """Validate a directory path.

        Args:
            path: Path to validate.
            must_exist: Whether the directory must exist.

        Returns:
            Validated absolute path.

        Raises:
            PathValidationError: If path is outside project or not a directory.
        """
        path = Path(path)
        resolved = self.validate_within_project(path)

        if must_exist:
            if not resolved.exists():
                raise PathValidationError(f"Directory not found: {path}")
            if not resolved.is_dir():
                raise PathValidationError(f"Not a directory: {path}")

        return resolved

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove dangerous characters from filename.

        Args:
            filename: Original filename.

        Returns:
            Sanitized filename safe for filesystem use.
        """
        # Characters to remove completely
        dangerous = ['/', '\\', '\x00', ':', '*', '?', '"', '<', '>', '|']

        result = filename
        for char in dangerous:
            result = result.replace(char, '_')

        # Replace path traversal attempts
        result = result.replace('..', '_')

        # Remove leading dots (hidden files on Unix)
        result = result.lstrip('.')

        # Remove leading/trailing whitespace
        result = result.strip()

        # Limit length (most filesystems support 255)
        if len(result) > 200:
            name_part, ext = os.path.splitext(result)
            result = name_part[:200 - len(ext)] + ext

        # Ensure not empty
        if not result:
            result = "unnamed"

        return result

    @staticmethod
    def safe_join(base: Path, *parts: str) -> Path:
        """Safely join path components, preventing traversal.

        Args:
            base: Base directory path.
            *parts: Path components to join.

        Returns:
            Joined path that is guaranteed to be under base.

        Raises:
            PathValidationError: If result would be outside base.
        """
        # Sanitize each component
        safe_parts = [PathValidator.sanitize_filename(p) for p in parts]

        # Join and resolve
        result = base
        for part in safe_parts:
            result = result / part

        # Verify still under base
        try:
            result.resolve().relative_to(base.resolve())
        except ValueError:
            raise PathValidationError(
                f"Path traversal attempt detected: {'/'.join(parts)}"
            )

        return result


def safe_path(path: str, project_root: Optional[Path] = None) -> Path:
    """Convenience function for quick path validation.

    Args:
        path: Path string to validate.
        project_root: Optional project root directory.

    Returns:
        Validated absolute path.
    """
    validator = PathValidator(project_root)
    return validator.validate_within_project(Path(path))


def safe_image_path(path: str, project_root: Optional[Path] = None) -> Path:
    """Validate and return a safe image path.

    Args:
        path: Image path to validate.
        project_root: Optional project root directory.

    Returns:
        Validated absolute path.
    """
    validator = PathValidator(project_root)
    return validator.validate_image(Path(path))


def safe_model_path(path: str, project_root: Optional[Path] = None) -> Path:
    """Validate and return a safe model path.

    Args:
        path: Model path to validate.
        project_root: Optional project root directory.

    Returns:
        Validated absolute path.
    """
    validator = PathValidator(project_root)
    return validator.validate_model(Path(path))
