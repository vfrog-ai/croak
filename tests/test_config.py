"""Tests for CROAK configuration."""

import pytest
from pathlib import Path
import tempfile
import yaml

from croak.core.config import CroakConfig, TrainingConfig, ComputeConfig


class TestCroakConfig:
    """Test CroakConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CroakConfig()

        assert config.version == "1.0"
        assert config.task_type == "detection"
        assert config.training.architecture == "yolov8s"
        assert config.compute.provider == "modal"

    def test_save_and_load(self):
        """Test saving and loading config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            # Create and save config
            config = CroakConfig(
                project_name="test-project",
                task_type="detection",
            )
            config.save(config_path)

            # Load and verify
            loaded = CroakConfig.load(config_path)
            assert loaded.project_name == "test-project"
            assert loaded.task_type == "detection"

    def test_nested_config(self):
        """Test nested configuration objects."""
        config = CroakConfig(
            training=TrainingConfig(
                architecture="yolov8m",
                epochs=200,
            ),
            compute=ComputeConfig(
                provider="local",
                gpu_type="RTX3080",
            ),
        )

        assert config.training.architecture == "yolov8m"
        assert config.training.epochs == 200
        assert config.compute.provider == "local"

    def test_find_config_not_found(self):
        """Test finding config when none exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = CroakConfig.find_config(Path(tmpdir))
            assert result is None

    def test_find_config_found(self):
        """Test finding config in directory hierarchy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .croak directory with config
            croak_dir = Path(tmpdir) / ".croak"
            croak_dir.mkdir()
            config_path = croak_dir / "config.yaml"

            config = CroakConfig(project_name="test")
            config.save(config_path)

            # Find from subdirectory
            subdir = Path(tmpdir) / "sub" / "dir"
            subdir.mkdir(parents=True)

            found = CroakConfig.find_config(subdir)
            assert found == config_path


class TestTrainingConfig:
    """Test TrainingConfig class."""

    def test_defaults(self):
        """Test default training values."""
        config = TrainingConfig()

        assert config.framework == "ultralytics"
        assert config.architecture == "yolov8s"
        assert config.epochs == 100
        assert config.batch_size == 16
        assert config.image_size == 640
        assert config.patience == 20

    def test_custom_values(self):
        """Test custom training values."""
        config = TrainingConfig(
            architecture="yolov8n",
            epochs=50,
            batch_size=32,
        )

        assert config.architecture == "yolov8n"
        assert config.epochs == 50
        assert config.batch_size == 32


class TestComputeConfig:
    """Test ComputeConfig class."""

    def test_defaults(self):
        """Test default compute values."""
        config = ComputeConfig()

        assert config.provider == "modal"
        assert config.gpu_type == "T4"
        assert config.timeout_hours == 4

    def test_modal_config(self):
        """Test Modal compute configuration."""
        config = ComputeConfig(
            provider="modal",
            gpu_type="A10G",
            timeout_hours=8,
        )

        assert config.provider == "modal"
        assert config.gpu_type == "A10G"
        assert config.timeout_hours == 8
