"""Dataset splitting for CROAK."""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
import random
import shutil
from collections import defaultdict
import yaml
import hashlib


class DatasetSplitter:
    """Split dataset into train/val/test sets.

    Features:
    - Stratified splitting by class
    - Reproducible with seed
    - Creates YOLO-compatible directory structure
    - Generates data.yaml for training
    """

    def __init__(self, data_dir: Path):
        """Initialize dataset splitter.

        Args:
            data_dir: Path to data directory.
        """
        self.data_dir = Path(data_dir)
        self.images_dir = self.data_dir / "raw"
        self.labels_dir = self.data_dir / "annotations"
        self.output_dir = self.data_dir / "processed"

    def split(
        self,
        train_ratio: float = 0.8,
        val_ratio: float = 0.15,
        test_ratio: float = 0.05,
        seed: int = 42,
        stratify: bool = True,
        class_names: Optional[List[str]] = None,
    ) -> Dict:
        """Split dataset into train/val/test sets.

        Args:
            train_ratio: Fraction for training (0-1).
            val_ratio: Fraction for validation (0-1).
            test_ratio: Fraction for testing (0-1).
            seed: Random seed for reproducibility.
            stratify: Whether to maintain class proportions in splits.
            class_names: Optional list of class names.

        Returns:
            Dict with split statistics.
        """
        # Validate ratios
        total = train_ratio + val_ratio + test_ratio
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Ratios must sum to 1.0, got {total}")

        random.seed(seed)

        # Find all image-label pairs
        pairs = self._find_pairs()
        if not pairs:
            raise ValueError("No image-label pairs found. Check data/raw and data/annotations.")

        # Get or infer class names
        if not class_names:
            class_names = self._infer_class_names(pairs)

        # Split data
        if stratify and len(pairs) > 10:
            splits = self._stratified_split(pairs, train_ratio, val_ratio, test_ratio)
        else:
            splits = self._random_split(pairs, train_ratio, val_ratio, test_ratio)

        # Create output directories and copy files
        self._setup_output_dirs()
        self._copy_splits(splits)

        # Create data.yaml
        data_yaml_path = self._create_data_yaml(class_names, splits)

        # Calculate dataset hash for reproducibility
        dataset_hash = self._compute_hash(pairs)

        return {
            'train': len(splits['train']),
            'val': len(splits['val']),
            'test': len(splits['test']),
            'total': len(pairs),
            'classes': class_names,
            'num_classes': len(class_names),
            'data_yaml': str(data_yaml_path),
            'output_dir': str(self.output_dir),
            'seed': seed,
            'stratified': stratify,
            'dataset_hash': dataset_hash,
        }

    def _find_pairs(self) -> List[Tuple[Path, Path]]:
        """Find image-label pairs.

        Returns:
            List of (image_path, label_path) tuples.
        """
        pairs = []
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}

        for img_path in self.images_dir.glob('*'):
            if img_path.suffix.lower() in image_extensions:
                label_path = self.labels_dir / f"{img_path.stem}.txt"
                if label_path.exists():
                    pairs.append((img_path, label_path))

        return pairs

    def _infer_class_names(self, pairs: List[Tuple[Path, Path]]) -> List[str]:
        """Infer class names from annotations or config.

        Args:
            pairs: Image-label pairs.

        Returns:
            List of class names.
        """
        # Try to read from config
        config_path = self.data_dir.parent / ".croak" / "config.yaml"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                if config and config.get('classes'):
                    return config['classes']
            except Exception:
                pass

        # Try to read from existing data.yaml
        data_yaml_path = self.output_dir / 'data.yaml'
        if data_yaml_path.exists():
            try:
                with open(data_yaml_path) as f:
                    data = yaml.safe_load(f)
                if data and data.get('names'):
                    if isinstance(data['names'], dict):
                        return list(data['names'].values())
                    return data['names']
            except Exception:
                pass

        # Otherwise, generate from class IDs
        class_ids = set()
        for _, label_path in pairs[:100]:  # Sample first 100
            try:
                with open(label_path) as f:
                    for line in f:
                        parts = line.strip().split()
                        if parts:
                            class_ids.add(int(parts[0]))
            except Exception:
                continue

        return [f"class_{i}" for i in sorted(class_ids)]

    def _stratified_split(
        self,
        pairs: List[Tuple[Path, Path]],
        train_ratio: float,
        val_ratio: float,
        test_ratio: float,
    ) -> Dict[str, List[Tuple[Path, Path]]]:
        """Split maintaining class proportions.

        Args:
            pairs: Image-label pairs.
            train_ratio: Training ratio.
            val_ratio: Validation ratio.
            test_ratio: Test ratio.

        Returns:
            Dict with 'train', 'val', 'test' lists.
        """
        # Group by primary (first) class
        by_class = defaultdict(list)
        for img, label in pairs:
            try:
                with open(label) as f:
                    first_line = f.readline().strip()
                    if first_line:
                        class_id = int(first_line.split()[0])
                        by_class[class_id].append((img, label))
                    else:
                        # Empty annotation - put in special group
                        by_class[-1].append((img, label))
            except Exception:
                by_class[-1].append((img, label))

        splits = {'train': [], 'val': [], 'test': []}

        for class_id, class_pairs in by_class.items():
            random.shuffle(class_pairs)
            n = len(class_pairs)

            train_end = int(n * train_ratio)
            val_end = train_end + int(n * val_ratio)

            splits['train'].extend(class_pairs[:train_end])
            splits['val'].extend(class_pairs[train_end:val_end])
            splits['test'].extend(class_pairs[val_end:])

        # Shuffle each split
        for split in splits.values():
            random.shuffle(split)

        return splits

    def _random_split(
        self,
        pairs: List[Tuple[Path, Path]],
        train_ratio: float,
        val_ratio: float,
        test_ratio: float,
    ) -> Dict[str, List[Tuple[Path, Path]]]:
        """Simple random split.

        Args:
            pairs: Image-label pairs.
            train_ratio: Training ratio.
            val_ratio: Validation ratio.
            test_ratio: Test ratio.

        Returns:
            Dict with 'train', 'val', 'test' lists.
        """
        pairs = pairs.copy()
        random.shuffle(pairs)
        n = len(pairs)

        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)

        return {
            'train': pairs[:train_end],
            'val': pairs[train_end:val_end],
            'test': pairs[val_end:],
        }

    def _setup_output_dirs(self) -> None:
        """Create output directory structure."""
        for split in ['train', 'val', 'test']:
            (self.output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
            (self.output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    def _copy_splits(self, splits: Dict[str, List[Tuple[Path, Path]]]) -> None:
        """Copy files to split directories.

        Args:
            splits: Dict of splits with file pairs.
        """
        for split_name, pairs in splits.items():
            img_dir = self.output_dir / "images" / split_name
            label_dir = self.output_dir / "labels" / split_name

            for img_path, label_path in pairs:
                shutil.copy2(img_path, img_dir / img_path.name)
                shutil.copy2(label_path, label_dir / f"{img_path.stem}.txt")

    def _create_data_yaml(
        self,
        class_names: List[str],
        splits: Dict[str, List]
    ) -> Path:
        """Create YOLO data.yaml file.

        Args:
            class_names: List of class names.
            splits: Split data for documentation.

        Returns:
            Path to created data.yaml.
        """
        data_yaml = {
            'path': str(self.output_dir.absolute()),
            'train': 'images/train',
            'val': 'images/val',
            'test': 'images/test',
            'names': {i: name for i, name in enumerate(class_names)},
            'nc': len(class_names),
        }

        yaml_path = self.output_dir / 'data.yaml'
        with open(yaml_path, 'w') as f:
            f.write("# CROAK Dataset Configuration\n")
            f.write(f"# Generated with seed for reproducibility\n")
            f.write(f"# Train: {len(splits['train'])}, Val: {len(splits['val'])}, Test: {len(splits['test'])}\n\n")
            yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False)

        return yaml_path

    def _compute_hash(self, pairs: List[Tuple[Path, Path]]) -> str:
        """Compute hash of dataset for reproducibility tracking.

        Args:
            pairs: Image-label pairs.

        Returns:
            Hash string.
        """
        # Hash based on sorted filenames
        filenames = sorted([p[0].name for p in pairs])
        content = "\n".join(filenames)
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def get_split_stats(self) -> Dict:
        """Get statistics about existing splits.

        Returns:
            Dict with split statistics.
        """
        stats = {}

        for split in ['train', 'val', 'test']:
            img_dir = self.output_dir / "images" / split
            if img_dir.exists():
                stats[split] = len(list(img_dir.glob('*')))
            else:
                stats[split] = 0

        stats['total'] = sum(stats.values())

        # Check for data.yaml
        data_yaml_path = self.output_dir / 'data.yaml'
        stats['data_yaml_exists'] = data_yaml_path.exists()

        if data_yaml_path.exists():
            try:
                with open(data_yaml_path) as f:
                    data = yaml.safe_load(f)
                stats['num_classes'] = data.get('nc', 0)
                names = data.get('names', {})
                if isinstance(names, dict):
                    stats['class_names'] = list(names.values())
                else:
                    stats['class_names'] = names
            except Exception:
                pass

        return stats

    def reset_splits(self) -> None:
        """Remove existing splits."""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
