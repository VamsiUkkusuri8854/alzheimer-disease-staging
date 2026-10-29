# ============================================================
# ALZHEIMER MRI STAGING
# MRI SLICE DATASET
# ============================================================

import sys
from pathlib import Path
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset
from torchvision import transforms

# Robust project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class MRISliceDataset(Dataset):
    """
    PyTorch Dataset for MRI 2D slices.
    
    Reads a fold CSV, selects the requested split ('train', 'validation', or 'test'),
    finds all 224x224 RGB slice PNGs for each patient, and returns ImageNet-normalized tensors.
    """

    def __init__(
        self,
        metadata_file,
        split,
        fold=None,
        processed_dir=None,
        transform=None
    ):
        """
        Args:
            metadata_file (str or Path): Path to fold CSV (e.g. fold_1.csv).
            split (str): 'train', 'validation', or 'test'.
            fold (int, optional): Fold number (if filtering by fold).
            processed_dir (str or Path, optional): Directory containing patient slice folders.
            transform (callable, optional): Custom transform. Defaults to ImageNet normalization.
        """
        metadata_path = Path(metadata_file)
        if not metadata_path.is_absolute():
            metadata_path = PROJECT_ROOT / metadata_path

        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        df = pd.read_csv(metadata_path)

        # Normalize label column
        if "label" in df.columns:
            label_col = "label"
        elif "class_id" in df.columns:
            label_col = "class_id"
        else:
            raise ValueError(
                f"Missing label/class_id column in {metadata_path}. "
                f"Columns present: {list(df.columns)}"
            )

        if "patient_id" not in df.columns:
            raise ValueError(f"Missing 'patient_id' column in {metadata_path}.")

        if "split" not in df.columns:
            raise ValueError(f"Missing 'split' column in {metadata_path}.")

        # Filter by fold if provided and column exists
        if fold is not None and "fold" in df.columns:
            df = df[df["fold"] == fold]

        # Select only requested split
        df = df[df["split"] == split].reset_index(drop=True)

        self.metadata = df
        self.split = split
        self.fold = fold

        # Determine processed data directory
        if processed_dir is None:
            self.processed_dir = PROJECT_ROOT / "data" / "processed"
        else:
            self.processed_dir = Path(processed_dir)
            if not self.processed_dir.is_absolute():
                self.processed_dir = PROJECT_ROOT / self.processed_dir

        # ----------------------------------------------------
        # Build slice-level samples
        # ----------------------------------------------------
        self.samples = []

        for row in self.metadata.itertuples():
            patient_id = row.patient_id
            label = int(getattr(row, label_col))

            slice_dir = self.processed_dir / patient_id / "slices"
            if not slice_dir.exists():
                continue

            slice_files = sorted(slice_dir.glob("*.png"))

            for slice_file in slice_files:
                self.samples.append({
                    "image_path": str(slice_file),
                    "patient_id": patient_id,
                    "label": label,
                })

        # ----------------------------------------------------
        # Image transformations
        # ----------------------------------------------------
        if transform is not None:
            self.transform = transform
        else:
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        sample = self.samples[index]

        image = Image.open(sample["image_path"]).convert("RGB")
        image_tensor = self.transform(image)

        label_tensor = torch.tensor(
            sample["label"],
            dtype=torch.long
        )

        return {
            "image": image_tensor,
            "label": label_tensor,
            "patient_id": sample["patient_id"],
            "image_path": sample["image_path"]
        }


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING MRI SLICE DATASET")
    print("=" * 60)

    dataset = MRISliceDataset(
        metadata_file="data/metadata/folds/fold_1.csv",
        split="train",
        fold=1
    )

    print(f"Total train slices loaded: {len(dataset)}")
    if len(dataset) > 0:
        first_sample = dataset[0]
        print(f"Image tensor shape: {first_sample['image'].shape}")
        print(f"Label tensor:       {first_sample['label']}")
        print(f"Patient ID:         {first_sample['patient_id']}")
        print(f"Image path:         {first_sample['image_path']}")
        print("MRI dataset test successful.")
    else:
        print("Warning: No slices found.")