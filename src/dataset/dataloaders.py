# ============================================================
# ALZHEIMER MRI STAGING
# DATALOADERS CREATION
# ============================================================

import sys
from pathlib import Path
import torch
from torch.utils.data import DataLoader

# Robust project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dataset.mri_dataset import MRISliceDataset

BATCH_SIZE = 16
NUM_WORKERS = 0
PIN_MEMORY = False


def get_dataloaders(
    fold=1,
    batch_size=BATCH_SIZE,
    num_workers=NUM_WORKERS,
    pin_memory=PIN_MEMORY,
    metadata_file=None
):
    """
    Create train, validation, and test DataLoaders and Datasets
    for a particular patient-wise fold.
    
    Args:
        fold (int): Fold index (1 to 5).
        batch_size (int): Batch size (default: 16).
        num_workers (int): DataLoader num_workers (default: 0).
        pin_memory (bool): DataLoader pin_memory (default: False).
        metadata_file (str or Path, optional): Custom path to fold CSV.
        
    Returns:
        tuple: (train_loader, val_loader, test_loader, train_dataset, val_dataset, test_dataset)
    """
    if metadata_file is None:
        metadata_file = PROJECT_ROOT / "data" / "metadata" / "folds" / f"fold_{fold}.csv"
    else:
        metadata_file = Path(metadata_file)
        if not metadata_file.is_absolute():
            metadata_file = PROJECT_ROOT / metadata_file

    if not metadata_file.exists():
        raise FileNotFoundError(
            f"Fold metadata file not found at: {metadata_file}. "
            f"Please run patient_splitter.py first."
        )

    # --------------------------------------------------------
    # Datasets
    # --------------------------------------------------------
    train_dataset = MRISliceDataset(
        metadata_file=metadata_file,
        fold=fold,
        split="train"
    )

    val_dataset = MRISliceDataset(
        metadata_file=metadata_file,
        fold=fold,
        split="validation"
    )

    test_dataset = MRISliceDataset(
        metadata_file=metadata_file,
        fold=fold,
        split="test"
    )

    # --------------------------------------------------------
    # DataLoaders
    # --------------------------------------------------------
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory
    )

    return (
        train_loader,
        val_loader,
        test_loader,
        train_dataset,
        val_dataset,
        test_dataset
    )


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING DATALOADERS")
    print("=" * 60)

    (
        train_loader,
        val_loader,
        test_loader,
        train_dataset,
        val_dataset,
        test_dataset
    ) = get_dataloaders(fold=1, batch_size=16)

    print("\nDataset Sizes:")
    print("-" * 60)
    print(f"Training slices:   {len(train_dataset)}")
    print(f"Validation slices: {len(val_dataset)}")
    print(f"Test slices:       {len(test_dataset)}")

    print("\nDataLoader Batches:")
    print("-" * 60)
    print(f"Training batches:   {len(train_loader)}")
    print(f"Validation batches: {len(val_loader)}")
    print(f"Test batches:       {len(test_loader)}")

    # Test training batch
    train_batch = next(iter(train_loader))
    images = train_batch["image"]
    labels = train_batch["label"]

    print("\nBatch Verification:")
    print("-" * 60)
    print(f"Images shape: {images.shape}")
    print(f"Labels shape: {labels.shape}")
    print(f"Expected:     torch.Size([16, 3, 224, 224]) and torch.Size([16])")

    assert images.shape == torch.Size([16, 3, 224, 224]), f"Unexpected image shape: {images.shape}"
    assert labels.shape == torch.Size([16]), f"Unexpected label shape: {labels.shape}"

    print("\nDataloader test completed successfully.")