"""Tests for CROAK security modules."""

import pytest
from pathlib import Path
import tempfile
import os

from croak.core.secrets import SecretsManager
from croak.core.paths import PathValidator, PathSecurityError
from croak.core.commands import SecureRunner, CommandSecurityError


class TestSecretsManager:
    """Test SecretsManager class."""

    def test_redact_vfrog_key(self):
        """Test redacting vfrog API keys."""
        text = "Using key vfrog_abc123def456ghi789jkl012mno345"
        redacted = SecretsManager.redact(text)
        assert "vfrog_" not in redacted
        assert "[VFROG_API_KEY]" in redacted

    def test_redact_modal_token(self):
        """Test redacting Modal tokens."""
        text = "Token: sk-abc123def456ghi789jkl012mno345pqr678"
        redacted = SecretsManager.redact(text)
        assert "sk-" not in redacted
        assert "[MODAL_TOKEN]" in redacted

    def test_redact_preserves_normal_text(self):
        """Test that normal text is preserved."""
        text = "This is a normal message with no secrets"
        redacted = SecretsManager.redact(text)
        assert redacted == text

    def test_redact_multiple_secrets(self):
        """Test redacting multiple secrets."""
        text = "Key1: vfrog_abc123def456ghi789jkl012mno345 Key2: sk-xyz789abc123def456ghi"
        redacted = SecretsManager.redact(text)
        assert "vfrog_" not in redacted
        assert "sk-" not in redacted

    def test_get_vfrog_key_from_env(self):
        """Test getting vfrog key from environment."""
        original = os.environ.get("VFROG_API_KEY")
        try:
            os.environ["VFROG_API_KEY"] = "test_key_123"
            key = SecretsManager.get_vfrog_key()
            assert key == "test_key_123"
        finally:
            if original:
                os.environ["VFROG_API_KEY"] = original
            else:
                os.environ.pop("VFROG_API_KEY", None)

    def test_get_vfrog_key_missing(self):
        """Test getting vfrog key when not set."""
        original = os.environ.get("VFROG_API_KEY")
        try:
            os.environ.pop("VFROG_API_KEY", None)
            key = SecretsManager.get_vfrog_key()
            assert key is None
        finally:
            if original:
                os.environ["VFROG_API_KEY"] = original


class TestPathValidator:
    """Test PathValidator class."""

    def test_validate_within_project(self):
        """Test validating path within project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = PathValidator(Path(tmpdir))
            subpath = Path(tmpdir) / "subdir" / "file.txt"

            validated = validator.validate_within_project(subpath)
            assert validated.is_relative_to(tmpdir)

    def test_validate_path_traversal_blocked(self):
        """Test that path traversal is blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = PathValidator(Path(tmpdir))

            # Try to escape with ..
            malicious_path = Path(tmpdir) / ".." / ".." / "etc" / "passwd"

            with pytest.raises(PathSecurityError):
                validator.validate_within_project(malicious_path)

    def test_validate_image_valid(self):
        """Test validating valid image files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = PathValidator(Path(tmpdir))

            # Create a fake image file
            image_path = Path(tmpdir) / "test.jpg"
            image_path.write_bytes(b'\xff\xd8\xff\xe0')  # JPEG magic bytes

            validated = validator.validate_image(image_path)
            assert validated == image_path

    def test_validate_image_invalid_extension(self):
        """Test rejecting invalid image extensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = PathValidator(Path(tmpdir))

            text_path = Path(tmpdir) / "test.txt"
            text_path.write_text("not an image")

            with pytest.raises(PathSecurityError):
                validator.validate_image(text_path)

    def test_validate_data_yaml(self):
        """Test validating data.yaml files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = PathValidator(Path(tmpdir))

            yaml_path = Path(tmpdir) / "data.yaml"
            yaml_path.write_text("train: ./train\nval: ./val\nnames: [cat, dog]")

            validated = validator.validate_data_yaml(yaml_path)
            assert validated == yaml_path


class TestSecureRunner:
    """Test SecureRunner class."""

    def test_run_allowed_command(self):
        """Test running allowed commands."""
        result = SecureRunner.run(["python", "--version"])
        assert result.returncode == 0

    def test_run_blocked_command(self):
        """Test blocking disallowed commands."""
        with pytest.raises(CommandSecurityError):
            SecureRunner.run(["rm", "-rf", "/"])

    def test_run_blocked_subcommand(self):
        """Test blocking disallowed subcommands."""
        with pytest.raises(CommandSecurityError):
            SecureRunner.run(["git", "push", "--force"])

    def test_run_with_timeout(self):
        """Test command timeout."""
        # This should complete quickly
        result = SecureRunner.run(["python", "-c", "print('hello')"], timeout=5)
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_run_captures_output(self):
        """Test that output is captured."""
        result = SecureRunner.run(["python", "-c", "print('test output')"])
        assert "test output" in result.stdout

    def test_run_with_cwd(self):
        """Test running command in specific directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = SecureRunner.run(
                ["python", "-c", "import os; print(os.getcwd())"],
                cwd=Path(tmpdir)
            )
            assert tmpdir in result.stdout
