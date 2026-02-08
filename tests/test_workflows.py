"""Tests for CROAK workflow execution."""

import pytest
from pathlib import Path
import tempfile
import yaml

from croak.workflows.executor import WorkflowExecutor, Workflow, WorkflowStep
from croak.core.state import PipelineState


class TestWorkflow:
    """Test Workflow class."""

    def test_create_workflow(self):
        """Test creating a workflow."""
        workflow = Workflow(
            id="test-workflow",
            name="Test Workflow",
            description="A test workflow",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="First Step",
                    agent="data-agent",
                    description="Validate data",
                    depends_on=[],
                ),
                WorkflowStep(
                    id="step2",
                    name="Second Step",
                    agent="training-agent",
                    description="Train model",
                    depends_on=["step1"],
                ),
            ],
        )

        assert workflow.id == "test-workflow"
        assert len(workflow.steps) == 2
        assert workflow.steps[1].depends_on == ["step1"]


class TestWorkflowExecutor:
    """Test WorkflowExecutor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.mkdtemp()
        self.project_dir = Path(self.tmpdir)
        self.workflows_dir = self.project_dir / ".croak" / "workflows"
        self.workflows_dir.mkdir(parents=True)

        # Create pipeline state
        self.state = PipelineState(
            current_stage="uninitialized",
            stages_completed=[],
            initialized_at="2024-01-01T00:00:00",
        )

    def teardown_method(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.tmpdir)

    def _create_workflow_file(self, workflow_id: str, steps: list):
        """Create a workflow YAML file in subdirectory structure."""
        workflow_dir = self.workflows_dir / workflow_id
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = {
            "id": workflow_id,
            "name": f"Test {workflow_id}",
            "description": "Test workflow",
            "steps": steps,
        }

        workflow_path = workflow_dir / "workflow.yaml"
        with open(workflow_path, "w") as f:
            yaml.dump(workflow, f)

        return workflow_path

    def test_load_workflow(self):
        """Test loading a workflow."""
        self._create_workflow_file("test-workflow", [
            {
                "id": "step1",
                "name": "Step 1",
                "agent": "data-agent",
                "description": "Validate data",
                "depends_on": [],
            }
        ])

        executor = WorkflowExecutor(self.workflows_dir, self.state)
        workflow = executor.load_workflow("test-workflow")

        assert workflow.id == "test-workflow"
        assert len(workflow.steps) == 1

    def test_get_ready_steps(self):
        """Test getting steps ready for execution."""
        self._create_workflow_file("multi-step", [
            {
                "id": "step1",
                "name": "Step 1",
                "agent": "data-agent",
                "description": "Validate data",
                "depends_on": [],
            },
            {
                "id": "step2",
                "name": "Step 2",
                "agent": "training-agent",
                "description": "Train model",
                "depends_on": ["step1"],
            },
        ])

        executor = WorkflowExecutor(self.workflows_dir, self.state)
        workflow = executor.load_workflow("multi-step")

        # Initially only step1 should be ready
        next_step = workflow.get_next_step([])
        assert next_step is not None
        assert next_step.id == "step1"

        # After step1 completes, step2 should be ready
        next_step = workflow.get_next_step(["step1"])
        assert next_step is not None
        assert next_step.id == "step2"

    def test_complete_step(self):
        """Test completing a workflow step."""
        self._create_workflow_file("completion-test", [
            {
                "id": "step1",
                "name": "Step 1",
                "agent": "data-agent",
                "description": "Validate data",
                "depends_on": [],
            }
        ])

        executor = WorkflowExecutor(self.workflows_dir, self.state)

        result = executor.complete_step(
            "completion-test",
            "step1",
            artifacts={"output": "test_output"},
        )

        assert "step1" in result.get("completed", [])

    def test_get_workflow_status(self):
        """Test getting workflow status."""
        self._create_workflow_file("status-test", [
            {
                "id": "step1",
                "name": "Step 1",
                "agent": "data-agent",
                "description": "Validate data",
                "depends_on": [],
            },
            {
                "id": "step2",
                "name": "Step 2",
                "agent": "training-agent",
                "description": "Train model",
                "depends_on": ["step1"],
            },
        ])

        executor = WorkflowExecutor(self.workflows_dir, self.state)

        # Complete first step
        executor.complete_step("status-test", "step1")

        status = executor.get_workflow_status("status-test")

        assert status["total_steps"] == 2
        assert status["completed_steps"] == 1
        assert status["progress_percent"] == 50.0
        assert not status["is_complete"]

    def test_workflow_completion(self):
        """Test workflow completion detection."""
        self._create_workflow_file("full-workflow", [
            {
                "id": "step1",
                "name": "Step 1",
                "agent": "data-agent",
                "description": "Validate data",
                "depends_on": [],
            },
        ])

        executor = WorkflowExecutor(self.workflows_dir, self.state)

        # Complete the only step
        executor.complete_step("full-workflow", "step1")

        status = executor.get_workflow_status("full-workflow")

        assert status["is_complete"]
        assert status["progress_percent"] == 100.0

    def test_parallel_steps(self):
        """Test detecting parallel-ready steps."""
        self._create_workflow_file("parallel-workflow", [
            {
                "id": "step1",
                "name": "Step 1",
                "agent": "agent-a",
                "description": "Task 1",
                "depends_on": [],
            },
            {
                "id": "step2",
                "name": "Step 2",
                "agent": "agent-b",
                "description": "Task 2",
                "depends_on": [],  # No dependencies
            },
            {
                "id": "step3",
                "name": "Step 3",
                "agent": "agent-c",
                "description": "Task 3",
                "depends_on": ["step1", "step2"],
            },
        ])

        executor = WorkflowExecutor(self.workflows_dir, self.state)
        workflow = executor.load_workflow("parallel-workflow")

        def get_ready_steps(wf, completed):
            """Get all steps whose dependencies are met."""
            return [s for s in wf.steps
                    if s.id not in completed
                    and all(d in completed for d in s.depends_on)]

        # Both step1 and step2 should be ready initially
        ready = get_ready_steps(workflow, [])
        assert len(ready) == 2

        # step3 not ready until both complete
        ready = get_ready_steps(workflow, ["step1"])
        assert len(ready) == 1  # Only step2

        ready = get_ready_steps(workflow, ["step1", "step2"])
        assert len(ready) == 1
        assert ready[0].id == "step3"
