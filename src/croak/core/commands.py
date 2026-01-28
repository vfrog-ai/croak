"""Secure subprocess execution for CROAK.

Provides secure command execution with:
- Command whitelist enforcement
- Output redaction for secrets
- Timeout protection
- Working directory validation
"""

import subprocess
import shlex
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from croak.core.paths import safe_path, PathValidator
from croak.core.secrets import SecretsManager

logger = logging.getLogger(__name__)


class CommandExecutionError(Exception):
    """Raised when command execution fails."""
    pass


class CommandNotAllowedError(Exception):
    """Raised when a command is not in the whitelist."""
    pass


class SecureRunner:
    """Execute subprocess commands securely.

    Security features:
    - Command whitelist enforcement
    - Script path validation
    - Output redaction in logs
    - Timeout protection
    - Working directory validation
    """

    # Allowed commands whitelist with permitted subcommands
    # Format: {base_command: [allowed_subcommands]} or {base_command: None} for any
    ALLOWED_COMMANDS = {
        # Modal.com
        'modal': ['run', 'token', 'volume', 'app', 'deploy', '--version'],
        # Python
        'python': None,  # Any Python command allowed
        'python3': None,
        # Pip
        'pip': ['install', 'list', 'show', 'freeze', '--version'],
        'pip3': ['install', 'list', 'show', 'freeze', '--version'],
        # UV (fast pip alternative)
        'uv': ['pip', 'venv', 'run', '--version'],
        # System info
        'nvidia-smi': None,  # Any nvidia-smi command
        'nvcc': ['--version'],
        # Git (read-only operations)
        'git': ['--version', 'status', 'log', 'diff', 'rev-parse'],
        # YOLO/Ultralytics
        'yolo': None,  # Any YOLO command
    }

    # Default timeout in seconds
    DEFAULT_TIMEOUT = 300  # 5 minutes

    # Maximum timeout for long-running operations
    MAX_TIMEOUT = 14400  # 4 hours (for training)

    @classmethod
    def is_command_allowed(cls, cmd: List[str]) -> bool:
        """Check if a command is in the whitelist.

        Args:
            cmd: Command as list of arguments.

        Returns:
            True if command is allowed.
        """
        if not cmd:
            return False

        # Get base command name (handle full paths)
        base_cmd = Path(cmd[0]).name

        if base_cmd not in cls.ALLOWED_COMMANDS:
            return False

        # Check subcommand if restrictions exist
        allowed_sub = cls.ALLOWED_COMMANDS[base_cmd]
        if allowed_sub is not None and len(cmd) > 1:
            # Check if first argument is an allowed subcommand
            if cmd[1] not in allowed_sub:
                # Allow if it's a flag that starts with -
                if not cmd[1].startswith('-'):
                    return False

        return True

    @classmethod
    def validate_command(cls, cmd: List[str]) -> None:
        """Validate command against whitelist.

        Args:
            cmd: Command to validate.

        Raises:
            CommandNotAllowedError: If command not allowed.
        """
        if not cmd:
            raise CommandNotAllowedError("Empty command")

        base_cmd = Path(cmd[0]).name

        if not cls.is_command_allowed(cmd):
            allowed_sub = cls.ALLOWED_COMMANDS.get(base_cmd)
            if base_cmd not in cls.ALLOWED_COMMANDS:
                raise CommandNotAllowedError(
                    f"Command not allowed: '{base_cmd}'. "
                    f"Allowed commands: {', '.join(sorted(cls.ALLOWED_COMMANDS.keys()))}"
                )
            else:
                raise CommandNotAllowedError(
                    f"Subcommand not allowed: '{base_cmd} {cmd[1] if len(cmd) > 1 else ''}'. "
                    f"Allowed for {base_cmd}: {', '.join(allowed_sub or ['any'])}"
                )

    @classmethod
    def run(
        cls,
        cmd: List[str],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        capture_output: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        check: bool = True,
        validate: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run command securely.

        Args:
            cmd: Command as list of arguments.
            cwd: Working directory.
            env: Environment variables (merged with current env).
            capture_output: Whether to capture stdout/stderr.
            timeout: Timeout in seconds.
            check: Whether to raise on non-zero exit.
            validate: Whether to validate against whitelist.

        Returns:
            CompletedProcess with results.

        Raises:
            CommandNotAllowedError: If command not in whitelist.
            CommandExecutionError: If command fails and check=True.
            TimeoutError: If command times out.
        """
        # Validate command
        if validate:
            cls.validate_command(cmd)

        # Validate working directory
        if cwd:
            cwd = safe_path(str(cwd))

        # Clamp timeout
        timeout = min(timeout, cls.MAX_TIMEOUT)

        # Prepare environment
        run_env = None
        if env:
            import os
            run_env = os.environ.copy()
            run_env.update(env)

        # Log command (redacted)
        redacted_cmd = [SecretsManager.redact(str(c)) for c in cmd]
        logger.info(f"Running: {' '.join(redacted_cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                env=run_env,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
            )

            # Log result (redacted)
            if result.stdout:
                logger.debug(f"stdout: {SecretsManager.redact(result.stdout[:500])}")
            if result.stderr:
                logger.debug(f"stderr: {SecretsManager.redact(result.stderr[:500])}")

            if check and result.returncode != 0:
                raise CommandExecutionError(
                    f"Command failed with exit code {result.returncode}: "
                    f"{SecretsManager.redact(result.stderr or result.stdout or 'No output')}"
                )

            return result

        except subprocess.TimeoutExpired as e:
            raise TimeoutError(
                f"Command timed out after {timeout}s: {cmd[0]}"
            ) from e

    @classmethod
    def run_python(
        cls,
        script_path: str,
        args: Optional[List[str]] = None,
        cwd: Optional[Path] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> subprocess.CompletedProcess:
        """Run a Python script securely.

        Args:
            script_path: Path to Python script.
            args: Additional arguments.
            cwd: Working directory.
            timeout: Timeout in seconds.

        Returns:
            CompletedProcess with results.
        """
        # Validate script path
        script = safe_path(script_path)
        if not script.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        if script.suffix != '.py':
            raise ValueError("Script must be a .py file")

        cmd = ['python', str(script)]
        if args:
            cmd.extend(args)

        return cls.run(cmd, cwd=cwd, timeout=timeout)

    @classmethod
    def run_modal(
        cls,
        script_path: str,
        detached: bool = False,
        timeout: int = MAX_TIMEOUT,
    ) -> Dict[str, Any]:
        """Run Modal script securely.

        Args:
            script_path: Path to Modal script.
            detached: Whether to run in background.
            timeout: Timeout in seconds.

        Returns:
            Dict with success status and output.
        """
        # Validate script path
        script = safe_path(script_path)
        if not script.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        if script.suffix != '.py':
            raise ValueError("Modal scripts must be .py files")

        cmd = ['modal', 'run']
        if detached:
            cmd.append('--detach')
        cmd.append(str(script))

        try:
            result = cls.run(cmd, capture_output=not detached, timeout=timeout)
            return {
                'success': result.returncode == 0,
                'output': result.stdout if not detached else 'Running in background',
                'error': result.stderr if result.returncode != 0 else None,
            }
        except CommandExecutionError as e:
            return {
                'success': False,
                'output': None,
                'error': str(e),
            }

    @classmethod
    def check_command_available(cls, command: str) -> bool:
        """Check if a command is available on the system.

        Args:
            command: Command name to check.

        Returns:
            True if command is available.
        """
        import shutil
        return shutil.which(command) is not None

    @classmethod
    def get_python_version(cls) -> Optional[str]:
        """Get Python version string.

        Returns:
            Version string like "3.11.0" or None if failed.
        """
        try:
            result = cls.run(['python', '--version'], capture_output=True, check=False)
            if result.returncode == 0:
                return result.stdout.strip().replace('Python ', '')
        except Exception:
            pass
        return None

    @classmethod
    def check_gpu_available(cls) -> Dict[str, Any]:
        """Check if NVIDIA GPU is available.

        Returns:
            Dict with gpu info or None if not available.
        """
        if not cls.check_command_available('nvidia-smi'):
            return {'available': False, 'reason': 'nvidia-smi not found'}

        try:
            result = cls.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,driver_version',
                 '--format=csv,noheader'],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpus = []
                for line in lines:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 3:
                        gpus.append({
                            'name': parts[0],
                            'memory': parts[1],
                            'driver': parts[2],
                        })
                return {'available': True, 'gpus': gpus}
            else:
                return {'available': False, 'reason': result.stderr}
        except Exception as e:
            return {'available': False, 'reason': str(e)}
