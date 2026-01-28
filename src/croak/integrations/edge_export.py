"""Edge deployment export utilities."""

from pathlib import Path
from typing import Optional
from textwrap import dedent


class EdgeExporter:
    """Export models for edge deployment."""

    def __init__(self, model_path: str):
        """Initialize exporter.

        Args:
            model_path: Path to PyTorch model weights (.pt file).
        """
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

    def export_onnx(
        self,
        output_path: Optional[str] = None,
        imgsz: int = 640,
        half: bool = True,
        simplify: bool = True,
        opset: int = 17,
        dynamic: bool = False,
    ) -> dict:
        """Export model to ONNX format.

        Args:
            output_path: Output path for ONNX file.
            imgsz: Input image size.
            half: Use FP16 precision.
            simplify: Simplify ONNX graph.
            opset: ONNX opset version.
            dynamic: Use dynamic input shapes.

        Returns:
            Export result with path and metadata.
        """
        from ultralytics import YOLO

        model = YOLO(str(self.model_path))

        # Export
        export_path = model.export(
            format="onnx",
            imgsz=imgsz,
            half=half,
            simplify=simplify,
            opset=opset,
            dynamic=dynamic,
        )

        # Move to output path if specified
        if output_path:
            output_path = Path(output_path)
            Path(export_path).rename(output_path)
            export_path = str(output_path)

        return {
            "format": "onnx",
            "path": export_path,
            "imgsz": imgsz,
            "precision": "fp16" if half else "fp32",
            "size_mb": Path(export_path).stat().st_size / (1024 * 1024),
        }

    def export_tensorrt(
        self,
        output_path: Optional[str] = None,
        imgsz: int = 640,
        half: bool = True,
        int8: bool = False,
        workspace: int = 4,
        batch: int = 1,
    ) -> dict:
        """Export model to TensorRT engine.

        Args:
            output_path: Output path for engine file.
            imgsz: Input image size.
            half: Use FP16 precision.
            int8: Use INT8 quantization.
            workspace: TensorRT workspace size in GB.
            batch: Batch size.

        Returns:
            Export result with path and metadata.
        """
        from ultralytics import YOLO

        model = YOLO(str(self.model_path))

        # Export
        export_path = model.export(
            format="engine",
            imgsz=imgsz,
            half=half,
            int8=int8,
            workspace=workspace,
            batch=batch,
        )

        # Move to output path if specified
        if output_path:
            output_path = Path(output_path)
            Path(export_path).rename(output_path)
            export_path = str(output_path)

        precision = "int8" if int8 else ("fp16" if half else "fp32")

        return {
            "format": "tensorrt",
            "path": export_path,
            "imgsz": imgsz,
            "precision": precision,
            "batch_size": batch,
            "size_mb": Path(export_path).stat().st_size / (1024 * 1024),
        }

    def generate_inference_script(
        self,
        model_format: str,
        model_path: str,
        class_names: list[str],
        confidence_threshold: float = 0.25,
    ) -> str:
        """Generate ready-to-run inference script.

        Args:
            model_format: Model format (onnx, tensorrt, pytorch).
            model_path: Path to exported model.
            class_names: List of class names.
            confidence_threshold: Detection confidence threshold.

        Returns:
            Python script content.
        """
        class_names_str = str(class_names)

        script = dedent(f'''
            #!/usr/bin/env python3
            """
            CROAK Edge Inference Script

            Model: {model_path}
            Format: {model_format}
            Classes: {len(class_names)}

            Usage:
                python inference.py --image path/to/image.jpg
                python inference.py --image path/to/image.jpg --output result.jpg
            """

            import argparse
            import cv2
            import numpy as np
            from pathlib import Path
            from ultralytics import YOLO

            # Model configuration
            MODEL_PATH = "{model_path}"
            CLASS_NAMES = {class_names_str}
            CONFIDENCE_THRESHOLD = {confidence_threshold}


            class Detector:
                """Object detector for edge inference."""

                def __init__(self, model_path: str = MODEL_PATH):
                    """Load model."""
                    self.model = YOLO(model_path)
                    self.class_names = CLASS_NAMES

                def detect(self, image_path: str, conf: float = CONFIDENCE_THRESHOLD) -> list:
                    """Run detection on image.

                    Args:
                        image_path: Path to input image.
                        conf: Confidence threshold.

                    Returns:
                        List of detection dicts.
                    """
                    results = self.model(image_path, conf=conf, verbose=False)

                    detections = []
                    for result in results:
                        for box in result.boxes:
                            detections.append({{
                                "class": self.class_names[int(box.cls[0])],
                                "class_id": int(box.cls[0]),
                                "confidence": float(box.conf[0]),
                                "bbox": box.xyxy[0].tolist(),  # [x1, y1, x2, y2]
                            }})

                    return detections

                def detect_and_draw(
                    self,
                    image_path: str,
                    output_path: str,
                    conf: float = CONFIDENCE_THRESHOLD,
                ) -> list:
                    """Run detection and save annotated image.

                    Args:
                        image_path: Path to input image.
                        output_path: Path to save annotated image.
                        conf: Confidence threshold.

                    Returns:
                        List of detection dicts.
                    """
                    # Run detection
                    results = self.model(image_path, conf=conf, verbose=False)

                    # Get annotated image
                    annotated = results[0].plot()

                    # Save
                    cv2.imwrite(output_path, annotated)

                    # Return detections
                    return self.detect(image_path, conf)


            def main():
                parser = argparse.ArgumentParser(description="CROAK Edge Inference")
                parser.add_argument("--image", "-i", required=True, help="Input image path")
                parser.add_argument("--output", "-o", help="Output image path (optional)")
                parser.add_argument("--conf", "-c", type=float, default=CONFIDENCE_THRESHOLD,
                                    help="Confidence threshold")
                parser.add_argument("--json", action="store_true", help="Output as JSON")
                args = parser.parse_args()

                # Initialize detector
                detector = Detector()

                # Run inference
                if args.output:
                    detections = detector.detect_and_draw(args.image, args.output, args.conf)
                    print(f"Saved annotated image to {{args.output}}")
                else:
                    detections = detector.detect(args.image, args.conf)

                # Output results
                if args.json:
                    import json
                    print(json.dumps(detections, indent=2))
                else:
                    print(f"\\nDetected {{len(detections)}} objects:\\n")
                    for det in detections:
                        bbox = det["bbox"]
                        print(f"  {{det['class']}}: {{det['confidence']:.2f}}")
                        print(f"    Box: [{{bbox[0]:.0f}}, {{bbox[1]:.0f}}, {{bbox[2]:.0f}}, {{bbox[3]:.0f}}]")


            if __name__ == "__main__":
                main()
        ''')

        return script.strip()

    def benchmark(
        self,
        test_images: list[str],
        warmup: int = 10,
        iterations: int = 100,
    ) -> dict:
        """Benchmark model inference speed.

        Args:
            test_images: List of test image paths.
            warmup: Number of warmup iterations.
            iterations: Number of benchmark iterations.

        Returns:
            Benchmark results.
        """
        import time
        from ultralytics import YOLO

        model = YOLO(str(self.model_path))

        # Use first image for benchmarking
        test_image = test_images[0] if test_images else None
        if not test_image:
            return {"error": "No test images provided"}

        # Warmup
        for _ in range(warmup):
            model(test_image, verbose=False)

        # Benchmark
        latencies = []
        for _ in range(iterations):
            start = time.perf_counter()
            model(test_image, verbose=False)
            latencies.append((time.perf_counter() - start) * 1000)  # ms

        import statistics

        return {
            "latency_ms": {
                "mean": round(statistics.mean(latencies), 2),
                "std": round(statistics.stdev(latencies), 2),
                "min": round(min(latencies), 2),
                "max": round(max(latencies), 2),
                "p95": round(sorted(latencies)[int(len(latencies) * 0.95)], 2),
            },
            "throughput_fps": round(1000 / statistics.mean(latencies), 1),
            "iterations": iterations,
        }
