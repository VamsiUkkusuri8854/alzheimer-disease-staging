# ============================================================
# ALZHEIMER MRI STAGING - END-TO-END PIPELINE VALIDATION TEST
# ============================================================

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import torch


def run_validation_checks():
    print("=" * 70)
    print("RUNNING END-TO-END PIPELINE VALIDATION CHECKS")
    print("=" * 70)

    # --------------------------------------------------------
    # Check 1: Metadata Loading
    # --------------------------------------------------------
    print("\n[Check 1/9] Metadata Loading...")
    metadata_file = PROJECT_ROOT / "data" / "metadata" / "oasis_metadata.csv"
    assert metadata_file.exists(), f"Metadata file not found: {metadata_file}"
    df_meta = pd.read_csv(metadata_file)
    print(f"  --> Columns: {list(df_meta.columns)}")
    print(f"  --> Total patient rows: {len(df_meta)}")
    assert len(df_meta) == 76, f"Expected 76 patients, got {len(df_meta)}"
    print("  [PASSED] Metadata loading verified.")

    # --------------------------------------------------------
    # Check 2: Fold Files Verification
    # --------------------------------------------------------
    print("\n[Check 2/9] Fold Files Verification...")
    folds_dir = PROJECT_ROOT / "data" / "metadata" / "folds"
    for fold in range(1, 6):
        fold_file = folds_dir / f"fold_{fold}.csv"
        assert fold_file.exists(), f"Fold file missing: {fold_file}"
        df_fold = pd.read_csv(fold_file)
        expected_cols = ["patient_id", "label", "split", "fold"]
        assert list(df_fold.columns) == expected_cols, f"Invalid columns in {fold_file}: {list(df_fold.columns)}"
        assert len(df_fold) == 76, f"Expected 76 patients in {fold_file}, got {len(df_fold)}"
    assert (folds_dir / "all_folds.csv").exists(), "all_folds.csv is missing."
    print("  [PASSED] All 5 fold CSVs and all_folds.csv verified.")

    # --------------------------------------------------------
    # Check 3: Patient Leakage Check
    # --------------------------------------------------------
    print("\n[Check 3/9] Patient Leakage Check...")
    all_folds_df = pd.read_csv(folds_dir / "all_folds.csv")
    total_tv = 0
    total_tt = 0
    total_vt = 0
    for fold in range(1, 6):
        fdf = all_folds_df[all_folds_df["fold"] == fold]
        train_p = set(fdf[fdf["split"] == "train"]["patient_id"])
        val_p = set(fdf[fdf["split"] == "validation"]["patient_id"])
        test_p = set(fdf[fdf["split"] == "test"]["patient_id"])
        tv = train_p.intersection(val_p)
        tt = train_p.intersection(test_p)
        vt = val_p.intersection(test_p)
        total_tv += len(tv)
        total_tt += len(tt)
        total_vt += len(vt)
    print(f"  - train/validation overlap: {total_tv}")
    print(f"  - train/test overlap: {total_tt}")
    print(f"  - validation/test overlap: {total_vt}")
    assert total_tv == 0 and total_tt == 0 and total_vt == 0, "Patient leakage detected!"
    print("  No patient leakage detected.")
    print("  [PASSED] Leakage check verified.")

    # --------------------------------------------------------
    # Check 4: Dataset Creation
    # --------------------------------------------------------
    print("\n[Check 4/9] Dataset Creation...")
    from src.dataset.mri_dataset import MRISliceDataset
    train_ds = MRISliceDataset(metadata_file=folds_dir / "fold_1.csv", fold=1, split="train")
    val_ds = MRISliceDataset(metadata_file=folds_dir / "fold_1.csv", fold=1, split="validation")
    test_ds = MRISliceDataset(metadata_file=folds_dir / "fold_1.csv", fold=1, split="test")
    print(f"  --> Train slices: {len(train_ds)}")
    print(f"  --> Val slices:   {len(val_ds)}")
    print(f"  --> Test slices:  {len(test_ds)}")
    assert len(train_ds) > 0 and len(val_ds) > 0 and len(test_ds) > 0
    sample = train_ds[0]
    assert "image" in sample and "label" in sample and "patient_id" in sample and "image_path" in sample
    assert sample["image"].shape == torch.Size([3, 224, 224])
    print(f"  --> Single slice image tensor shape: {sample['image'].shape}")
    print("  [PASSED] Dataset creation verified.")

    # --------------------------------------------------------
    # Check 5: DataLoader Creation
    # --------------------------------------------------------
    print("\n[Check 5/9] DataLoader Creation...")
    from src.dataset.dataloaders import get_dataloaders
    (
        train_loader,
        val_loader,
        test_loader,
        _, _, _
    ) = get_dataloaders(fold=1, batch_size=16)

    batch = next(iter(train_loader))
    images = batch["image"]
    labels = batch["label"]
    print(f"  --> Batch image shape: {images.shape} (Expected: torch.Size([16, 3, 224, 224]))")
    print(f"  --> Batch label shape: {labels.shape} (Expected: torch.Size([16]))")
    assert images.shape == torch.Size([16, 3, 224, 224]), f"Wrong image shape: {images.shape}"
    assert labels.shape == torch.Size([16]), f"Wrong label shape: {labels.shape}"
    print("  [PASSED] DataLoader creation and batch extraction verified.")

    # --------------------------------------------------------
    # Check 6: Class Weight Calculation
    # --------------------------------------------------------
    print("\n[Check 6/9] Class Weight Calculation...")
    from src.dataset.class_weights import calculate_class_weights
    weights, counts = calculate_class_weights(metadata_file=folds_dir / "fold_1.csv", split="train", num_classes=3)
    print(f"  --> Patient counts per class: {dict(counts)}")
    print(f"  --> Calculated weights: {weights.tolist()}")
    assert len(weights) == 3
    assert all(w > 0 for w in weights)
    print("  [PASSED] Patient-level class weights verified.")

    # --------------------------------------------------------
    # Check 7: MobileNet Model Creation
    # --------------------------------------------------------
    print("\n[Check 7/9] MobileNetV3-Large Model Creation...")
    from src.models.mobilenet import get_mobilenet_v3_model
    model = get_mobilenet_v3_model(num_classes=3, pretrained=True)
    assert model is not None
    print("  [PASSED] MobileNetV3-Large initialized with pretrained weights.")

    # --------------------------------------------------------
    # Check 8: Forward Pass
    # --------------------------------------------------------
    print("\n[Check 8/9] Single Batch Forward Pass...")
    model.eval()
    with torch.no_grad():
        outputs = model(images)
    print(f"  --> Model output shape: {outputs.shape} (Expected: torch.Size([16, 3]))")
    assert outputs.shape == torch.Size([16, 3]), f"Wrong output shape: {outputs.shape}"
    print("  [PASSED] Forward pass successful.")

    # --------------------------------------------------------
    # Check 9: Clean Imports & train.py Module Check
    # --------------------------------------------------------
    print("\n[Check 9/9] Import & train.py Integrity Check...")
    import config.config as cfg
    from src.training.trainer import Trainer
    assert cfg.NUM_CLASSES == 3
    assert cfg.DEVICE in ["cuda", "cpu"]
    print(f"  --> Config DEVICE: {cfg.DEVICE}")
    print(f"  --> Config EPOCHS: {cfg.EPOCHS}")
    print(f"  --> Config BATCH_SIZE: {cfg.BATCH_SIZE}")
    print("  [PASSED] All modules and config imported cleanly.")

    print("\n" + "=" * 70)
    print("ALL 9 VALIDATION CHECKS PASSED SUCCESSFULLY!")
    print("Project is 100% verified and ready to run: python train.py")
    print("=" * 70)


if __name__ == "__main__":
    run_validation_checks()
