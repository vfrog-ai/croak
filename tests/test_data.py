"""Tests for CROAK data processing modules."""

import pytest
from pathlib import Path
import tempfile
import shutil

from croak.data.validator import DataValidator, ValidationResult
from croak.data.splitter import DatasetSplitter


class TestDataValidator:
    """Test DataValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.mkdtemp()
        self.dataset_dir = Path(self.tmpdir) / "dataset"

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.tmpdir)

    def _create_dataset_structure(self, num_images=10, num_labels=10):
        """Create a test dataset structure."""
        images_dir = self.dataset_dir / "images"
        labels_dir = self.dataset_dir / "labels"
        images_dir.mkdir(parents=True)
        labels_dir.mkdir(parents=True)

        # Create fake images
        for i in range(num_images):
            image_path = images_dir / f"img_{i:04d}.jpg"
            image_path.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

        # Create labels
        for i in range(num_labels):
            label_path = labels_dir / f"img_{i:04d}.txt"
            # YOLO format: class x_center y_center width height
            label_path.write_text("0 0.5 0.5 0.1 0.1\n")

    def test_validate_empty_dataset(self):
        """Test validating empty dataset."""
        self.dataset_dir.mkdir(parents=True)

        validator = DataValidator(self.dataset_dir)
        result = validator.validate_all()

        assert not result.is_valid
        assert len(result.errors) > 0

    def test_validate_valid_dataset(self):
        """Test validating valid dataset."""
        self._create_dataset_structure(num_images=100, num_labels=100)

        validator = DataValidator(self.dataset_dir)
        result = validator.validate_all()

        # May have warnings but should be valid
        assert result.statistics.get("total_images", 0) == 100

    def test_validate_missing_labels(self):
        """Test detecting missing labels."""
        self._create_dataset_structure(num_images=10, num_labels=5)

        validator = DataValidator(self.dataset_dir)
        result = validator.validate_all()

        # Should have warnings about missing labels
        assert any("missing" in w.lower() or "label" in w.lower()
                   for w in result.warnings + result.errors)

    def test_validate_corrupt_label(self):
        """Test detecting corrupt label files."""
        self._create_dataset_structure(num_images=5, num_labels=5)

        # Corrupt one label
        corrupt_label = self.dataset_dir / "labels" / "img_0000.txt"
        corrupt_label.write_text("not valid yolo format")

        validator = DataValidator(self.dataset_dir)
        result = validator.validate_all()

        # Should detect the corrupt label
        assert any("invalid" in str(e).lower() or "corrupt" in str(e).lower()
                   or "format" in str(e).lower() for e in result.errors + result.warnings)

    def test_validation_result_structure(self):
        """Test ValidationResult structure."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["minor issue"],
            statistics={"total_images": 100},
        )

        assert result.is_valid
        assert len(result.warnings) == 1
        assert result.statistics["total_images"] == 100


class TestDatasetSplitter:
    """Test DatasetSplitter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.mkdtemp()
        self.dataset_dir = Path(self.tmpdir) / "dataset"

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.tmpdir)

    def _create_dataset(self, num_images=100):
        """Create test dataset."""
        images_dir = self.dataset_dir / "images"
        labels_dir = self.dataset_dir / "labels"
        images_dir.mkdir(parents=True)
        labels_dir.mkdir(parents=True)

        for i in range(num_images):
            image_path = images_dir / f"img_{i:04d}.jpg"
            image_path.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

            label_path = labels_dir / f"img_{i:04d}.txt"
            class_id = i % 3  # Cycle through 3 classes
            label_path.write_text(f"{class_id} 0.5 0.5 0.1 0.1\n")

    def test_split_default_ratios(self):
        """Test splitting with default ratios."""
        self._create_dataset(100)

        splitter = DatasetSplitter(self.dataset_dir)
        result = splitter.split()

        assert result.get("success")
        splits = result.get("splits", {})

        # Check approximate ratios (80/15/5)
        total = sum(splits.values())
        assert total == 100

    def test_split_custom_ratios(self):
        """Test splitting with custom ratios."""
        self._create_dataset(100)

        splitter = DatasetSplitter(self.dataset_dir)
        result = splitter.split(
            train_ratio=0.7,
            val_ratio=0.2,
            test_ratio=0.1,
        )

        assert result.get("success")
        splits = result.get("splits", {})
        assert splits.get("train", 0) == 70
        assert splits.get("val", 0) == 20
        assert splits.get("test", 0) == 10

    def test_split_creates_data_yaml(self):
        """Test that data.yaml is created."""
        self._create_dataset(100)

        splitter = DatasetSplitter(self.dataset_dir)
        result = splitter.split()

        assert result.get("data_yaml_path")
        data_yaml_path = Path(result["data_yaml_path"])
        assert data_yaml_path.exists()

    def test_split_reproducibility(self):
        """Test that splits are reproducible with same seed."""
        self._create_dataset(100)

        splitter1 = DatasetSplitter(self.dataset_dir)
        result1 = splitter1.split(seed=42)

        # Reset and split again
        splitter2 = DatasetSplitter(self.dataset_dir)
        result2 = splitter2.split(seed=42)

        assert result1.get("splits") == result2.get("splits")

    def test_split_stratified(self):
        """Test stratified splitting."""
        self._create_dataset(100)

        splitter = DatasetSplitter(self.dataset_dir)
        result = splitter.split(stratify=True)

        assert result.get("success")
        # Stratified split should maintain class proportions in each split

    def test_split_invalid_ratios(self):
        """Test that invalid ratios are rejected."""
        self._create_dataset(100)

        splitter = DatasetSplitter(self.dataset_dir)
        result = splitter.split(
            train_ratio=0.5,
            val_ratio=0.5,
            test_ratio=0.5,  # Sum > 1
        )

        assert not result.get("success")
        assert "ratio" in result.get("error", "").lower()
