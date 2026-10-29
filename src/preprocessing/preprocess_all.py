import argparse
from pathlib import Path
import nibabel as nib
import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm


# ============================================================
# SETTINGS & CONSTANTS
# ============================================================

DEFAULT_METADATA_FILE = Path("data/metadata/oasis_metadata.csv")
DEFAULT_RAW_DIR = Path("data/raw/oasis_cross-sectional_disc5")
OUTPUT_ROOT = Path("data/processed")
IMAGE_SIZE = (224, 224)
MIN_NONZERO_RATIO = 0.10


# ============================================================
# NORMALIZE MRI (ROBUST INTENSITY NORMALIZATION)
# ============================================================

def normalize_volume(volume: np.ndarray) -> np.ndarray:
    """
    Robust intensity normalization:
    Clips to 1st and 99th percentiles of non-zero voxels,
    then scales to [0, 1]. Background remains 0.
    """
    nonzero = volume[volume > 0]

    if len(nonzero) == 0:
        raise ValueError("MRI contains no non-zero voxels.")

    low = np.percentile(nonzero, 1)
    high = np.percentile(nonzero, 99)

    volume = np.clip(volume, low, high)

    volume = (volume - low) / (high - low + 1e-8)

    volume[volume < 0] = 0.0
    volume[volume > 1] = 1.0

    return volume


# ============================================================
# FIND RAW MPRAGE
# ============================================================

def find_mprage(patient_folder: Path) -> Path:
    """
    Search recursively for the mpr-1 MPRAGE Analyze header file (*_mpr-1_anon.hdr).
    """
    files = list(patient_folder.rglob("*_mpr-1_anon.hdr"))

    if not files:
        # Fallback to any .hdr or .nii if mpr-1 specific filename differs
        hdr_files = list(patient_folder.rglob("*.hdr"))
        if hdr_files:
            return hdr_files[0]
        nii_files = list(patient_folder.rglob("*.nii*"))
        if nii_files:
            return nii_files[0]
        raise FileNotFoundError(
            f"No mpr-1 MPRAGE (*_mpr-1_anon.hdr) found in {patient_folder}"
        )

    return files[0]


# ============================================================
# PROCESS ONE PATIENT
# ============================================================

def process_patient(patient_id: str, mri_folder: Path or str, output_root: Path = OUTPUT_ROOT, skip_existing: bool = True):
    """
    Process a single patient's structural MRI volume into 224x224 RGB axial slices.
    
    Returns:
        (saved_slices_count, status_str)
    """
    patient_folder = Path(mri_folder)
    output_dir = output_root / patient_id / "slices"

    # Skip if already processed and has slices
    if skip_existing and output_dir.exists():
        existing_slices = list(output_dir.glob("slice_*.png"))
        if len(existing_slices) > 0:
            return len(existing_slices), "skipped"

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Find MPRAGE volume
    mri_file = find_mprage(patient_folder)

    # 2. Load MRI Analyze/NIfTI volume
    img = nib.load(str(mri_file))
    volume = img.get_fdata().astype(np.float32)

    # 3. Remove singleton dimensions
    volume = np.squeeze(volume)

    if volume.ndim != 3:
        raise ValueError(
            f"{patient_id}: expected 3D MRI volume, got shape {volume.shape}"
        )

    # 4. Intensity Normalization
    volume = normalize_volume(volume)

    saved = 0

    # 5. Extract informative axial slices
    for z in range(volume.shape[2]):
        slice_img = volume[:, :, z]

        # Skip non-informative background slices (< 10% brain tissue)
        nonzero_ratio = np.mean(slice_img > 0)
        if nonzero_ratio < MIN_NONZERO_RATIO:
            continue

        # Convert to 8-bit grayscale
        slice_uint8 = (slice_img * 255.0).clip(0, 255).astype(np.uint8)

        pil_img = Image.fromarray(slice_uint8, mode="L")

        # Resize to 224x224 (Bilinear)
        pil_img = pil_img.resize(IMAGE_SIZE, Image.Resampling.BILINEAR)

        # Grayscale -> 3-channel RGB
        pil_img = pil_img.convert("RGB")

        output_file = output_dir / f"slice_{z:03d}.png"
        pil_img.save(output_file)
        saved += 1

    if saved == 0:
        raise ValueError(f"{patient_id}: 0 valid informative slices were extracted.")

    return saved, "processed"


# ============================================================
# BATCH PREPROCESSING ENTRYPOINT
# ============================================================

def process_disc(source_dir: Path, output_root: Path = OUTPUT_ROOT, skip_existing: bool = True):
    """
    Process all patient folders within a raw disc folder.
    """
    print("=" * 65)
    print(f"OASIS MRI PREPROCESSING: {source_dir.name}")
    print("=" * 65)
    print(f"Source Directory : {source_dir}")
    print(f"Output Directory : {output_root}")
    print(f"Skip Existing    : {skip_existing}")
    print("=" * 65)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

    # Discover patient folders (OAS1_*)
    patient_folders = sorted([
        p for p in source_dir.iterdir()
        if p.is_dir() and p.name.startswith("OAS1_")
    ])

    total_discovered = len(patient_folders)
    print(f"\nDiscovered {total_discovered} patient folders in {source_dir.name}\n")

    successful_count = 0
    skipped_count = 0
    failed_list = []
    patient_slices_counts = []

    for p_folder in tqdm(patient_folders, desc=f"Processing {source_dir.name}"):
        patient_id = p_folder.name
        try:
            saved_count, status = process_patient(
                patient_id=patient_id,
                mri_folder=p_folder,
                output_root=output_root,
                skip_existing=skip_existing
            )
            if status == "skipped":
                skipped_count += 1
                patient_slices_counts.append(saved_count)
            else:
                successful_count += 1
                patient_slices_counts.append(saved_count)

        except Exception as e:
            failed_list.append((patient_id, str(e)))

    total_slices = sum(patient_slices_counts)
    min_slices = min(patient_slices_counts) if patient_slices_counts else 0
    max_slices = max(patient_slices_counts) if patient_slices_counts else 0
    avg_slices = (total_slices / len(patient_slices_counts)) if patient_slices_counts else 0.0

    # ========================================================
    # REPORTING SUMMARY
    # ========================================================
    print("\n" + "=" * 65)
    print("OASIS DISC PREPROCESSING SUMMARY REPORT")
    print("=" * 65)
    print(f"1. Number of patients discovered : {total_discovered}")
    print(f"2. Number successfully processed  : {successful_count} (New) + {skipped_count} (Skipped Existing)")
    print(f"3. Number failed                 : {len(failed_list)}")
    print(f"4. Total slices generated        : {total_slices}")
    print(f"5. Minimum slices per patient    : {min_slices}")
    print(f"6. Maximum slices per patient    : {max_slices}")
    print(f"7. Average slices per patient    : {avg_slices:.2f}")

    if failed_list:
        print("\n8. List of Failed Patient IDs and Reasons:")
        for pid, err in failed_list:
            print(f"   - {pid}: {err}")
    else:
        print("\n8. Failed Patients               : None (0 failures)")

    print("=" * 65 + "\n")

    return {
        "discovered": total_discovered,
        "successful": successful_count,
        "skipped": skipped_count,
        "failed": len(failed_list),
        "failed_details": failed_list,
        "total_slices": total_slices,
        "min_slices": min_slices,
        "max_slices": max_slices,
        "avg_slices": avg_slices
    }


def main():
    parser = argparse.ArgumentParser(description="OASIS-1 MRI Batch Preprocessing Pipeline")
    parser.add_argument(
        "--source-dir",
        type=str,
        default=str(DEFAULT_RAW_DIR),
        help="Path to raw OASIS disc folder (e.g., data/raw/oasis_cross-sectional_disc5)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_ROOT),
        help="Output root directory for processed slices (default: data/processed)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing processed slices if already present"
    )

    args = parser.parse_args()
    source_path = Path(args.source_dir)
    output_path = Path(args.output_dir)
    skip_existing = not args.force

    process_disc(source_path, output_path, skip_existing=skip_existing)


if __name__ == "__main__":
    main()