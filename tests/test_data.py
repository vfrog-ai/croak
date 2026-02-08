"""Tests for CROAK data processing modules."""

import pytest
from pathlib import Path
import tempfile
import shutil

from PIL import Image

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
        images_dir = self.dataset_dir / "raw"
        labels_dir = self.dataset_dir / "annotations"
        images_dir.mkdir(parents=True)
        labels_dir.mkdir(parents=True)

        # Create valid JPEG images using PIL
        for i in range(num_images):
            image_path = images_dir / f"img_{i:04d}.jpg"
            img = Image.new('RGB', (640, 480), color=(i % 256, 0, 0))
            img.save(str(image_path), 'JPEG')

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

        assert not result.passed
        assert len(result.errors) > 0

    def test_validate_valid_dataset(self):
        """Test validating valid dataset."""
        self._create_dataset_structure(num_images=100, num_labels=100)

        validator = DataValidator(self.dataset_dir)
        result = validator.validate_all()

        # May have warnings but should find all images
        assert result.statistics.get("images", {}).get("total_images", 0) == 100

    def test_validate_missing_labels(self):
        """Test detecting missing labels."""
        self._create_dataset_structure(num_images=10, num_labels=5)

        validator = DataValidator(self.dataset_dir)
        result = validator.validate_all()

        # Should have warnings about missing annotations
        all_messages = result.warnings + result.errors
        assert any("annotation" in w.lower() or "without" in w.lower()
                   for w in all_messages)

    def test_validate_corrupt_label(self):
        """Test detecting corrupt label files."""
        self._create_dataset_structure(num_images=5, num_labels=5)

        # Corrupt one label
        corrupt_label = self.dataset_dir / "annotations" / "img_0000.txt"
        corrupt_label.write_text("not valid yolo format")

        validator = DataValidator(self.dataset_dir)
        result = validator.validate_all()

        # Should detect the corrupt label
        all_messages = result.errors + result.warnings
        assert any("invalid" in str(e).lower() or "corrupt" in str(e).lower()
                   or "format" in str(e).lower() or "error" in str(e).lower()
                   for e in all_messages)

    def test_validation_result_structure(self):
        """Test ValidationResult structure."""
        result = ValidationResult(
            passed=True,
            errors=[],
            warnings=["minor issue"],
            statistics={"total_images": 100},
        )

        assert result.passed
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
        images_dir = self.dataset_dir / "raw"
        labels_dir = self.dataset_dir / "annotations"
        images_dir.mkdir(parents=True)
        labels_dir.mkdir(parents=True)

        for i in range(num_images):
            image_path = images_dir / f"img_{i:04d}.jpg"
            img = Image.new('RGB', (64, 64), color=(i % 256, (i * 7) % 256, 0))
            img.save(str(image_path), 'JPEG')

            label_path = labels_dir / f"img_{i:04d}.txt"
            class_id = i % 3  # Cycle through 3 classes
            label_path.write_text(f"{class_id} 0.5 0.5 0.1 0.1\n")

    def test_split_default_ratios(self):
        """Test splitting with default ratios."""
        self._create_dataset(100)

        splitter = DatasetSplitter(self.dataset_dir)
        result = splitter.split()

        # Check total adds up
        total = result["train"] + result["val"] + result["test"]
        assert total == 100

    def test_split_custom_ratios(self):
        """Test splitting with custom ratios."""
        self._create_dataset(100)

        splitter = DatasetSplitter(self.dataset_dir)
        result = splitter.split(
            train_ratio=0.7,
            val_ratio=0.2,
            test_ratio=0.1,
            stratify=False,
        )

        assert result["train"] == 70
        assert result["val"] == 20
        assert result["test"] == 10

    def test_split_creates_data_yaml(self):
        """Test that data.yaml is created."""
        self._create_dataset(100)

        splitter = DatasetSplitter(self.dataset_dir)
        result = splitter.split()

        assert result.get("data_yaml")
        data_yaml_path = Path(result["data_yaml"])
        assert data_yaml_path.exists()

    def test_split_reproducibility(self):
        """Test that splits are reproducible with same seed."""
        self._create_dataset(100)

        splitter1 = DatasetSplitter(self.dataset_dir)
        result1 = splitter1.split(seed=42)

        # Reset and split again
        splitter2 = DatasetSplitter(self.dataset_dir)
        result2 = splitter2.split(seed=42)

        assert result1["train"] == result2["train"]
        assert result1["val"] == result2["val"]
        assert result1["test"] == result2["test"]
        assert result1["dataset_hash"] == result2["dataset_hash"]

    def test_split_stratified(self):
        """Test stratified splitting."""
        self._create_dataset(100)

        splitter = DatasetSplitter(self.dataset_dir)
        result = splitter.split(stratify=True)

        total = result["train"] + result["val"] + result["test"]
        assert total == 100

    def test_split_invalid_ratios(self):
        """Test that invalid ratios are rejected."""
        self._create_dataset(100)

        splitter = DatasetSplitter(self.dataset_dir)
        with pytest.raises(ValueError, match="[Rr]atio"):
            splitter.split(
                train_ratio=0.5,
                val_ratio=0.5,
                test_ratio=0.5,  # Sum > 1
            )
