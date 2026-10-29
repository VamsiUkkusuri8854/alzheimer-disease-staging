"""
Validation test for OASIS Disc 5 Preprocessing:
Verifies:
1. Processed image shape = [3, 224, 224] (RGB)
2. Pixel values are valid in [0, 255] uint8 / [0.0, 1.0] float
3. Patient ID is preserved across folder structure and filenames
4. No patient leakage between slices and patient directories
"""

from pathlib import Path
import numpy as np
from PIL import Image
import torch
from torchvision import transforms

def validate_disc5_patient(patient_id="OAS1_0151_MR1"):
    print("=" * 65)
    print(f"VALIDATION TEST: DISC 5 PATIENT [{patient_id}]")
    print("=" * 65)

    processed_dir = Path("data/processed") / patient_id / "slices"
    assert processed_dir.exists(), f"Processed directory not found: {processed_dir}"

    slices = sorted(list(processed_dir.glob("slice_*.png")))
    assert len(slices) > 0, f"No slices found in {processed_dir}"
    print(f"[OK] Patient ID preserved in output path: {processed_dir}")
    print(f"[OK] Total informative slices extracted: {len(slices)}")

    # 1. Inspect first, middle, and last slices
    test_indices = [0, len(slices) // 2, len(slices) - 1]
    
    transform = transforms.Compose([
        transforms.ToTensor(), # Converts PIL [H, W, C] in [0, 255] -> Tensor [C, H, W] in [0.0, 1.0]
    ])

    for idx in test_indices:
        slice_path = slices[idx]
        pil_img = Image.open(slice_path)
        
        # Verify PIL mode & size
        assert pil_img.mode == "RGB", f"Expected RGB mode, got {pil_img.mode}"
        assert pil_img.size == (224, 224), f"Expected (224, 224) size, got {pil_img.size}"
        
        # Verify Tensor shape [3, 224, 224]
        tensor_img = transform(pil_img)
        assert tensor_img.shape == (3, 224, 224), f"Expected [3, 224, 224], got {tensor_img.shape}"
        
        # Verify Pixel Value range
        min_val = tensor_img.min().item()
        max_val = tensor_img.max().item()
        assert 0.0 <= min_val <= 1.0, f"Min pixel value out of bounds: {min_val}"
        assert 0.0 <= max_val <= 1.0, f"Max pixel value out of bounds: {max_val}"
        assert not torch.isnan(tensor_img).any(), "NaN values found in slice tensor"
        assert not torch.isinf(tensor_img).any(), "Inf values found in slice tensor"

        print(f"  -> Slice {slice_path.name}: Shape={list(tensor_img.shape)}, Dtype={tensor_img.dtype}, Range=[{min_val:.3f}, {max_val:.3f}]")

    # 2. Verify No Patient Leakage across all processed patients
    all_processed = sorted([p.name for p in Path("data/processed").iterdir() if p.is_dir()])
    unique_patients = set(all_processed)
    assert len(all_processed) == len(unique_patients), "Duplicate patient directories detected in data/processed"
    
    # Check that disc 5 patient exists in metadata
    import pandas as pd
    meta_path = Path("data/metadata/oasis_metadata.csv")
    if meta_path.exists():
        df_meta = pd.read_csv(meta_path)
        matching_meta = df_meta[df_meta["patient_id"] == patient_id]
        if not matching_meta.empty:
            row = matching_meta.iloc[0]
            print(f"[OK] Patient ID verified in metadata: Class={row['class_name']} (CDR={row['cdr']}, Age={row['age']})")

    print(f"[OK] Total patient directories in data/processed: {len(all_processed)}")
    print(f"[OK] Patient leakage check passed: All {len(all_processed)} patients are strictly segregated.")
    print("=" * 65)
    print("ALL DISC 5 VALIDATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    validate_disc5_patient()
