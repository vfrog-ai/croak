"""Model deployment to various targets."""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import shutil

try:
    from ultralytics import YOLO
    HAS_ULTRALYTICS = True
except ImportError:
    HAS_ULTRALYTICS = False

from croak.core.paths import PathValidator
from croak.core.commands import SecureRunner
from croak.core.state import load_state


class ModelDeployer:
    """Deploy trained models to various targets.

    Supports export to multiple formats and deployment to
    Modal.com serverless inference endpoints.
    """

    # Supported export formats
    EXPORT_FORMATS = {
        'onnx': {
            'description': 'ONNX format for cross-platform inference',
            'suffix': '.onnx',
        },
        'torchscript': {
            'description': 'TorchScript for PyTorch deployment',
            'suffix': '.torchscript',
        },
        'coreml': {
            'description': 'CoreML for iOS/macOS deployment',
            'suffix': '.mlpackage',
        },
        'tflite': {
            'description': 'TFLite for mobile/edge devices',
            'suffix': '.tflite',
        },
        'engine': {
            'description': 'TensorRT for NVIDIA GPUs',
            'suffix': '.engine',
        },
        'openvino': {
            'description': 'OpenVINO for Intel hardware',
            'suffix': '_openvino_model',
        },
    }

    def __init__(self, project_dir: Optional[Path] = None):
        """Initialize model deployer.

        Args:
            project_dir: Project directory. Uses current if not specified.
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.path_validator = PathValidator(self.project_dir)
        self.state = load_state(self.project_dir)

    def export_model(
        self,
        model_path: str,
        format: str,
        output_dir: Optional[str] = None,
        imgsz: int = 640,
        half: bool = False,
        dynamic: bool = False,
        simplify: bool = True,
    ) -> Dict[str, Any]:
        """Export model to specified format.

        Args:
            model_path: Path to model weights (.pt file).
            format: Export format (onnx, torchscript, coreml, tflite, engine, openvino).
            output_dir: Output directory for exported model.
            imgsz: Input image size.
            half: Use FP16 precision.
            dynamic: Enable dynamic input shapes (ONNX).
            simplify: Simplify ONNX model.

        Returns:
            Dict with export results.
        """
        if not HAS_ULTRALYTICS:
            return {
                'success': False,
                'error': 'ultralytics not installed. Run: pip install ultralytics',
            }

        if format not in self.EXPORT_FORMATS:
            return {
                'success': False,
                'error': f'Unsupported format: {format}. Supported: {list(self.EXPORT_FORMATS.keys())}',
            }

        # Validate model path
        model_path = self.path_validator.validate_within_project(Path(model_path))
        if not model_path.exists():
            return {
                'success': False,
                'error': f'Model not found: {model_path}',
            }

        # Set output directory
        if output_dir:
            out_dir = self.path_validator.validate_within_project(Path(output_dir))
        else:
            out_dir = self.project_dir / 'exports' / format
        out_dir.mkdir(parents=True, exist_ok=True)

        # Load and export model
        model = YOLO(str(model_path))

        export_kwargs = {
            'format': format,
            'imgsz': imgsz,
            'half': half,
        }

        if format == 'onnx':
            export_kwargs['dynamic'] = dynamic
            export_kwargs['simplify'] = simplify

        try:
            exported_path = model.export(**export_kwargs)

            # Move to output directory if different
            exported_path = Path(exported_path)
            if exported_path.parent != out_dir:
                final_path = out_dir / exported_path.name
                if exported_path.is_dir():
                    shutil.copytree(exported_path, final_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(exported_path, final_path)
                exported_path = final_path

            result = {
                'success': True,
                'format': format,
                'exported_path': str(exported_path),
                'input_model': str(model_path),
                'imgsz': imgsz,
                'half': half,
                'exported_at': datetime.utcnow().isoformat(),
            }

            # Save export record
            self._save_export_record(result)

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'format': format,
            }

    def _save_export_record(self, result: Dict[str, Any]):
        """Save export record for tracking."""
        exports_dir = self.project_dir / '.croak' / 'exports'
        exports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        record_path = exports_dir / f'export-{result["format"]}-{timestamp}.json'

        with open(record_path, 'w') as f:
            json.dump(result, f, indent=2)

    def deploy_modal(
        self,
        model_path: str,
        app_name: str,
        gpu: str = "T4",
        concurrency: int = 10,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """Deploy model as Modal.com serverless endpoint.

        Args:
            model_path: Path to model weights.
            app_name: Name for the Modal app.
            gpu: GPU type (T4, A10G, A100).
            concurrency: Max concurrent requests.
            timeout: Request timeout in seconds.

        Returns:
            Dict with deployment results.
        """
        model_path = self.path_validator.validate_within_project(Path(model_path))
        if not model_path.exists():
            return {
                'success': False,
                'error': f'Model not found: {model_path}',
            }

        # Generate Modal deployment script
        modal_script = self._generate_modal_script(
            model_path=str(model_path),
            app_name=app_name,
            gpu=gpu,
            concurrency=concurrency,
            timeout=timeout,
        )

        # Save Modal script
        deploy_dir = self.project_dir / 'deploy'
        deploy_dir.mkdir(parents=True, exist_ok=True)
        script_path = deploy_dir / f'{app_name}_modal.py'

        with open(script_path, 'w') as f:
            f.write(modal_script)

        # Deploy to Modal
        try:
            result = SecureRunner.run(
                ['modal', 'deploy', str(script_path)],
                cwd=self.project_dir,
                timeout=600,
            )

            if result.returncode == 0:
                # Parse endpoint URL from output
                endpoint_url = self._parse_modal_endpoint(result.stdout)

                deploy_result = {
                    'success': True,
                    'app_name': app_name,
                    'endpoint_url': endpoint_url,
                    'script_path': str(script_path),
                    'gpu': gpu,
                    'deployed_at': datetime.utcnow().isoformat(),
                }

                self._save_deployment_record(deploy_result)
                return deploy_result
            else:
                return {
                    'success': False,
                    'error': result.stderr or 'Modal deployment failed',
                    'stdout': result.stdout,
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'script_path': str(script_path),
                'note': 'Script generated - deploy manually with: modal deploy ' + str(script_path),
            }

    def _generate_modal_script(
        self,
        model_path: str,
        app_name: str,
        gpu: str,
        concurrency: int,
        timeout: int,
    ) -> str:
        """Generate Modal deployment script."""
        return f'''"""Modal.com deployment for {app_name}."""

import modal

app = modal.App("{app_name}")

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "ultralytics>=8.0.0",
    "opencv-python-headless",
)

volume = modal.Volume.from_name("croak-models", create_if_missing=True)

@app.cls(
    image=image,
    gpu="{gpu}",
    volumes={{"/models": volume}},
    concurrency_limit={concurrency},
    timeout={timeout},
)
class Detector:
    @modal.enter()
    def load_model(self):
        from ultralytics import YOLO
        self.model = YOLO("/models/{Path(model_path).name}")

    @modal.method()
    def predict(self, image_bytes: bytes, conf: float = 0.25) -> dict:
        """Run inference on image bytes."""
        import numpy as np
        import cv2

        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Run inference
        results = self.model(img, conf=conf, verbose=False)

        # Format results
        detections = []
        for r in results:
            for box in r.boxes:
                detections.append({{
                    "class": r.names[int(box.cls)],
                    "confidence": float(box.conf),
                    "bbox": box.xyxy[0].tolist(),
                }})

        return {{"detections": detections, "count": len(detections)}}

    @modal.web_endpoint()
    def health(self):
        """Health check endpoint."""
        return {{"status": "healthy", "model": "{Path(model_path).name}"}}


@app.local_entrypoint()
def main():
    """Upload model to volume."""
    import shutil
    volume.put_file("{model_path}", "/{Path(model_path).name}")
    print(f"Model uploaded to volume")
'''

    def _parse_modal_endpoint(self, stdout: str) -> Optional[str]:
        """Parse endpoint URL from Modal deploy output."""
        # Look for URL pattern in output
        import re
        url_pattern = r'https://[a-zA-Z0-9-]+\.modal\.run'
        match = re.search(url_pattern, stdout)
        return match.group(0) if match else None

    def _save_deployment_record(self, result: Dict[str, Any]):
        """Save deployment record."""
        deploy_dir = self.project_dir / '.croak' / 'deployments'
        deploy_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        record_path = deploy_dir / f'deploy-{result["app_name"]}-{timestamp}.json'

        with open(record_path, 'w') as f:
            json.dump(result, f, indent=2)

    def list_exports(self) -> List[Dict[str, Any]]:
        """List all exported models."""
        exports_dir = self.project_dir / '.croak' / 'exports'
        if not exports_dir.exists():
            return []

        exports = []
        for f in exports_dir.glob('export-*.json'):
            with open(f) as fp:
                exports.append(json.load(fp))

        return sorted(exports, key=lambda x: x.get('exported_at', ''), reverse=True)

    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all deployments."""
        deploy_dir = self.project_dir / '.croak' / 'deployments'
        if not deploy_dir.exists():
            return []

        deployments = []
        for f in deploy_dir.glob('deploy-*.json'):
            with open(f) as fp:
                deployments.append(json.load(fp))

        return sorted(deployments, key=lambda x: x.get('deployed_at', ''), reverse=True)

    def generate_deployment_package(
        self,
        model_path: str,
        include_formats: List[str] = None,
        include_sample_code: bool = True,
    ) -> Dict[str, Any]:
        """Generate a deployment package with model and inference code.

        Args:
            model_path: Path to model weights.
            include_formats: Export formats to include. Defaults to ['onnx'].
            include_sample_code: Include sample inference code.

        Returns:
            Dict with package information.
        """
        if include_formats is None:
            include_formats = ['onnx']

        model_path = self.path_validator.validate_within_project(Path(model_path))
        if not model_path.exists():
            return {
                'success': False,
                'error': f'Model not found: {model_path}',
            }

        # Create package directory
        package_dir = self.project_dir / 'deployment-package'
        package_dir.mkdir(parents=True, exist_ok=True)

        # Copy original model
        shutil.copy2(model_path, package_dir / model_path.name)

        # Export to requested formats
        exported = []
        for fmt in include_formats:
            result = self.export_model(
                str(model_path),
                fmt,
                output_dir=str(package_dir / 'exports'),
            )
            if result.get('success'):
                exported.append(result)

        # Generate sample code
        if include_sample_code:
            self._generate_sample_code(package_dir, model_path.name)

        # Generate README
        self._generate_package_readme(package_dir, model_path.name, exported)

        return {
            'success': True,
            'package_dir': str(package_dir),
            'model': model_path.name,
            'exports': exported,
            'created_at': datetime.utcnow().isoformat(),
        }

    def _generate_sample_code(self, package_dir: Path, model_name: str):
        """Generate sample inference code."""
        samples_dir = package_dir / 'samples'
        samples_dir.mkdir(exist_ok=True)

        # Python inference sample
        python_sample = f'''"""Sample inference code for {model_name}."""

from ultralytics import YOLO
import cv2

# Load model
model = YOLO("{model_name}")

# Run inference on image
results = model("path/to/image.jpg")

# Process results
for result in results:
    boxes = result.boxes
    for box in boxes:
        # Get box coordinates
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        confidence = float(box.conf)
        class_id = int(box.cls)
        class_name = result.names[class_id]

        print(f"Detected {{class_name}} with confidence {{confidence:.2f}}")
        print(f"  Bounding box: ({{x1:.0f}}, {{y1:.0f}}) - ({{x2:.0f}}, {{y2:.0f}})")

# Save annotated image
results[0].save("output.jpg")
'''
        with open(samples_dir / 'inference.py', 'w') as f:
            f.write(python_sample)

        # ONNX inference sample
        onnx_sample = f'''"""ONNX inference sample for {model_name}."""

import onnxruntime as ort
import cv2
import numpy as np

# Load ONNX model
session = ort.InferenceSession("exports/{model_name.replace('.pt', '.onnx')}")

# Prepare input
img = cv2.imread("path/to/image.jpg")
img_resized = cv2.resize(img, (640, 640))
img_normalized = img_resized.astype(np.float32) / 255.0
img_transposed = np.transpose(img_normalized, (2, 0, 1))
img_batch = np.expand_dims(img_transposed, axis=0)

# Run inference
outputs = session.run(None, {{"images": img_batch}})

# Process outputs (format depends on model version)
print(f"Output shape: {{outputs[0].shape}}")
'''
        with open(samples_dir / 'inference_onnx.py', 'w') as f:
            f.write(onnx_sample)

    def _generate_package_readme(
        self,
        package_dir: Path,
        model_name: str,
        exports: List[Dict],
    ):
        """Generate README for deployment package."""
        readme = f"""# Deployment Package: {model_name}

## Contents

- `{model_name}` - Original PyTorch model weights
- `exports/` - Exported model formats
- `samples/` - Sample inference code

## Exported Formats

"""
        for exp in exports:
            readme += f"- **{exp['format']}**: `{exp['exported_path']}`\n"

        readme += """
## Quick Start

### Python with Ultralytics

```python
from ultralytics import YOLO

model = YOLO("{model_name}")
results = model("image.jpg")
```

### ONNX Runtime

See `samples/inference_onnx.py` for ONNX inference example.

## Requirements

- Python 3.8+
- ultralytics>=8.0.0
- opencv-python
- onnxruntime (for ONNX inference)

## Generated by CROAK

This deployment package was generated by CROAK - Computer Recognition Orchestration Agent Kit.
"""

        with open(package_dir / 'README.md', 'w') as f:
            f.write(readme)
