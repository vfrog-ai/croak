"""Handoff contract validation between agents."""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import yaml

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


class ContractValidationError(Exception):
    """Raised when contract validation fails."""
    pass


class HandoffValidator:
    """Validate handoff data against JSON Schema contracts.

    Ensures data passed between agents conforms to defined contracts,
    preventing data corruption and miscommunication between pipeline stages.
    """

    def __init__(self, contracts_dir: Path):
        """Initialize handoff validator.

        Args:
            contracts_dir: Directory containing contract schema files.
        """
        self.contracts_dir = contracts_dir
        self._schemas: Dict[str, dict] = {}

    def load_schema(self, contract_name: str) -> dict:
        """Load JSON Schema for a contract.

        Args:
            contract_name: Name of the contract (without extension).

        Returns:
            Schema dict.

        Raises:
            FileNotFoundError: If schema file not found.
        """
        if contract_name in self._schemas:
            return self._schemas[contract_name]

        # Try multiple extensions
        for ext in ['.schema.yaml', '.schema.json', '.yaml', '.json']:
            schema_path = self.contracts_dir / f"{contract_name}{ext}"
            if schema_path.exists():
                with open(schema_path) as f:
                    if ext.endswith('.json'):
                        schema = json.load(f)
                    else:
                        schema = yaml.safe_load(f)

                self._schemas[contract_name] = schema
                return schema

        raise FileNotFoundError(
            f"Contract schema not found: {contract_name} "
            f"in {self.contracts_dir}"
        )

    def validate(self, contract_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against contract schema.

        Args:
            contract_name: Name of the contract.
            data: Data to validate.

        Returns:
            Dict with validation result.
        """
        if not HAS_JSONSCHEMA:
            # If jsonschema not installed, do basic validation
            return self._basic_validate(contract_name, data)

        schema = self.load_schema(contract_name)

        errors = []
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            errors.append({
                'path': list(e.absolute_path),
                'message': e.message,
                'value': str(e.instance)[:100],  # Truncate for display
            })
        except jsonschema.SchemaError as e:
            errors.append({
                'path': [],
                'message': f"Schema error: {e.message}",
                'value': None,
            })

        return {
            'valid': len(errors) == 0,
            'contract': contract_name,
            'errors': errors,
            'validated_at': datetime.utcnow().isoformat(),
        }

    def _basic_validate(self, contract_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Basic validation without jsonschema.

        Args:
            contract_name: Name of the contract.
            data: Data to validate.

        Returns:
            Dict with validation result.
        """
        errors = []
        schema = self.load_schema(contract_name)

        # Check required fields
        required = schema.get('required', [])
        for field in required:
            if field not in data:
                errors.append({
                    'path': [field],
                    'message': f"Required field missing: {field}",
                    'value': None,
                })

        return {
            'valid': len(errors) == 0,
            'contract': contract_name,
            'errors': errors,
            'validated_at': datetime.utcnow().isoformat(),
            'note': 'Basic validation only (install jsonschema for full validation)',
        }

    def create_handoff(
        self,
        contract_name: str,
        from_agent: str,
        to_agent: str,
        data: Dict[str, Any],
        handoffs_dir: Path,
    ) -> Path:
        """Create validated handoff file.

        Args:
            contract_name: Name of the contract.
            from_agent: Source agent name.
            to_agent: Destination agent name.
            data: Handoff data.
            handoffs_dir: Directory to store handoff files.

        Returns:
            Path to created handoff file.

        Raises:
            ContractValidationError: If validation fails.
        """
        # Validate first
        result = self.validate(contract_name, data)
        if not result['valid']:
            error_msgs = [e['message'] for e in result['errors']]
            raise ContractValidationError(
                f"Handoff validation failed for {contract_name}:\n" +
                "\n".join(f"  - {msg}" for msg in error_msgs)
            )

        # Create handoff document
        handoff = {
            'contract': contract_name,
            'from_agent': from_agent,
            'to_agent': to_agent,
            'created_at': datetime.utcnow().isoformat(),
            'data': data,
        }

        # Save to file
        handoffs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        filename = f"{from_agent}-to-{to_agent}-{timestamp}.yaml"
        handoff_path = handoffs_dir / filename

        with open(handoff_path, 'w') as f:
            yaml.dump(handoff, f, default_flow_style=False, sort_keys=False)

        return handoff_path

    def read_handoff(self, handoff_path: Path) -> Dict[str, Any]:
        """Read and validate existing handoff.

        Args:
            handoff_path: Path to handoff file.

        Returns:
            Handoff document with validation result.
        """
        with open(handoff_path) as f:
            handoff = yaml.safe_load(f)

        # Re-validate
        result = self.validate(handoff['contract'], handoff['data'])

        return {
            **handoff,
            'validation': result,
        }

    def find_latest_handoff(
        self,
        handoffs_dir: Path,
        from_agent: Optional[str] = None,
        to_agent: Optional[str] = None,
    ) -> Optional[Path]:
        """Find the most recent handoff file.

        Args:
            handoffs_dir: Directory containing handoff files.
            from_agent: Optional filter by source agent.
            to_agent: Optional filter by destination agent.

        Returns:
            Path to latest matching handoff, or None.
        """
        if not handoffs_dir.exists():
            return None

        matching = []
        for f in handoffs_dir.glob('*.yaml'):
            name = f.stem
            if from_agent and not name.startswith(f"{from_agent}-to-"):
                continue
            if to_agent and f"-to-{to_agent}-" not in name:
                continue
            matching.append(f)

        if not matching:
            return None

        # Sort by modification time, newest first
        matching.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return matching[0]


# Convenience functions for common handoffs

def create_data_handoff(
    validator: HandoffValidator,
    dataset_path: str,
    format: str,
    data_yaml_path: str,
    splits: Dict[str, int],
    classes: List[str],
    statistics: Dict[str, Any],
    validation_passed: bool,
    vfrog_project_id: Optional[str] = None,
    handoffs_dir: Path = Path('.croak/handoffs'),
) -> Path:
    """Create data → training handoff.

    Args:
        validator: HandoffValidator instance.
        dataset_path: Path to the processed dataset.
        format: Dataset format (yolo, coco, etc.).
        data_yaml_path: Path to data.yaml file.
        splits: Dict with train/val/test counts.
        classes: List of class names.
        statistics: Dataset statistics.
        validation_passed: Whether validation passed.
        vfrog_project_id: Optional vfrog project ID.
        handoffs_dir: Directory for handoff files.

    Returns:
        Path to created handoff file.
    """
    data = {
        'dataset_path': dataset_path,
        'format': format,
        'data_yaml_path': data_yaml_path,
        'splits': splits,
        'classes': classes,
        'statistics': statistics,
        'validation_passed': validation_passed,
    }
    if vfrog_project_id:
        data['vfrog_project_id'] = vfrog_project_id

    return validator.create_handoff(
        'data-handoff',
        'data',
        'training',
        data,
        handoffs_dir,
    )


def create_training_handoff(
    validator: HandoffValidator,
    model_path: str,
    architecture: str,
    config: Dict[str, Any],
    experiment: Dict[str, Any],
    training_metrics: Dict[str, float],
    checkpoints: List[Dict[str, Any]],
    compute: Dict[str, Any],
    dataset_hash: str,
    random_seed: int,
    handoffs_dir: Path = Path('.croak/handoffs'),
) -> Path:
    """Create training → evaluation handoff.

    Args:
        validator: HandoffValidator instance.
        model_path: Path to best model weights.
        architecture: Model architecture name.
        config: Training configuration.
        experiment: Experiment tracking info.
        training_metrics: Final training metrics.
        checkpoints: List of checkpoint info.
        compute: Compute resources used.
        dataset_hash: Hash of training dataset.
        random_seed: Random seed used.
        handoffs_dir: Directory for handoff files.

    Returns:
        Path to created handoff file.
    """
    data = {
        'model_path': model_path,
        'architecture': architecture,
        'config': config,
        'experiment': experiment,
        'training_metrics': training_metrics,
        'checkpoints': checkpoints,
        'compute': compute,
        'dataset_hash': dataset_hash,
        'random_seed': random_seed,
    }

    return validator.create_handoff(
        'training-handoff',
        'training',
        'evaluation',
        data,
        handoffs_dir,
    )


def create_evaluation_handoff(
    validator: HandoffValidator,
    model_path: str,
    evaluation_report_path: str,
    metrics: Dict[str, float],
    deployment_ready: bool,
    recommended_threshold: float,
    failure_analysis: Optional[Dict[str, Any]] = None,
    handoffs_dir: Path = Path('.croak/handoffs'),
) -> Path:
    """Create evaluation → deployment handoff.

    Args:
        validator: HandoffValidator instance.
        model_path: Path to evaluated model.
        evaluation_report_path: Path to evaluation report.
        metrics: Evaluation metrics.
        deployment_ready: Whether model is ready for deployment.
        recommended_threshold: Recommended confidence threshold.
        failure_analysis: Optional failure analysis results.
        handoffs_dir: Directory for handoff files.

    Returns:
        Path to created handoff file.
    """
    data = {
        'model_path': model_path,
        'evaluation_report_path': evaluation_report_path,
        'metrics': metrics,
        'deployment_ready': deployment_ready,
        'recommended_threshold': recommended_threshold,
    }
    if failure_analysis:
        data['failure_analysis'] = failure_analysis

    return validator.create_handoff(
        'evaluation-handoff',
        'evaluation',
        'deployment',
        data,
        handoffs_dir,
    )
