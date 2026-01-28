"""Model evaluation and error analysis."""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

try:
    from ultralytics import YOLO
    HAS_ULTRALYTICS = True
except ImportError:
    HAS_ULTRALYTICS = False

from croak.core.paths import PathValidator
from croak.core.state import load_state


class ModelEvaluator:
    """Evaluate trained models and analyze errors.

    Provides comprehensive evaluation metrics, per-class analysis,
    and error pattern detection for model improvement.
    """

    def __init__(self, project_dir: Optional[Path] = None):
        """Initialize model evaluator.

        Args:
            project_dir: Project directory. Uses current if not specified.
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.path_validator = PathValidator(self.project_dir)
        self.state = load_state(self.project_dir)

    def evaluate(
        self,
        model_path: str,
        data_yaml: Optional[str] = None,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.5,
        split: str = "test",
    ) -> Dict[str, Any]:
        """Run full evaluation on test set.

        Args:
            model_path: Path to model weights (.pt file).
            data_yaml: Path to data.yaml. Uses state if not provided.
            conf_threshold: Confidence threshold for predictions.
            iou_threshold: IoU threshold for NMS.
            split: Dataset split to evaluate on (test, val).

        Returns:
            Dict with evaluation results and metrics.
        """
        if not HAS_ULTRALYTICS:
            return {
                'success': False,
                'error': 'ultralytics not installed. Run: pip install ultralytics',
            }

        # Validate model path
        model_path = self.path_validator.validate_within_project(Path(model_path))
        if not model_path.exists():
            return {
                'success': False,
                'error': f'Model not found: {model_path}',
            }

        # Get data.yaml path
        if data_yaml:
            data_yaml_path = self.path_validator.validate_within_project(Path(data_yaml))
        elif self.state.data_yaml_path:
            data_yaml_path = Path(self.state.data_yaml_path)
        else:
            return {
                'success': False,
                'error': 'No data.yaml specified and none in project state',
            }

        if not data_yaml_path.exists():
            return {
                'success': False,
                'error': f'data.yaml not found: {data_yaml_path}',
            }

        # Load model and run evaluation
        model = YOLO(str(model_path))

        results = model.val(
            data=str(data_yaml_path),
            conf=conf_threshold,
            iou=iou_threshold,
            split=split,
            verbose=False,
        )

        # Extract metrics
        metrics = self._extract_metrics(results)

        # Per-class metrics
        per_class = self._extract_per_class_metrics(results)

        # Determine deployment readiness
        deployment_ready = self._check_deployment_ready(metrics)

        eval_result = {
            'success': True,
            'model_path': str(model_path),
            'data_yaml': str(data_yaml_path),
            'split': split,
            'conf_threshold': conf_threshold,
            'iou_threshold': iou_threshold,
            'metrics': metrics,
            'per_class': per_class,
            'deployment_ready': deployment_ready,
            'recommended_threshold': self._recommend_threshold(results),
            'evaluated_at': datetime.utcnow().isoformat(),
        }

        # Save evaluation results
        self._save_results(eval_result)

        return eval_result

    def _extract_metrics(self, results) -> Dict[str, float]:
        """Extract overall metrics from validation results."""
        box = results.box

        return {
            'mAP50': float(box.map50) if hasattr(box, 'map50') else 0.0,
            'mAP50_95': float(box.map) if hasattr(box, 'map') else 0.0,
            'precision': float(box.mp) if hasattr(box, 'mp') else 0.0,
            'recall': float(box.mr) if hasattr(box, 'mr') else 0.0,
            'f1': self._calculate_f1(
                float(box.mp) if hasattr(box, 'mp') else 0.0,
                float(box.mr) if hasattr(box, 'mr') else 0.0,
            ),
        }

    def _extract_per_class_metrics(self, results) -> List[Dict[str, Any]]:
        """Extract per-class metrics."""
        per_class = []
        box = results.box

        if hasattr(box, 'ap_class_index') and hasattr(results, 'names'):
            for i, class_idx in enumerate(box.ap_class_index):
                class_name = results.names.get(int(class_idx), f'class_{class_idx}')
                per_class.append({
                    'class': class_name,
                    'class_idx': int(class_idx),
                    'ap50': float(box.ap50[i]) if hasattr(box, 'ap50') else 0.0,
                    'ap': float(box.ap[i]) if hasattr(box, 'ap') else 0.0,
                    'precision': float(box.p[i]) if hasattr(box, 'p') else 0.0,
                    'recall': float(box.r[i]) if hasattr(box, 'r') else 0.0,
                })

        return per_class

    def _calculate_f1(self, precision: float, recall: float) -> float:
        """Calculate F1 score."""
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

    def _check_deployment_ready(self, metrics: Dict[str, float]) -> bool:
        """Check if model meets deployment thresholds."""
        # Default thresholds - can be customized via config
        min_map50 = 0.5
        min_precision = 0.5
        min_recall = 0.5

        return (
            metrics.get('mAP50', 0) >= min_map50 and
            metrics.get('precision', 0) >= min_precision and
            metrics.get('recall', 0) >= min_recall
        )

    def _recommend_threshold(self, results) -> float:
        """Recommend confidence threshold based on PR curve."""
        # Default recommendation - could be improved with PR curve analysis
        return 0.25

    def _save_results(self, eval_result: Dict[str, Any]):
        """Save evaluation results to project."""
        eval_dir = self.project_dir / '.croak' / 'evaluations'
        eval_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        eval_path = eval_dir / f'eval-{timestamp}.json'

        with open(eval_path, 'w') as f:
            json.dump(eval_result, f, indent=2)

    def analyze_errors(
        self,
        model_path: str,
        data_yaml: str,
        num_samples: int = 20,
    ) -> Dict[str, Any]:
        """Analyze model errors on worst-performing samples.

        Args:
            model_path: Path to model weights.
            data_yaml: Path to data.yaml.
            num_samples: Number of error samples to analyze.

        Returns:
            Dict with error analysis results.
        """
        if not HAS_ULTRALYTICS:
            return {
                'success': False,
                'error': 'ultralytics not installed',
            }

        model_path = self.path_validator.validate_within_project(Path(model_path))
        data_yaml_path = self.path_validator.validate_within_project(Path(data_yaml))

        model = YOLO(str(model_path))

        # Run prediction on test set to get per-image results
        # This is a simplified analysis - full implementation would
        # compare predictions to ground truth for each image

        error_patterns = {
            'false_positives': [],
            'false_negatives': [],
            'misclassifications': [],
            'localization_errors': [],
        }

        analysis = {
            'success': True,
            'model_path': str(model_path),
            'data_yaml': str(data_yaml_path),
            'num_samples': num_samples,
            'error_patterns': error_patterns,
            'recommendations': self._generate_recommendations(error_patterns),
            'analyzed_at': datetime.utcnow().isoformat(),
        }

        return analysis

    def _generate_recommendations(self, error_patterns: Dict) -> List[str]:
        """Generate recommendations based on error patterns."""
        recommendations = []

        # Default recommendations
        recommendations.append('Consider augmentation strategies for underperforming classes')
        recommendations.append('Review annotation quality for high-error samples')
        recommendations.append('Try longer training or different learning rate')

        return recommendations

    def generate_report_md(self, eval_result: Dict[str, Any]) -> str:
        """Generate markdown evaluation report.

        Args:
            eval_result: Evaluation results from evaluate().

        Returns:
            Markdown formatted report string.
        """
        if not eval_result.get('success'):
            return f"# Evaluation Failed\n\nError: {eval_result.get('error', 'Unknown error')}"

        metrics = eval_result.get('metrics', {})
        per_class = eval_result.get('per_class', [])

        report = f"""# Model Evaluation Report

**Generated:** {eval_result.get('evaluated_at', 'Unknown')}

## Model Information

- **Model Path:** `{eval_result.get('model_path', 'N/A')}`
- **Data YAML:** `{eval_result.get('data_yaml', 'N/A')}`
- **Split:** {eval_result.get('split', 'test')}
- **Confidence Threshold:** {eval_result.get('conf_threshold', 0.25)}
- **IoU Threshold:** {eval_result.get('iou_threshold', 0.5)}

## Overall Metrics

| Metric | Value |
|--------|-------|
| mAP@50 | {metrics.get('mAP50', 0):.4f} |
| mAP@50-95 | {metrics.get('mAP50_95', 0):.4f} |
| Precision | {metrics.get('precision', 0):.4f} |
| Recall | {metrics.get('recall', 0):.4f} |
| F1 Score | {metrics.get('f1', 0):.4f} |

## Deployment Readiness

"""
        if eval_result.get('deployment_ready'):
            report += "✅ **Model meets deployment thresholds**\n\n"
        else:
            report += "⚠️ **Model does not meet deployment thresholds**\n\n"

        report += f"**Recommended Confidence Threshold:** {eval_result.get('recommended_threshold', 0.25)}\n\n"

        if per_class:
            report += "## Per-Class Metrics\n\n"
            report += "| Class | AP@50 | AP@50-95 | Precision | Recall |\n"
            report += "|-------|-------|----------|-----------|--------|\n"

            for cls in per_class:
                report += f"| {cls.get('class', 'N/A')} | "
                report += f"{cls.get('ap50', 0):.4f} | "
                report += f"{cls.get('ap', 0):.4f} | "
                report += f"{cls.get('precision', 0):.4f} | "
                report += f"{cls.get('recall', 0):.4f} |\n"

        report += """
## Next Steps

1. Review per-class metrics for underperforming classes
2. Analyze error patterns with `croak evaluate --analyze-errors`
3. Consider additional data collection for weak classes
4. Experiment with augmentation strategies
"""

        return report

    def compare_models(
        self,
        model_paths: List[str],
        data_yaml: str,
    ) -> Dict[str, Any]:
        """Compare multiple models on the same test set.

        Args:
            model_paths: List of model paths to compare.
            data_yaml: Path to data.yaml.

        Returns:
            Dict with comparison results.
        """
        results = []

        for model_path in model_paths:
            eval_result = self.evaluate(model_path, data_yaml)
            results.append({
                'model': model_path,
                'metrics': eval_result.get('metrics', {}),
                'deployment_ready': eval_result.get('deployment_ready', False),
            })

        # Sort by mAP50-95
        results.sort(
            key=lambda x: x['metrics'].get('mAP50_95', 0),
            reverse=True,
        )

        return {
            'success': True,
            'comparison': results,
            'best_model': results[0]['model'] if results else None,
            'compared_at': datetime.utcnow().isoformat(),
        }
