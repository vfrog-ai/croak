"""
CROAK - Computer Recognition Orchestration Agent Kit

An agentic framework for object detection model development.
"""

__version__ = "1.0.0-alpha"
__author__ = "vfrog.ai"

from croak.core.state import PipelineState
from croak.core.config import CroakConfig

__all__ = [
    "__version__",
    "PipelineState",
    "CroakConfig",
]
