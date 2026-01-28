"""Data directory scanning utilities."""

from pathlib import Path
from typing import Optional
from collections import defaultdict

from PIL import Image


SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def scan_directory(directory: Path) -> dict:
    """Scan a directory for images and annotations.

    Args:
        directory: Path to scan for images.

    Returns:
        Dict with scan results including counts and formats.
    """
    results = {
        "total_images": 0,
        "formats": defaultdict(int),
        "sizes": [],
        "has_annotations": False,
        "annotation_format": None,
        "images": [],
        "corrupt": [],
    }

    # Scan for images
    for path in directory.rglob("*"):
        if path.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
            # Try to open and verify
            try:
                with Image.open(path) as img:
                    img.verify()
                # Re-open to get size (verify closes the file)
                with Image.open(path) as img:
                    results["sizes"].append(img.size)
                    results["images"].append(str(path))
                    results["formats"][path.suffix.lower()] += 1
                    results["total_images"] += 1
            except Exception as e:
                results["corrupt"].append((str(path), str(e)))

    # Check for existing annotations
    results["has_annotations"], results["annotation_format"] = _detect_annotations(
        directory, results["images"]
    )

    # Compute size statistics
    if results["sizes"]:
        widths = [s[0] for s in results["sizes"]]
        heights = [s[1] for s in results["sizes"]]
        results["size_stats"] = {
            "min": (min(widths), min(heights)),
            "max": (max(widths), max(heights)),
            "median": (
                sorted(widths)[len(widths) // 2],
                sorted(heights)[len(heights) // 2],
            ),
        }

    return dict(results)


def _detect_annotations(directory: Path, images: list[str]) -> tuple[bool, Optional[str]]:
    """Detect if annotations exist and their format.

    Args:
        directory: Directory to check.
        images: List of image paths found.

    Returns:
        Tuple of (has_annotations, format_name).
    """
    # Check for YOLO format (.txt files alongside images)
    yolo_count = 0
    for img_path in images:
        txt_path = Path(img_path).with_suffix(".txt")
        if txt_path.exists():
            yolo_count += 1

    if yolo_count > len(images) * 0.5:  # More than 50% have labels
        return True, "yolo"

    # Check for COCO format (annotations.json or instances_*.json)
    coco_patterns = ["annotations.json", "instances_*.json", "*_annotations.json"]
    for pattern in coco_patterns:
        if list(directory.rglob(pattern)):
            return True, "coco"

    # Check for Pascal VOC format (.xml files)
    xml_count = len(list(directory.rglob("*.xml")))
    if xml_count > len(images) * 0.5:
        return True, "voc"

    return False, None


def validate_images(image_paths: list[str]) -> dict:
    """Validate that all images can be opened.

    Args:
        image_paths: List of image paths to validate.

    Returns:
        Dict with valid and corrupt image lists.
    """
    results = {"valid": [], "corrupt": []}

    for path in image_paths:
        try:
            with Image.open(path) as img:
                img.verify()
            with Image.open(path) as img:
                img.load()  # Actually load pixels
            results["valid"].append(path)
        except Exception as e:
            results["corrupt"].append((path, str(e)))

    return results


def find_duplicates(image_paths: list[str]) -> list[tuple[str, str]]:
    """Find duplicate images by content hash.

    Args:
        image_paths: List of image paths to check.

    Returns:
        List of tuples (duplicate_path, original_path).
    """
    import hashlib

    hashes = {}
    duplicates = []

    for path in image_paths:
        try:
            with open(path, "rb") as f:
                content_hash = hashlib.md5(f.read()).hexdigest()

            if content_hash in hashes:
                duplicates.append((path, hashes[content_hash]))
            else:
                hashes[content_hash] = path
        except Exception:
            continue

    return duplicates
