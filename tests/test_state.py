"""Tests for CROAK pipeline state."""

import pytest
from pathlib import Path
import tempfile

from croak.core.state import PipelineState, Experiment, DatasetArtifact


class TestPipelineState:
    """Test PipelineState class."""

    def test_default_state(self):
        """Test default state values."""
        state = PipelineState()

        assert state.version == "1.0"
        assert state.current_stage == "uninitialized"
        assert state.stages_completed == []
        assert state.experiments == []

    def test_save_and_load(self):
        """Test saving and loading state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "state.yaml"

            # Create and save state
            state = PipelineState(
                current_stage="training",
                stages_completed=["data_preparation"],
            )
            state.save(state_path)

            # Load and verify
            loaded = PipelineState.load(state_path)
            assert loaded.current_stage == "training"
            assert "data_preparation" in loaded.stages_completed

    def test_complete_stage(self):
        """Test completing stages."""
        state = PipelineState()

        state.complete_stage("data_scan")
        assert state.is_stage_completed("data_scan")
        assert not state.is_stage_completed("training")

        state.complete_stage("data_validation")
        assert len(state.stages_completed) == 2

    def test_no_duplicate_stages(self):
        """Test that stages aren't duplicated."""
        state = PipelineState()

        state.complete_stage("data_scan")
        state.complete_stage("data_scan")

        assert state.stages_completed.count("data_scan") == 1

    def test_add_warning(self):
        """Test adding warnings."""
        state = PipelineState()

        state.add_warning("Low image count")
        state.add_warning("Class imbalance")

        assert len(state.warnings) == 2
        assert "Low image count" in state.warnings

    def test_add_experiment(self):
        """Test adding experiments."""
        state = PipelineState()

        exp = Experiment(
            id="exp-001",
            status="running",
            architecture="yolov8s",
        )
        state.add_experiment(exp)

        assert len(state.experiments) == 1
        assert state.get_experiment("exp-001") == exp
        assert state.get_experiment("nonexistent") is None

    def test_dataset_artifact(self):
        """Test dataset artifact storage."""
        state = PipelineState()

        state.artifacts.dataset = DatasetArtifact(
            path="./data/processed",
            format="yolo",
            classes=["person", "car"],
            splits={"train": 800, "val": 100, "test": 100},
        )

        assert state.artifacts.dataset.path == "./data/processed"
        assert len(state.artifacts.dataset.classes) == 2
        assert state.artifacts.dataset.splits["train"] == 800


class TestExperiment:
    """Test Experiment class."""

    def test_default_experiment(self):
        """Test default experiment values."""
        exp = Experiment(id="exp-001")

        assert exp.id == "exp-001"
        assert exp.status == "pending"
        assert exp.metrics == {}

    def test_experiment_with_metrics(self):
        """Test experiment with metrics."""
        exp = Experiment(
            id="exp-001",
            status="completed",
            architecture="yolov8s",
            metrics={"mAP50": 0.75, "mAP50_95": 0.52},
            model_path="./weights/best.pt",
        )

        assert exp.metrics["mAP50"] == 0.75
        assert exp.model_path == "./weights/best.pt"
