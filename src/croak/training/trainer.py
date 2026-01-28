"""Training orchestration for CROAK."""

from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import yaml
import hashlib

from croak.core.config import CroakConfig
from croak.core.state import PipelineState


class TrainingOrchestrator:
    """Orchestrate model training.

    Handles:
    - Configuration generation
    - Cost estimation
    - Local and cloud training
    - Experiment tracking
    """

    # GPU cost estimates (USD per hour)
    GPU_COSTS = {
        'T4': 0.50,
        'A10G': 1.10,
        'A100': 3.00,
        'L4': 0.80,
        'H100': 4.50,
    }

    # Training time estimates (seconds per image per epoch, by architecture)
    TIME_PER_IMAGE = {
        'yolov8n': 0.002,
        'yolov8s': 0.004,
        'yolov8m': 0.008,
        'yolov8l': 0.015,
        'yolov8x': 0.025,
        'yolov11n': 0.003,
        'yolov11s': 0.005,
        'yolov11m': 0.010,
        'rt-detr-l': 0.012,
        'rt-detr-x': 0.020,
    }

    def __init__(self, project_root: Path):
        """Initialize training orchestrator.

        Args:
            project_root: Path to project root directory.
        """
        self.project_root = Path(project_root)
        self.config = CroakConfig.load(self.project_root / ".croak" / "config.yaml")
        self.state = PipelineState.load(self.project_root / ".croak" / "pipeline-state.yaml")

    def prepare_training(
        self,
        architecture: Optional[str] = None,
        epochs: Optional[int] = None,
        batch_size: Optional[int] = None,
        image_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Prepare training configuration.

        Args:
            architecture: Model architecture (overrides config).
            epochs: Number of epochs (overrides config).
            batch_size: Batch size (overrides config).
            image_size: Image size (overrides config).

        Returns:
            Training configuration dict.

        Raises:
            FileNotFoundError: If data.yaml not found.
        """
        # Use provided values or defaults from config
        arch = architecture or self.config.training.architecture
        ep = epochs or self.config.training.epochs
        bs = batch_size or self.config.training.batch_size
        img = image_size or self.config.training.image_size

        # Find data.yaml
        data_yaml = self.project_root / "data" / "processed" / "data.yaml"
        if not data_yaml.exists():
            raise FileNotFoundError(
                "data.yaml not found. Run 'croak split' first to prepare your dataset."
            )

        # Create experiment ID
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        exp_id = f"exp-{timestamp}"

        # Output directory
        output_dir = self.project_root / "training" / "experiments" / exp_id

        # Training config
        train_config = {
            'architecture': arch,
            'epochs': ep,
            'batch_size': bs,
            'image_size': img,
            'data_yaml': str(data_yaml),
            'experiment_id': exp_id,
            'output_dir': str(output_dir),
            'seed': 42,
            'patience': self.config.training.patience,
            'compute_provider': self.config.compute.provider,
            'gpu_type': self.config.compute.gpu_type,
        }

        return train_config

    def estimate_cost(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate training time and cost.

        Args:
            config: Training configuration from prepare_training.

        Returns:
            Dict with cost estimates.
        """
        # Count images
        data_yaml_path = Path(config['data_yaml'])
        with open(data_yaml_path) as f:
            data_yaml = yaml.safe_load(f)

        train_dir = Path(data_yaml['path']) / data_yaml['train']
        num_images = len(list(train_dir.glob('*')))

        # Estimate time
        arch = config['architecture']
        time_per_img = self.TIME_PER_IMAGE.get(arch, 0.005)  # Default
        epochs = config['epochs']

        # Total time in hours
        total_seconds = num_images * epochs * time_per_img
        # Add overhead (validation, checkpointing, etc.)
        total_seconds *= 1.3
        total_hours = total_seconds / 3600

        # Estimate cost
        gpu_type = config.get('gpu_type', 'T4')
        hourly_cost = self.GPU_COSTS.get(gpu_type, 0.50)
        estimated_cost = total_hours * hourly_cost

        return {
            'num_images': num_images,
            'epochs': epochs,
            'architecture': arch,
            'gpu_type': gpu_type,
            'estimated_hours': round(total_hours, 2),
            'estimated_cost_usd': round(estimated_cost, 2),
            'hourly_rate_usd': hourly_cost,
            'note': 'Estimates are approximate and may vary based on image sizes and complexity.',
        }

    def train_local(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Train locally with GPU.

        Args:
            config: Training configuration.

        Returns:
            Training results dict.
        """
        try:
            from ultralytics import YOLO
        except ImportError:
            return {
                'success': False,
                'error': "Ultralytics not installed. Run: pip install ultralytics",
            }

        # Create output directory
        output_dir = Path(config['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine model file
        arch = config['architecture']
        if arch.startswith('rt-detr'):
            model_file = f"{arch}.pt"
        else:
            model_file = f"{arch}.pt"

        try:
            # Load model
            model = YOLO(model_file)

            # Train
            results = model.train(
                data=config['data_yaml'],
                epochs=config['epochs'],
                batch=config['batch_size'],
                imgsz=config['image_size'],
                project=str(output_dir.parent),
                name=output_dir.name,
                seed=config['seed'],
                patience=config['patience'],
                exist_ok=True,
                verbose=True,
            )

            # Extract metrics
            metrics = {}
            if hasattr(results, 'results_dict'):
                metrics = {
                    'mAP50': float(results.results_dict.get('metrics/mAP50(B)', 0)),
                    'mAP50_95': float(results.results_dict.get('metrics/mAP50-95(B)', 0)),
                    'precision': float(results.results_dict.get('metrics/precision(B)', 0)),
                    'recall': float(results.results_dict.get('metrics/recall(B)', 0)),
                }

            # Best model path
            best_model = output_dir / "weights" / "best.pt"

            # Update state
            self.state.artifacts.model.path = str(best_model)
            self.state.artifacts.model.architecture = config['architecture']
            self.state.artifacts.model.experiment_id = config['experiment_id']
            self.state.artifacts.model.metrics = metrics
            self.state.complete_stage('training')
            self.state.save(self.project_root / ".croak" / "pipeline-state.yaml")

            return {
                'success': True,
                'metrics': metrics,
                'model_path': str(best_model),
                'experiment_dir': str(output_dir),
                'experiment_id': config['experiment_id'],
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    def train_modal(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Train on Modal.com GPU.

        Args:
            config: Training configuration.

        Returns:
            Training results dict.
        """
        try:
            from croak.integrations.modal_compute import ModalTrainer
        except ImportError:
            return {
                'success': False,
                'error': "Modal integration not available.",
            }

        modal = ModalTrainer()

        # Check Modal setup
        setup = modal.check_setup()
        if not setup.get('authenticated'):
            return {
                'success': False,
                'error': "Modal not set up. Run 'pip install modal && modal token new'",
            }

        # Generate training script
        script = modal.generate_training_script(
            experiment_id=config['experiment_id'],
            architecture=config['architecture'],
            data_dir=str(Path(config['data_yaml']).parent),
            config={
                'epochs': config['epochs'],
                'batch_size': config['batch_size'],
                'image_size': config['image_size'],
                'seed': config['seed'],
                'patience': config['patience'],
            },
            gpu_type=config.get('gpu_type', 'T4'),
            timeout_hours=self.config.compute.timeout_hours,
        )

        # Save script
        scripts_dir = self.project_root / "training" / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        script_path = scripts_dir / f"{config['experiment_id']}_train.py"
        script_path.write_text(script)

        # Run training
        result = modal.run_training(str(script_path), detached=False)

        if result.get('success'):
            self.state.complete_stage('training')
            self.state.save(self.project_root / ".croak" / "pipeline-state.yaml")

        return result

    def get_experiment_list(self) -> list:
        """Get list of experiments.

        Returns:
            List of experiment info dicts.
        """
        experiments_dir = self.project_root / "training" / "experiments"
        if not experiments_dir.exists():
            return []

        experiments = []
        for exp_dir in sorted(experiments_dir.iterdir(), reverse=True):
            if exp_dir.is_dir():
                # Check for results
                best_model = exp_dir / "weights" / "best.pt"
                results_csv = exp_dir / "results.csv"

                exp_info = {
                    'id': exp_dir.name,
                    'path': str(exp_dir),
                    'has_model': best_model.exists(),
                    'has_results': results_csv.exists(),
                }

                # Try to get metrics
                if results_csv.exists():
                    try:
                        import csv
                        with open(results_csv) as f:
                            reader = csv.DictReader(f)
                            rows = list(reader)
                            if rows:
                                last = rows[-1]
                                exp_info['final_mAP50'] = float(last.get('metrics/mAP50(B)', 0))
                    except Exception:
                        pass

                experiments.append(exp_info)

        return experiments

    def resume_training(self, experiment_id: str) -> Dict[str, Any]:
        """Resume training from checkpoint.

        Args:
            experiment_id: Experiment ID to resume.

        Returns:
            Training results dict.
        """
        exp_dir = self.project_root / "training" / "experiments" / experiment_id
        if not exp_dir.exists():
            return {
                'success': False,
                'error': f"Experiment not found: {experiment_id}",
            }

        last_checkpoint = exp_dir / "weights" / "last.pt"
        if not last_checkpoint.exists():
            return {
                'success': False,
                'error': f"No checkpoint found for {experiment_id}",
            }

        try:
            from ultralytics import YOLO

            model = YOLO(str(last_checkpoint))
            results = model.train(resume=True)

            return {
                'success': True,
                'resumed_from': str(last_checkpoint),
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
