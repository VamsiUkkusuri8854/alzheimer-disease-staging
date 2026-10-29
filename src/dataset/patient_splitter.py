# ============================================================
# ALZHEIMER MRI STAGING
# PATIENT-WISE 5-FOLD STRATIFIED SPLITTER
# ============================================================

import sys
from pathlib import Path
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split

# Robust project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_METADATA_FILE = PROJECT_ROOT / "data" / "metadata" / "oasis_metadata.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "metadata" / "folds"

N_SPLITS = 5
RANDOM_STATE = 42


def generate_patient_folds(
    metadata_file=DEFAULT_METADATA_FILE,
    output_dir=DEFAULT_OUTPUT_DIR,
    n_splits=N_SPLITS,
    random_state=RANDOM_STATE,
    val_size=0.2
):
    """
    Generate 5-fold patient-wise cross validation splits.
    
    The outer fold determines held-out TEST patients using StratifiedKFold.
    The remaining training patients are divided into TRAIN and VALIDATION
    using patient-level stratified train_test_split.
    
    Each output CSV contains exactly:
        patient_id,label,split,fold
    """
    metadata_path = Path(metadata_file)
    output_path = Path(output_dir)

    print("=" * 60)
    print("PATIENT-WISE 5-FOLD SPLITTING")
    print("=" * 60)

    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    df = pd.read_csv(metadata_path)

    # Normalize label column
    if "label" in df.columns:
        df["label"] = df["label"].astype(int)
    elif "class_id" in df.columns:
        df["label"] = df["class_id"].astype(int)
    elif "cdr" in df.columns:
        cdr_to_label = {0.0: 0, 0.5: 1, 1.0: 2, 2.0: 3}
        df["label"] = df["cdr"].map(cdr_to_label).astype(int)
    else:
        raise ValueError(
            f"No recognizable label column in {metadata_path}. "
            f"Available columns: {list(df.columns)}"
        )

    # Ensure unique patient rows
    df = df.drop_duplicates(subset=["patient_id"]).reset_index(drop=True)

    print(f"Total unique patients: {len(df)}")
    print("\nTarget 4-Class Patient Distribution:")
    class_names = [
        "Cognitively Normal",
        "Very Mild Dementia",
        "Mild Dementia",
        "Moderate Dementia"
    ]
    for c_id, c_name in enumerate(class_names):
        c_count = int((df["label"] == c_id).sum())
        print(f"  Class {c_id} ({c_name}): {c_count} patients")

    class_3_count = int((df["label"] == 3).sum())
    if class_3_count == 0:
        print("\n" + "=" * 70)
        print("NOTICE: Moderate Dementia samples (Class 3, CDR=2.0) are currently unavailable in dataset (0 patients found).")
        print("Additional real CDR=2.0 patients are required before 4-class stratified cross-validation.")
        print("4-class stratified cross-validation cannot be executed without class 3 samples.")
        print("Existing 3-class patient-wise fold files remain intact.")
        print("=" * 70)
        return []
    elif class_3_count < n_splits:
        print("\n" + "=" * 70)
        print(f"NOTICE: Found {class_3_count} Class 3 patients, but at least {n_splits} are required for stratified {n_splits}-fold CV.")
        print("Additional real CDR=2.0 patients are required before 4-class stratified cross-validation.")
        print("=" * 70)
        return []

    output_path.mkdir(parents=True, exist_ok=True)

    # Outer StratifiedKFold determines held-out TEST patients
    skf = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=random_state
    )

    all_folds = []

    for fold, (train_val_idx, test_idx) in enumerate(
        skf.split(df["patient_id"], df["label"]),
        start=1
    ):
        train_val_df = df.iloc[train_val_idx].copy()
        test_df = df.iloc[test_idx].copy()

        # Inner stratified split for TRAIN and VALIDATION
        train_df, val_df = train_test_split(
            train_val_df,
            test_size=val_size,
            shuffle=True,
            random_state=random_state,
            stratify=train_val_df["label"]
        )

        train_df = train_df.copy()
        val_df = val_df.copy()
        test_df = test_df.copy()

        train_df["split"] = "train"
        train_df["fold"] = fold

        val_df["split"] = "validation"
        val_df["fold"] = fold

        test_df["split"] = "test"
        test_df["fold"] = fold

        # Guarantee exact required columns: patient_id,label,split,fold
        columns_to_save = ["patient_id", "label", "split", "fold"]
        fold_df = pd.concat([train_df, val_df, test_df], ignore_index=True)[columns_to_save]

        fold_file = output_path / f"fold_{fold}.csv"
        fold_df.to_csv(fold_file, index=False)
        all_folds.append(fold_df)

        print(f"\nFold {fold}")
        print(f"  Train patients:      {len(train_df)} -> classes: {dict(train_df['label'].value_counts().sort_index())}")
        print(f"  Validation patients: {len(val_df)} -> classes: {dict(val_df['label'].value_counts().sort_index())}")
        print(f"  Test patients:       {len(test_df)} -> classes: {dict(test_df['label'].value_counts().sort_index())}")

    # ========================================================
    # COMBINE ALL FOLDS
    # ========================================================
    combined = pd.concat(all_folds, ignore_index=True)
    combined_file = output_path / "all_folds.csv"
    combined.to_csv(combined_file, index=False)
    print(f"\nAll folds saved to: {combined_file}")

    # ========================================================
    # LEAKAGE CHECK
    # ========================================================
    print("\n" + "=" * 60)
    print("LEAKAGE CHECK")
    print("=" * 60)

    total_tv_overlap = 0
    total_tt_overlap = 0
    total_vt_overlap = 0

    for fold in range(1, n_splits + 1):
        fold_data = combined[combined["fold"] == fold]
        train_pts = set(fold_data[fold_data["split"] == "train"]["patient_id"])
        val_pts = set(fold_data[fold_data["split"] == "validation"]["patient_id"])
        test_pts = set(fold_data[fold_data["split"] == "test"]["patient_id"])

        tv_overlap = train_pts.intersection(val_pts)
        tt_overlap = train_pts.intersection(test_pts)
        vt_overlap = val_pts.intersection(test_pts)

        total_tv_overlap += len(tv_overlap)
        total_tt_overlap += len(tt_overlap)
        total_vt_overlap += len(vt_overlap)

        if tv_overlap:
            print(f"Fold {fold} Train/Val overlap: {tv_overlap}")
        if tt_overlap:
            print(f"Fold {fold} Train/Test overlap: {tt_overlap}")
        if vt_overlap:
            print(f"Fold {fold} Val/Test overlap: {vt_overlap}")

    print(f"- train/validation overlap: {total_tv_overlap}")
    print(f"- train/test overlap: {total_tt_overlap}")
    print(f"- validation/test overlap: {total_vt_overlap}")

    if total_tv_overlap == 0 and total_tt_overlap == 0 and total_vt_overlap == 0:
        print("No patient leakage detected.")
    else:
        raise RuntimeError("Patient leakage detected across splits!")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)
    print(f"Fold files saved to: {output_path}")

    return all_folds


if __name__ == "__main__":
    generate_patient_folds()