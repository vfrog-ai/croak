#!/usr/bin/env python
"""
CROAK - Computer Recognition Orchestration Agent Kit

This is a shim for compatibility with older pip versions and tools
that don't support pyproject.toml. The actual package configuration
is in pyproject.toml.

For installation:
    pip install -e .           # Standard installation
    pip install -e ".[dev]"    # Development installation
"""

from setuptools import setup

if __name__ == "__main__":
    setup()
