from pathlib import Path

import nibabel as nib
import numpy as np
from PIL import Image


# ------------------------------------------------------------
# Input MRI
# ------------------------------------------------------------

MRI_FILE = Path(
    r"C:\Users\ACER\Downloads\oasis_cross-sectional_disc1 (1)"
    r"\disc1\OAS1_0042_MR1\RAW\OAS1_0042_MR1_mpr-1_anon.hdr"
)

# Output directory
OUTPUT_DIR = Path(
    r"data\processed\OAS1_0042_MR1\slices"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ------------------------------------------------------------
# 1. Load MRI
# ------------------------------------------------------------

print("Loading MRI...")

img = nib.load(str(MRI_FILE))

volume = img.get_fdata().astype(np.float32)

print("Original shape:", volume.shape)
print("Original dtype:", volume.dtype)
print(
    "Original intensity range:",
    float(volume.min()),
    "to",
    float(volume.max())
)


# ------------------------------------------------------------
# 2. Remove singleton dimensions
# ------------------------------------------------------------

volume = np.squeeze(volume)

print("Shape after squeeze:", volume.shape)


if volume.ndim != 3:
    raise ValueError(
        f"Expected 3D MRI, got shape {volume.shape}"
    )


# ------------------------------------------------------------
# 3. Robust intensity normalization
# ------------------------------------------------------------

nonzero = volume[volume > 0]

if len(nonzero) == 0:
    raise ValueError("MRI contains no non-zero voxels.")

low = np.percentile(nonzero, 1)
high = np.percentile(nonzero, 99)

print("1st percentile:", float(low))
print("99th percentile:", float(high))

volume = np.clip(volume, low, high)

volume = (volume - low) / (high - low + 1e-8)

volume[volume < 0] = 0
volume[volume > 1] = 1


# ------------------------------------------------------------
# 4. Extract axial slices
# ------------------------------------------------------------

num_slices = volume.shape[2]

saved = 0

print("Total axial slices:", num_slices)

for z in range(num_slices):

    slice_img = volume[:, :, z]

    # Percentage of non-zero pixels
    nonzero_ratio = np.mean(slice_img > 0)

    # Skip slices containing very little brain information
    if nonzero_ratio < 0.10:
        continue

    # Convert 0-1 → 0-255
    slice_uint8 = (
        slice_img * 255
    ).astype(np.uint8)

    # PIL image
    pil_img = Image.fromarray(
        slice_uint8,
        mode="L"
    )

    # Resize
    pil_img = pil_img.resize(
        (224, 224),
        Image.Resampling.BILINEAR
    )

    # Convert grayscale → RGB
    pil_img = pil_img.convert("RGB")

    output_file = (
        OUTPUT_DIR /
        f"slice_{z:03d}.png"
    )

    pil_img.save(output_file)

    saved += 1


# ------------------------------------------------------------
# 5. Summary
# ------------------------------------------------------------

print("\n" + "=" * 50)
print("PREPROCESSING COMPLETE")
print("=" * 50)

print("Patient: OAS1_0042_MR1")
print("Original shape:", volume.shape)
print("Slices saved:", saved)
print("Output:", OUTPUT_DIR)