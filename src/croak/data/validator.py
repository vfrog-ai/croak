"""Data validation for CROAK."""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from PIL import Image

from croak.data.scanner import scan_directory, SUPPORTED_IMAGE_FORMATS


@dataclass
class ValidationResult:
    """Result of data validation."""
    passed: bool = True
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)

    def add_warning(self, msg: str) -> None:
        """Add a warning message."""
        self.warnings.append(msg)

    def add_error(self, msg: str) -> None:
        """Add an error message and mark as failed."""
        self.errors.append(msg)
        self.passed = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'passed': self.passed,
            'warnings': self.warnings,
            'errors': self.errors,
            'statistics': self.statistics,
            'warning_count': len(self.warnings),
            'error_count': len(self.errors),
        }


class DataValidator:
    """Validate dataset for training readiness.

    Performs comprehensive validation including:
    - Image integrity checks
    - Annotation format validation
    - Class distribution analysis
    - Duplicate detection
    - Size and quality checks
    """

    # Validation thresholds
    MIN_IMAGES = 100
    MIN_INSTANCES_PER_CLASS = 50
    MAX_IMBALANCE_RATIO = 10
    MIN_IMAGE_SIZE = 320
    MAX_IMAGE_SIZE = 4096
    MIN_ANNOTATION_COVERAGE = 0.9  # 90%

    def __init__(self, data_dir: Path):
        """Initialize data validator.

        Args:
            data_dir: Path to data directory.
        """
        self.data_dir = Path(data_dir)
        self.images_dir = self.data_dir / "raw"
        self.labels_dir = self.data_dir / "annotations"
        self.processed_dir = self.data_dir / "processed"

    def validate_all(self) -> ValidationResult:
        """Run all validation checks.

        Returns:
            ValidationResult with all findings.
        """
        result = ValidationResult()

        # Check images
        self._validate_images(result)

        # Check annotations (only if images found)
        if result.statistics.get('images', {}).get('total_images', 0) > 0:
            self._validate_annotations(result)

            # Check class distribution (only if annotations found)
            if result.statistics.get('annotation_coverage', 0) > 0:
                self._validate_class_distribution(result)

        # Check for duplicates
        self._check_duplicates(result)

        return result

    def _validate_images(self, result: ValidationResult) -> None:
        """Validate image files."""
        if not self.images_dir.exists():
            result.add_error(f"Images directory not found: {self.images_dir}")
            return

        scan = scan_directory(self.images_dir)
        result.statistics['images'] = scan

        # Check count
        if scan['total_images'] == 0:
            result.add_error("No images found in data/raw/")
            return

        if scan['total_images'] < self.MIN_IMAGES:
            result.add_warning(
                f"Only {scan['total_images']} images found. "
                f"Recommend {self.MIN_IMAGES}+ for reliable training."
            )

        # Check corrupt images
        if scan.get('corrupt'):
            corrupt_count = len(scan['corrupt'])
            if corrupt_count > scan['total_images'] * 0.1:  # >10% corrupt
                result.add_error(
                    f"{corrupt_count} corrupt images found ({corrupt_count / scan['total_images'] * 100:.0f}%). "
                    f"Please remove or fix corrupt files."
                )
            else:
                sample = [c[0] for c in scan['corrupt'][:3]]
                result.add_warning(
                    f"{corrupt_count} corrupt images found. Examples: {sample}"
                )

        # Check sizes
        if scan.get('size_stats'):
            min_w, min_h = scan['size_stats']['min']
            max_w, max_h = scan['size_stats']['max']

            min_dim = min(min_w, min_h)
            max_dim = max(max_w, max_h)

            if min_dim < self.MIN_IMAGE_SIZE:
                result.add_warning(
                    f"Some images smaller than {self.MIN_IMAGE_SIZE}px. "
                    f"Minimum found: {min_dim}px. Small images may hurt detection accuracy."
                )

            if max_dim > self.MAX_IMAGE_SIZE:
                result.add_warning(
                    f"Some images larger than {self.MAX_IMAGE_SIZE}px. "
                    f"Maximum found: {max_dim}px. Consider resizing for faster training."
                )

            # Check for extreme aspect ratios
            aspect_ratios = [w / h for w, h in scan['sizes'] if h > 0]
            if aspect_ratios:
                min_ar = min(aspect_ratios)
                max_ar = max(aspect_ratios)
                if min_ar < 0.25 or max_ar > 4.0:
                    result.add_warning(
                        f"Extreme aspect ratios detected ({min_ar:.2f} to {max_ar:.2f}). "
                        f"Very tall or wide images may affect detection quality."
                    )

    def _validate_annotations(self, result: ValidationResult) -> None:
        """Validate annotation files."""
        # Check if annotations directory exists
        if not self.labels_dir.exists():
            result.add_warning(
                f"No annotations directory found at {self.labels_dir}. "
                f"Run 'croak annotate' to label your images."
            )
            result.statistics['annotation_coverage'] = 0
            return

        images = result.statistics.get('images', {}).get('images', [])
        if not images:
            return

        # Check annotation coverage
        image_stems = {Path(p).stem for p in images}
        label_files = list(self.labels_dir.glob('*.txt'))
        label_stems = {p.stem for p in label_files}

        matched = image_stems & label_stems
        missing = image_stems - label_stems
        extra = label_stems - image_stems

        coverage = len(matched) / len(image_stems) if image_stems else 0
        result.statistics['annotation_coverage'] = coverage
        result.statistics['images_with_labels'] = len(matched)
        result.statistics['images_without_labels'] = len(missing)

        if len(missing) == len(image_stems):
            result.add_warning(
                f"No annotations found for any images. Run 'croak annotate' first."
            )
        elif coverage < self.MIN_ANNOTATION_COVERAGE:
            result.add_warning(
                f"{len(missing)} images without annotations ({coverage * 100:.0f}% coverage). "
                f"Recommend {self.MIN_ANNOTATION_COVERAGE * 100:.0f}%+ coverage."
            )

        if extra:
            result.add_warning(
                f"{len(extra)} annotation files without matching images. "
                f"These will be ignored."
            )

        # Validate annotation format (sample)
        sample_labels = label_files[:min(100, len(label_files))]
        self._validate_yolo_format(result, sample_labels)

    def _validate_yolo_format(self, result: ValidationResult, label_files: List[Path]) -> None:
        """Validate YOLO annotation format."""
        invalid_files = []
        empty_files = 0
        total_annotations = 0

        for label_file in label_files:
            try:
                with open(label_file) as f:
                    lines = f.readlines()

                if not lines:
                    empty_files += 1
                    continue

                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split()
                    if len(parts) != 5:
                        invalid_files.append((
                            label_file.name, line_num,
                            f"Expected 5 values, got {len(parts)}"
                        ))
                        continue

                    try:
                        class_id = int(parts[0])
                        x, y, w, h = map(float, parts[1:])
                        total_annotations += 1

                        # Validate ranges
                        if not (0 <= x <= 1 and 0 <= y <= 1):
                            invalid_files.append((
                                label_file.name, line_num,
                                f"Center ({x:.3f}, {y:.3f}) out of [0,1] range"
                            ))

                        if not (0 < w <= 1 and 0 < h <= 1):
                            invalid_files.append((
                                label_file.name, line_num,
                                f"Size ({w:.3f}, {h:.3f}) out of (0,1] range"
                            ))

                        if class_id < 0:
                            invalid_files.append((
                                label_file.name, line_num,
                                f"Negative class ID: {class_id}"
                            ))

                    except ValueError as e:
                        invalid_files.append((
                            label_file.name, line_num,
                            f"Parse error: {e}"
                        ))

            except Exception as e:
                invalid_files.append((label_file.name, 0, f"File error: {e}"))

        result.statistics['total_annotations'] = total_annotations
        result.statistics['empty_label_files'] = empty_files

        if invalid_files:
            result.add_error(
                f"{len(invalid_files)} annotation format errors found. "
                f"First few: {invalid_files[:3]}"
            )

        if empty_files > len(label_files) * 0.5:
            result.add_warning(
                f"{empty_files} empty label files ({empty_files / len(label_files) * 100:.0f}%). "
                f"These images have no objects - verify this is intentional."
            )

    def _validate_class_distribution(self, result: ValidationResult) -> None:
        """Validate class balance."""
        if not self.labels_dir.exists():
            return

        class_counts: Dict[int, int] = {}
        for label_file in self.labels_dir.glob('*.txt'):
            try:
                with open(label_file) as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 1:
                            try:
                                class_id = int(parts[0])
                                class_counts[class_id] = class_counts.get(class_id, 0) + 1
                            except ValueError:
                                continue
            except Exception:
                continue

        if not class_counts:
            return

        result.statistics['class_distribution'] = class_counts
        result.statistics['num_classes'] = len(class_counts)

        # Check minimums
        min_count = min(class_counts.values())
        max_count = max(class_counts.values())
        total_count = sum(class_counts.values())

        result.statistics['min_class_count'] = min_count
        result.statistics['max_class_count'] = max_count

        for class_id, count in class_counts.items():
            if count < self.MIN_INSTANCES_PER_CLASS:
                result.add_warning(
                    f"Class {class_id} has only {count} instances. "
                    f"Recommend {self.MIN_INSTANCES_PER_CLASS}+ per class."
                )

        # Check imbalance
        if min_count > 0:
            ratio = max_count / min_count
            result.statistics['imbalance_ratio'] = ratio

            if ratio > self.MAX_IMBALANCE_RATIO:
                result.add_warning(
                    f"Class imbalance ratio is {ratio:.1f}:1. "
                    f"Consider collecting more minority class samples or using class weights."
                )

    def _check_duplicates(self, result: ValidationResult) -> None:
        """Check for duplicate images."""
        images = result.statistics.get('images', {}).get('images', [])
        if not images or len(images) < 2:
            return

        from croak.data.scanner import find_duplicates

        # Only check if reasonable number of images
        if len(images) > 10000:
            result.add_warning(
                f"Skipping duplicate check for {len(images)} images (too many)."
            )
            return

        duplicates = find_duplicates(images)
        result.statistics['duplicates'] = len(duplicates)

        if duplicates:
            result.add_warning(
                f"{len(duplicates)} duplicate images found. "
                f"Remove before training to avoid data leakage."
            )

    def get_summary(self, result: ValidationResult) -> str:
        """Get human-readable summary of validation result.

        Args:
            result: ValidationResult to summarize.

        Returns:
            Formatted summary string.
        """
        stats = result.statistics
        lines = []

        # Header
        if result.passed:
            lines.append("Validation PASSED")
        else:
            lines.append("Validation FAILED")

        lines.append("")

        # Image stats
        img_stats = stats.get('images', {})
        if img_stats:
            lines.append(f"Images: {img_stats.get('total_images', 0)}")
            if img_stats.get('formats'):
                formats = ", ".join(f"{k}: {v}" for k, v in img_stats['formats'].items())
                lines.append(f"  Formats: {formats}")

        # Annotation stats
        coverage = stats.get('annotation_coverage', 0)
        lines.append(f"Annotation Coverage: {coverage * 100:.0f}%")

        # Class stats
        num_classes = stats.get('num_classes', 0)
        if num_classes > 0:
            lines.append(f"Classes: {num_classes}")
            if stats.get('imbalance_ratio'):
                lines.append(f"  Imbalance Ratio: {stats['imbalance_ratio']:.1f}:1")

        # Duplicates
        dups = stats.get('duplicates', 0)
        if dups > 0:
            lines.append(f"Duplicates: {dups}")

        # Errors and warnings
        if result.errors:
            lines.append("")
            lines.append(f"Errors ({len(result.errors)}):")
            for e in result.errors:
                lines.append(f"  - {e}")

        if result.warnings:
            lines.append("")
            lines.append(f"Warnings ({len(result.warnings)}):")
            for w in result.warnings:
                lines.append(f"  - {w}")

        return "\n".join(lines)
