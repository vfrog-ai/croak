"""Tests for CROAK handoff contract validation."""

import pytest
from pathlib import Path
import tempfile
import yaml

from croak.contracts.validator import (
    HandoffValidator,
    ContractValidationError,
    create_data_handoff,
    create_training_handoff,
)


class TestHandoffValidator:
    """Test HandoffValidator class."""

    def test_load_schema(self):
        """Test loading JSON schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contracts_dir = Path(tmpdir)

            # Create a simple schema
            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                },
            }

            with open(contracts_dir / "test.schema.yaml", "w") as f:
                yaml.dump(schema, f)

            validator = HandoffValidator(contracts_dir)
            loaded = validator.load_schema("test")

            assert loaded["type"] == "object"
            assert "name" in loaded["required"]

    def test_validate_valid_data(self):
        """Test validating valid data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contracts_dir = Path(tmpdir)

            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["name", "value"],
                "properties": {
                    "name": {"type": "string"},
                    "value": {"type": "integer"},
                },
            }

            with open(contracts_dir / "test.schema.yaml", "w") as f:
                yaml.dump(schema, f)

            validator = HandoffValidator(contracts_dir)
            result = validator.validate("test", {"name": "test", "value": 42})

            assert result["valid"] is True
            assert len(result["errors"]) == 0

    def test_validate_invalid_data(self):
        """Test validating invalid data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contracts_dir = Path(tmpdir)

            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                },
            }

            with open(contracts_dir / "test.schema.yaml", "w") as f:
                yaml.dump(schema, f)

            validator = HandoffValidator(contracts_dir)
            result = validator.validate("test", {})  # Missing required field

            assert result["valid"] is False
            assert len(result["errors"]) > 0

    def test_create_handoff(self):
        """Test creating handoff file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contracts_dir = Path(tmpdir) / "contracts"
            contracts_dir.mkdir()
            handoffs_dir = Path(tmpdir) / "handoffs"

            # Create schema
            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["message"],
                "properties": {
                    "message": {"type": "string"},
                },
            }

            with open(contracts_dir / "test.schema.yaml", "w") as f:
                yaml.dump(schema, f)

            validator = HandoffValidator(contracts_dir)
            handoff_path = validator.create_handoff(
                "test",
                "agent1",
                "agent2",
                {"message": "hello"},
                handoffs_dir,
            )

            assert handoff_path.exists()
            assert "agent1-to-agent2" in handoff_path.name

    def test_create_handoff_validation_fails(self):
        """Test that invalid handoff raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contracts_dir = Path(tmpdir) / "contracts"
            contracts_dir.mkdir()
            handoffs_dir = Path(tmpdir) / "handoffs"

            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["message"],
                "properties": {
                    "message": {"type": "string"},
                },
            }

            with open(contracts_dir / "test.schema.yaml", "w") as f:
                yaml.dump(schema, f)

            validator = HandoffValidator(contracts_dir)

            with pytest.raises(ContractValidationError):
                validator.create_handoff(
                    "test",
                    "agent1",
                    "agent2",
                    {},  # Missing required field
                    handoffs_dir,
                )

    def test_read_handoff(self):
        """Test reading and re-validating handoff."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contracts_dir = Path(tmpdir) / "contracts"
            contracts_dir.mkdir()
            handoffs_dir = Path(tmpdir) / "handoffs"

            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["value"],
                "properties": {
                    "value": {"type": "integer"},
                },
            }

            with open(contracts_dir / "test.schema.yaml", "w") as f:
                yaml.dump(schema, f)

            validator = HandoffValidator(contracts_dir)
            handoff_path = validator.create_handoff(
                "test",
                "source",
                "dest",
                {"value": 123},
                handoffs_dir,
            )

            # Read it back
            handoff = validator.read_handoff(handoff_path)

            assert handoff["from_agent"] == "source"
            assert handoff["to_agent"] == "dest"
            assert handoff["data"]["value"] == 123
            assert handoff["validation"]["valid"] is True

    def test_find_latest_handoff(self):
        """Test finding latest handoff file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contracts_dir = Path(tmpdir) / "contracts"
            contracts_dir.mkdir()
            handoffs_dir = Path(tmpdir) / "handoffs"

            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {},
            }

            with open(contracts_dir / "test.schema.yaml", "w") as f:
                yaml.dump(schema, f)

            validator = HandoffValidator(contracts_dir)

            # Create multiple handoffs
            for i in range(3):
                validator.create_handoff(
                    "test",
                    "data",
                    "training",
                    {"index": i},
                    handoffs_dir,
                )

            latest = validator.find_latest_handoff(
                handoffs_dir,
                from_agent="data",
                to_agent="training",
            )

            assert latest is not None
            assert "data-to-training" in latest.name


class TestConvenienceFunctions:
    """Test convenience functions for common handoffs."""

    def test_create_data_handoff(self):
        """Test creating data handoff."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contracts_dir = Path(tmpdir) / "contracts"
            contracts_dir.mkdir()
            handoffs_dir = Path(tmpdir) / "handoffs"

            # Create data-handoff schema
            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": [
                    "dataset_path", "format", "data_yaml_path",
                    "splits", "classes", "statistics", "validation_passed"
                ],
                "properties": {
                    "dataset_path": {"type": "string"},
                    "format": {"type": "string"},
                    "data_yaml_path": {"type": "string"},
                    "splits": {"type": "object"},
                    "classes": {"type": "array"},
                    "statistics": {"type": "object"},
                    "validation_passed": {"type": "boolean"},
                },
            }

            with open(contracts_dir / "data-handoff.schema.yaml", "w") as f:
                yaml.dump(schema, f)

            validator = HandoffValidator(contracts_dir)

            handoff_path = create_data_handoff(
                validator=validator,
                dataset_path="/path/to/dataset",
                format="yolo",
                data_yaml_path="/path/to/data.yaml",
                splits={"train": 800, "val": 150, "test": 50},
                classes=["cat", "dog"],
                statistics={"total_images": 1000},
                validation_passed=True,
                handoffs_dir=handoffs_dir,
            )

            assert handoff_path.exists()

    def test_create_training_handoff(self):
        """Test creating training handoff."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contracts_dir = Path(tmpdir) / "contracts"
            contracts_dir.mkdir()
            handoffs_dir = Path(tmpdir) / "handoffs"

            # Create training-handoff schema
            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": [
                    "model_path", "architecture", "config", "experiment",
                    "training_metrics", "checkpoints", "compute",
                    "dataset_hash", "random_seed"
                ],
                "properties": {
                    "model_path": {"type": "string"},
                    "architecture": {"type": "string"},
                    "config": {"type": "object"},
                    "experiment": {"type": "object"},
                    "training_metrics": {"type": "object"},
                    "checkpoints": {"type": "array"},
                    "compute": {"type": "object"},
                    "dataset_hash": {"type": "string"},
                    "random_seed": {"type": "integer"},
                },
            }

            with open(contracts_dir / "training-handoff.schema.yaml", "w") as f:
                yaml.dump(schema, f)

            validator = HandoffValidator(contracts_dir)

            handoff_path = create_training_handoff(
                validator=validator,
                model_path="/path/to/best.pt",
                architecture="yolov8s",
                config={"epochs": 100, "batch_size": 16},
                experiment={"id": "exp-001", "name": "test"},
                training_metrics={"final_mAP50": 0.85},
                checkpoints=[{"path": "/path/to/last.pt", "epoch": 100}],
                compute={"provider": "modal", "gpu_type": "T4"},
                dataset_hash="abc123",
                random_seed=42,
                handoffs_dir=handoffs_dir,
            )

            assert handoff_path.exists()
