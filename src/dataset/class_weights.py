# ============================================================
# ALZHEIMER MRI STAGING
# CLASS WEIGHTS CALCULATION (PATIENT-WISE)
# ============================================================

import sys
from pathlib import Path
import pandas as pd
import torch

# Robust project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def calculate_class_weights(
    metadata_file,
    split="train",
    num_classes=4
):
    """
    Calculate inverse-frequency class weights from PATIENT COUNTS (not slice counts).
    
    Formula:
        weight[class] = total_patients / (num_classes * class_patient_count)
        
    Args:
        metadata_file (str or Path): Path to fold CSV file.
        split (str): Split name to compute weights for (default: 'train').
        num_classes (int): Number of target classes (default: 4).
        
    Returns:
        tuple: (weights_tensor, class_counts_series)
    """
    path = Path(metadata_file)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {path}")

    df = pd.read_csv(path)

    # Explicitly verify required columns
    required_columns = ["label", "split", "patient_id"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(
            f"Invalid fold CSV '{path}'. Missing required columns: {missing_columns}. "
            f"Existing columns: {list(df.columns)}. "
            f"Please ensure fold generation was run with patient_splitter.py."
        )

    # Filter for requested split
    split_df = df[df["split"] == split].copy()
    if len(split_df) == 0:
        raise ValueError(
            f"No patients found for split '{split}' in fold file: {path}. "
            f"Available splits: {list(df['split'].unique())}"
        )

    # Calculate patient counts (patient-level, not slice-level)
    unique_patients = split_df.drop_duplicates(subset=["patient_id"])
    class_counts = (
        unique_patients.groupby("label")
        .size()
        .reindex(range(num_classes), fill_value=0)
    )

    total_patients = int(class_counts.sum())
    if total_patients == 0:
        raise ValueError(f"Total patient count is 0 for split '{split}' in {path}.")

    weights = []
    for class_index in range(num_classes):
        count = int(class_counts[class_index])
        if count == 0:
            weight = 0.0
        else:
            weight = total_patients / (num_classes * count)
        weights.append(weight)

    weights_tensor = torch.tensor(weights, dtype=torch.float32)

    return weights_tensor, class_counts


if __name__ == "__main__":
    print("=" * 60)
    print("CLASS WEIGHTS TEST (4-CLASS READY, PATIENT-WISE)")
    print("=" * 60)

    metadata_path = PROJECT_ROOT / "data" / "metadata" / "folds" / "fold_1.csv"

    weights_4, counts_4 = calculate_class_weights(
        metadata_file=metadata_path,
        split="train",
        num_classes=4
    )

    print("\nTraining Patient Counts (4 Classes):")
    print("-" * 60)
    for class_idx, count in counts_4.items():
        print(f"  Class {class_idx}: {count} patients")

    print("\nClass Weights (4 Classes):")
    print("-" * 60)
    for class_idx, w in enumerate(weights_4.tolist()):
        print(f"  Class {class_idx}: {w:.4f}")

    print("\nClass weights test successful.")