"""Modal.com GPU compute integration."""

import subprocess
from pathlib import Path
from typing import Optional
from textwrap import dedent


class ModalTrainer:
    """Interface for Modal.com GPU compute."""

    GPU_RATES = {
        "T4": 0.59,
        "A10G": 1.10,
        "A100": 2.78,
        "A100-80GB": 3.22,
        "H100": 4.76,
    }

    def __init__(self):
        """Initialize Modal trainer."""
        self._modal_available = None

    def check_setup(self) -> dict:
        """Verify Modal CLI is installed and authenticated.

        Returns:
            Dict with status information.
        """
        result = {"installed": False, "authenticated": False, "error": None}

        # Check if modal is installed
        try:
            import modal

            result["installed"] = True
        except ImportError:
            result["error"] = "Modal not installed. Run: pip install modal"
            return result

        # Check if authenticated
        try:
            proc = subprocess.run(
                ["modal", "token", "show"],
                capture_output=True,
                text=True,
            )
            result["authenticated"] = proc.returncode == 0
            if not result["authenticated"]:
                result["error"] = "Modal not authenticated. Run: modal token new"
        except FileNotFoundError:
            result["error"] = "Modal CLI not found. Run: pip install modal"

        return result

    def install(self) -> bool:
        """Install Modal package.

        Returns:
            True if installation successful.
        """
        try:
            subprocess.run(
                ["pip", "install", "modal"],
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def authenticate(self) -> bool:
        """Open browser for Modal authentication.

        Returns:
            True if authentication started.
        """
        try:
            subprocess.run(["modal", "token", "new"], check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def generate_training_script(
        self,
        experiment_id: str,
        architecture: str,
        data_dir: str,
        config: dict,
        gpu_type: str = "T4",
        timeout_hours: int = 4,
    ) -> str:
        """Generate Modal training script.

        Args:
            experiment_id: Unique experiment identifier.
            architecture: Model architecture (e.g., yolov8s).
            data_dir: Path to data directory.
            config: Training configuration dict.
            gpu_type: GPU type (T4, A10G, A100).
            timeout_hours: Maximum training time.

        Returns:
            Python script content.
        """
        script = dedent(f'''
            """
            CROAK Training Script for Modal.com
            Experiment: {experiment_id}
            Architecture: {architecture}

            Run with: modal run {experiment_id}_train.py
            """

            import modal

            app = modal.App("croak-{experiment_id}")

            # Training environment image
            training_image = modal.Image.debian_slim(python_version="3.11").pip_install(
                "ultralytics>=8.0.0",
                "torch>=2.0.0",
                "torchvision>=0.15.0",
                "mlflow>=2.0.0",
                "pyyaml>=6.0"
            )

            # Mount local data
            data_mount = modal.Mount.from_local_dir(
                "{data_dir}",
                remote_path="/data"
            )

            # Persistent volume for results
            results_volume = modal.Volume.from_name(
                "croak-results-{experiment_id}",
                create_if_missing=True
            )

            @app.function(
                gpu="{gpu_type}",
                timeout={timeout_hours * 3600},
                image=training_image,
                mounts=[data_mount],
                volumes={{"/results": results_volume}}
            )
            def train():
                from ultralytics import YOLO
                import json

                print("Starting training...")
                print(f"Architecture: {architecture}")

                # Load pretrained model
                model = YOLO("{architecture}.pt")

                # Training configuration
                config = {config}

                # Run training
                results = model.train(
                    data="/data/data.yaml",
                    epochs=config["epochs"],
                    batch=config["batch_size"],
                    imgsz=config["image_size"],
                    project="/results",
                    name="{experiment_id}",
                    seed=config.get("seed", 42),
                    patience=config.get("patience", 20),
                    exist_ok=True
                )

                # Save metrics
                metrics = {{
                    "mAP50": float(results.results_dict.get("metrics/mAP50(B)", 0)),
                    "mAP50_95": float(results.results_dict.get("metrics/mAP50-95(B)", 0)),
                    "precision": float(results.results_dict.get("metrics/precision(B)", 0)),
                    "recall": float(results.results_dict.get("metrics/recall(B)", 0)),
                }}

                with open("/results/{experiment_id}/metrics.json", "w") as f:
                    json.dump(metrics, f, indent=2)

                # Commit results to volume
                results_volume.commit()

                print(f"Training complete!")
                print(f"mAP@50: {{metrics['mAP50']:.4f}}")
                print(f"Best weights: /results/{experiment_id}/weights/best.pt")

                return metrics

            @app.local_entrypoint()
            def main():
                print("Launching training on Modal.com...")
                metrics = train.remote()
                print(f"\\nTraining complete!")
                print(f"Results: {{metrics}}")
        ''')

        return script.strip()

    def estimate_cost(
        self,
        gpu_type: str,
        estimated_hours: float,
    ) -> dict:
        """Estimate training cost on Modal.

        Args:
            gpu_type: GPU type (T4, A10G, A100).
            estimated_hours: Estimated training time in hours.

        Returns:
            Cost estimation dict.
        """
        rate = self.GPU_RATES.get(gpu_type, 1.0)
        cost = rate * estimated_hours

        return {
            "gpu_type": gpu_type,
            "rate_per_hour": rate,
            "estimated_hours": estimated_hours,
            "estimated_cost_usd": round(cost, 2),
            "free_credits": "$30 for new accounts",
            "note": "Actual cost may be less if training completes early",
        }

    def estimate_training_time(
        self,
        architecture: str,
        num_images: int,
        epochs: int,
        gpu_type: str = "T4",
    ) -> float:
        """Estimate training time in hours.

        Args:
            architecture: Model architecture.
            num_images: Number of training images.
            epochs: Number of training epochs.
            gpu_type: GPU type.

        Returns:
            Estimated hours.
        """
        # Base time per epoch (seconds) on T4
        base_times = {
            "yolov8n": 30,
            "yolov8s": 60,
            "yolov8m": 120,
            "yolov8l": 180,
            "yolov11n": 25,
            "yolov11s": 55,
            "rt-detr": 90,
        }

        # GPU speed multipliers relative to T4
        gpu_speeds = {
            "T4": 1.0,
            "A10G": 1.5,
            "A100": 2.5,
            "H100": 4.0,
        }

        base_time = base_times.get(architecture, 60)
        gpu_speed = gpu_speeds.get(gpu_type, 1.0)

        # Scale by dataset size (roughly linear with diminishing returns)
        size_factor = (num_images / 1000) ** 0.8

        # Calculate total time
        time_per_epoch = base_time * size_factor / gpu_speed
        total_seconds = time_per_epoch * epochs

        # Add overhead (model download, setup, etc.)
        total_seconds += 300  # 5 minutes overhead

        return round(total_seconds / 3600, 2)

    def run_training(self, script_path: str, detached: bool = False) -> dict:
        """Execute training script on Modal.

        Args:
            script_path: Path to Modal training script.
            detached: Run in background if True.

        Returns:
            Execution result.
        """
        cmd = ["modal", "run"]
        if detached:
            cmd.append("--detach")
        cmd.append(script_path)

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=not detached,
                text=True,
            )
            return {
                "success": True,
                "output": result.stdout if not detached else "Running in background",
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": e.stderr,
            }
