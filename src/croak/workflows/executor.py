"""Workflow step execution and tracking."""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import yaml
from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    """Single workflow step."""
    id: str
    name: str
    description: str = ""
    file_path: str = ""
    agent: str = ""
    required: bool = True
    depends_on: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)


class Workflow(BaseModel):
    """Workflow definition."""
    id: str
    name: str
    description: str = ""
    agent: str = ""
    version: str = "1.0"
    steps: List[WorkflowStep] = Field(default_factory=list)

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get step by ID.

        Args:
            step_id: Step ID to find.

        Returns:
            WorkflowStep if found, None otherwise.
        """
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_next_step(self, completed: List[str]) -> Optional[WorkflowStep]:
        """Get next uncompleted step.

        Args:
            completed: List of completed step IDs.

        Returns:
            Next WorkflowStep to execute, or None if all done.
        """
        for step in self.steps:
            if step.id not in completed:
                # Check dependencies
                if all(dep in completed for dep in step.depends_on):
                    return step
        return None

    def get_progress(self, completed: List[str]) -> Dict[str, Any]:
        """Get workflow progress.

        Args:
            completed: List of completed step IDs.

        Returns:
            Dict with progress information.
        """
        total = len(self.steps)
        done = len([s for s in self.steps if s.id in completed])

        return {
            'total_steps': total,
            'completed_steps': done,
            'remaining_steps': total - done,
            'progress_percent': (done / total * 100) if total > 0 else 0,
            'is_complete': done == total,
        }


class WorkflowExecutor:
    """Execute and track workflow progress."""

    def __init__(self, workflows_dir: Path, state_manager):
        """Initialize workflow executor.

        Args:
            workflows_dir: Directory containing workflow definitions.
            state_manager: PipelineState instance for tracking.
        """
        self.workflows_dir = workflows_dir
        self.state = state_manager
        self._workflows: Dict[str, Workflow] = {}

    def load_workflow(self, workflow_id: str) -> Workflow:
        """Load workflow definition.

        Args:
            workflow_id: Workflow ID (directory name).

        Returns:
            Loaded Workflow.

        Raises:
            FileNotFoundError: If workflow not found.
        """
        if workflow_id in self._workflows:
            return self._workflows[workflow_id]

        workflow_dir = self.workflows_dir / workflow_id
        yaml_path = workflow_dir / "workflow.yaml"

        if not yaml_path.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_id}")

        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        # Parse steps
        steps = []
        steps_dir = workflow_dir / "steps"

        for step_data in data.get('steps', []):
            step_id = step_data.get('id', '')
            step_file = step_data.get('file', f"{step_id}.md")
            step_path = steps_dir / step_file

            steps.append(WorkflowStep(
                id=step_id,
                name=step_data.get('name', step_id),
                description=step_data.get('description', ''),
                file_path=str(step_path) if step_path.exists() else '',
                agent=step_data.get('agent', data.get('agent', '')),
                required=step_data.get('required', True),
                depends_on=step_data.get('depends_on', []),
                outputs=step_data.get('outputs', []),
            ))

        workflow = Workflow(
            id=workflow_id,
            name=data.get('name', workflow_id),
            description=data.get('description', ''),
            agent=data.get('agent', ''),
            version=data.get('version', '1.0'),
            steps=steps,
        )

        self._workflows[workflow_id] = workflow
        return workflow

    def get_step_content(self, step: WorkflowStep) -> str:
        """Get markdown content for a step.

        Args:
            step: WorkflowStep to get content for.

        Returns:
            Markdown content string.
        """
        if not step.file_path:
            return f"# {step.name}\n\n{step.description}\n\n*Step content not defined.*"

        step_path = Path(step.file_path)
        if not step_path.exists():
            return f"# {step.name}\n\n{step.description}\n\n*Step file not found: {step.file_path}*"

        with open(step_path) as f:
            return f.read()

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current workflow progress.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Dict with status information.
        """
        workflow = self._workflows.get(workflow_id) or self.load_workflow(workflow_id)

        # Get completed steps from state
        completed = self.state.get_workflow_progress(workflow_id)
        progress = workflow.get_progress(completed)
        next_step = workflow.get_next_step(completed)

        return {
            'workflow_id': workflow_id,
            'workflow_name': workflow.name,
            'agent': workflow.agent,
            **progress,
            'current_step': next_step.id if next_step else None,
            'current_step_name': next_step.name if next_step else None,
            'completed': completed,
            'remaining': [s.id for s in workflow.steps if s.id not in completed],
        }

    def complete_step(
        self,
        workflow_id: str,
        step_id: str,
        artifacts: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Mark step as completed.

        Args:
            workflow_id: Workflow ID.
            step_id: Step ID to complete.
            artifacts: Optional artifacts produced by step.

        Returns:
            Updated workflow status.

        Raises:
            ValueError: If step not found or dependencies not met.
        """
        workflow = self._workflows.get(workflow_id) or self.load_workflow(workflow_id)
        step = workflow.get_step(step_id)

        if not step:
            raise ValueError(f"Step not found: {step_id}")

        # Check dependencies
        completed = self.state.get_workflow_progress(workflow_id)
        for dep in step.depends_on:
            if dep not in completed:
                raise ValueError(
                    f"Dependency not met: '{dep}' must be completed before '{step_id}'"
                )

        # Update state
        self.state.complete_workflow_step(workflow_id, step_id, artifacts)

        return self.get_workflow_status(workflow_id)

    def reset_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Reset workflow progress.

        Args:
            workflow_id: Workflow ID to reset.

        Returns:
            Reset workflow status.
        """
        self.state.reset_workflow(workflow_id)
        return self.get_workflow_status(workflow_id)

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows.

        Returns:
            List of workflow info dicts.
        """
        workflows = []

        if not self.workflows_dir.exists():
            return workflows

        for workflow_dir in self.workflows_dir.iterdir():
            if workflow_dir.is_dir():
                yaml_path = workflow_dir / "workflow.yaml"
                if yaml_path.exists():
                    try:
                        workflow = self.load_workflow(workflow_dir.name)
                        workflows.append({
                            'id': workflow.id,
                            'name': workflow.name,
                            'description': workflow.description,
                            'agent': workflow.agent,
                            'steps_count': len(workflow.steps),
                        })
                    except Exception:
                        pass

        return workflows

    def validate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Validate workflow definition.

        Args:
            workflow_id: Workflow ID to validate.

        Returns:
            Validation result with any errors.
        """
        errors = []
        warnings = []

        try:
            workflow = self.load_workflow(workflow_id)
        except FileNotFoundError as e:
            return {'valid': False, 'errors': [str(e)], 'warnings': []}

        # Check steps
        step_ids = {s.id for s in workflow.steps}

        for step in workflow.steps:
            # Check dependencies exist
            for dep in step.depends_on:
                if dep not in step_ids:
                    errors.append(
                        f"Step '{step.id}' depends on non-existent step '{dep}'"
                    )

            # Check step file exists
            if step.file_path and not Path(step.file_path).exists():
                warnings.append(
                    f"Step '{step.id}' file not found: {step.file_path}"
                )

        # Check for circular dependencies
        def has_cycle(step_id: str, visited: set, stack: set) -> bool:
            visited.add(step_id)
            stack.add(step_id)

            step = workflow.get_step(step_id)
            if step:
                for dep in step.depends_on:
                    if dep not in visited:
                        if has_cycle(dep, visited, stack):
                            return True
                    elif dep in stack:
                        return True

            stack.remove(step_id)
            return False

        for step in workflow.steps:
            if has_cycle(step.id, set(), set()):
                errors.append(f"Circular dependency detected involving step '{step.id}'")
                break

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
        }
