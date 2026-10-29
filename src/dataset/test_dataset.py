import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dataset.mri_dataset import MRISliceDataset

METADATA_FILE = PROJECT_ROOT / "data" / "metadata" / "folds" / "fold_1.csv"

dataset = MRISliceDataset(
    metadata_file=METADATA_FILE,
    fold=1,
    split="train"
)

print("=" * 60)
print("DATASET TEST")
print("=" * 60)

print("Total slices:", len(dataset))

sample = dataset[0]

print("Image shape:", sample["image"].shape)
print("Label:", sample["label"].item())
print("Patient ID:", sample["patient_id"])
print("Image path:", sample["image_path"])

print("\nFirst 5 samples:")
for i in range(min(5, len(dataset))):
    sample = dataset[i]
    print(
        i,
        "| Patient:",
        sample["patient_id"],
        "| Label:",
        sample["label"].item()
    )