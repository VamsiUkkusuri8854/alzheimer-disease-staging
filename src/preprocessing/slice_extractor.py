from pathlib import Path

import numpy as np
from PIL import Image

from nifti_loader import load_nifti
from normalization import normalize_mri


MRI_PATH = (
    "data/raw/OAS1_0042_MR1/RAW/"
    "OAS1_0042_MR1_mpr-1_anon.hdr"
)

OUTPUT_DIR = Path("data/processed/OAS1_0042_MR1/slices")


def extract_slices(volume, output_dir, image_size=224):
    """
    Extract informative axial slices from a normalized 3D MRI volume.
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    depth = volume.shape[2]

    saved_slices = []

    for z in range(depth):

        slice_2d = volume[:, :, z]

        # Skip slices containing almost no brain information.
        non_zero_ratio = np.count_nonzero(slice_2d) / slice_2d.size

        if non_zero_ratio < 0.10:
            continue

        # Convert normalized values to 8-bit image.
        slice_uint8 = (slice_2d * 255).clip(0, 255).astype(np.uint8)

        image = Image.fromarray(slice_uint8)

        # Resize to MobileNet input size.
        image = image.resize(
            (image_size, image_size),
            Image.Resampling.BILINEAR
        )

        # Convert grayscale → RGB.
        image = image.convert("RGB")

        output_path = output_dir / f"slice_{z:03d}.png"

        image.save(output_path)

        saved_slices.append(output_path)

    return saved_slices


if __name__ == "__main__":

    print("=" * 60)
    print("MRI SLICE EXTRACTION")
    print("=" * 60)

    _, volume = load_nifti(MRI_PATH)

    normalized_volume = normalize_mri(volume)

    slices = extract_slices(
        normalized_volume,
        OUTPUT_DIR
    )

    print(f"Original MRI shape: {volume.shape}")
    print(f"Slices saved: {len(slices)}")
    print(f"Output directory: {OUTPUT_DIR}")

    if slices:
        print(f"First slice: {slices[0]}")
        print(f"Last slice: {slices[-1]}")

    print("=" * 60)