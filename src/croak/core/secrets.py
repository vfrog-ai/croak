"""Secure secrets management for CROAK."""

import os
import re
from typing import Optional
from functools import lru_cache


class SecretsManager:
    """Manage API keys and sensitive credentials.

    Security principles:
    - Never store secrets in files
    - Always read from environment variables
    - Redact secrets in all logs and outputs
    - Validate format before use
    """

    # Patterns to detect secrets in logs
    SECRET_PATTERNS = [
        (r'vfrog_[a-zA-Z0-9]{32}', 'VFROG_API_KEY'),
        (r'sk-[a-zA-Z0-9]{32,}', 'MODAL_TOKEN'),
        (r'wandb_[a-zA-Z0-9]{32,}', 'WANDB_API_KEY'),
        (r'[a-zA-Z0-9]{32,}', 'GENERIC_KEY'),
    ]

    # Environment variable mappings
    ENV_MAP = {
        'vfrog': 'VFROG_API_KEY',
        'modal': 'MODAL_TOKEN_ID',
        'wandb': 'WANDB_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
    }

    @staticmethod
    def get_vfrog_key() -> Optional[str]:
        """Get vfrog API key from environment only.

        Returns:
            API key if set and valid, None otherwise.

        Raises:
            ValueError: If key is set but invalid format.
        """
        key = os.environ.get("VFROG_API_KEY")
        if key:
            SecretsManager.validate_vfrog_key(key)
        return key

    @staticmethod
    def validate_vfrog_key(key: str) -> bool:
        """Validate vfrog API key format.

        Args:
            key: The API key to validate.

        Returns:
            True if valid.

        Raises:
            ValueError: If key format is invalid.
        """
        if not key:
            raise ValueError("VFROG_API_KEY cannot be empty")
        if len(key) < 20:
            raise ValueError(
                "Invalid VFROG_API_KEY format: key too short. "
                "Get your key at https://vfrog.ai/settings/api"
            )
        # Check for common mistakes
        if key.startswith("sk-"):
            raise ValueError(
                "This looks like an OpenAI key, not a vfrog key. "
                "Get your vfrog key at https://vfrog.ai/settings/api"
            )
        return True

    @staticmethod
    def get_modal_token() -> Optional[str]:
        """Get Modal.com token from environment.

        Returns:
            Token ID if set, None otherwise.
        """
        return os.environ.get("MODAL_TOKEN_ID")

    @staticmethod
    def get_wandb_key() -> Optional[str]:
        """Get Weights & Biases API key from environment.

        Returns:
            API key if set, None otherwise.
        """
        return os.environ.get("WANDB_API_KEY")

    @staticmethod
    def redact(text: str) -> str:
        """Redact any secrets from text for safe logging.

        Args:
            text: Text that may contain secrets.

        Returns:
            Text with secrets redacted.
        """
        if not text:
            return text

        result = text

        # Redact known patterns
        for pattern, name in SecretsManager.SECRET_PATTERNS:
            result = re.sub(
                pattern,
                f'[REDACTED:{name}]',
                result,
                flags=re.IGNORECASE
            )

        # Also redact anything that looks like a long alphanumeric key
        # but preserve short identifiers and common words
        def redact_long_keys(match):
            value = match.group()
            # Skip if it looks like a file path component or common word
            if '/' in value or '\\' in value:
                return value
            if len(value) > 20:
                return f"{value[:4]}...{value[-4:]}"
            return value

        result = re.sub(
            r'\b[a-zA-Z0-9_-]{24,}\b',
            redact_long_keys,
            result
        )

        return result

    @staticmethod
    def redact_key(key: str) -> str:
        """Redact a single key for display.

        Args:
            key: The key to redact.

        Returns:
            Redacted key showing only first and last 4 chars.
        """
        if not key:
            return '***'
        if len(key) < 8:
            return '***'
        return f"{key[:4]}...{key[-4:]}"

    @staticmethod
    def check_environment() -> dict:
        """Check which secrets are configured.

        Returns:
            Dict with status of each secret.
        """
        return {
            'vfrog': bool(os.environ.get("VFROG_API_KEY")),
            'modal': bool(os.environ.get("MODAL_TOKEN_ID")),
            'wandb': bool(os.environ.get("WANDB_API_KEY")),
        }

    @staticmethod
    def get_setup_instructions(service: str) -> str:
        """Get setup instructions for a service.

        Args:
            service: Service name (vfrog, modal, wandb).

        Returns:
            Setup instructions as a string.
        """
        instructions = {
            'vfrog': (
                "To set up vfrog.ai:\n"
                "1. Sign up at https://vfrog.ai\n"
                "2. Go to Settings > API Keys\n"
                "3. Create a new API key\n"
                "4. Run: export VFROG_API_KEY=your_key_here"
            ),
            'modal': (
                "To set up Modal.com:\n"
                "1. Sign up at https://modal.com\n"
                "2. Install: pip install modal\n"
                "3. Run: modal token new\n"
                "This will automatically configure your token."
            ),
            'wandb': (
                "To set up Weights & Biases:\n"
                "1. Sign up at https://wandb.ai\n"
                "2. Go to Settings > API Keys\n"
                "3. Copy your API key\n"
                "4. Run: export WANDB_API_KEY=your_key_here\n"
                "   Or: wandb login"
            ),
        }
        return instructions.get(service, f"Unknown service: {service}")


def get_secret(name: str) -> Optional[str]:
    """Get a secret by name. Never stores, always from env.

    Args:
        name: Secret name (vfrog, modal, wandb) or env var name.

    Returns:
        Secret value if set, None otherwise.
    """
    env_var = SecretsManager.ENV_MAP.get(name.lower(), name.upper())
    return os.environ.get(env_var)


def require_secret(name: str, purpose: str = "") -> str:
    """Get a secret, raising an error if not set.

    Args:
        name: Secret name.
        purpose: Description of why the secret is needed.

    Returns:
        Secret value.

    Raises:
        ValueError: If secret is not set.
    """
    value = get_secret(name)
    if not value:
        purpose_msg = f" for {purpose}" if purpose else ""
        raise ValueError(
            f"{name.upper()} is required{purpose_msg}. "
            f"{SecretsManager.get_setup_instructions(name.lower())}"
        )
    return value
