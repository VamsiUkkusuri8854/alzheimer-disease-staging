import numpy as np


def normalize_mri(volume):
    """
    Normalize MRI intensities using non-zero voxels.

    Background voxels remain zero.

    Returns:
        normalized_volume: float32 NumPy array
    """

    volume = volume.astype(np.float32)

    # Find brain/non-background voxels
    non_zero = volume[volume > 0]

    if non_zero.size == 0:
        raise ValueError("MRI contains no non-zero voxels.")

    # Robust intensity range
    lower = np.percentile(non_zero, 1)
    upper = np.percentile(non_zero, 99)

    # Clip extreme values
    clipped = np.clip(volume, lower, upper)

    # Normalize to approximately 0-1
    normalized = (clipped - lower) / (upper - lower + 1e-8)

    # Keep background at zero
    normalized[volume <= 0] = 0.0

    return normalized.astype(np.float32)


def print_normalization_info(volume, normalized_volume):

    print("=" * 60)
    print("MRI NORMALIZATION")
    print("=" * 60)

    print(
        f"Original range: "
        f"{volume.min():.4f} → {volume.max():.4f}"
    )

    print(
        f"Normalized range: "
        f"{normalized_volume.min():.4f} → "
        f"{normalized_volume.max():.4f}"
    )

    print(
        f"Normalized mean: "
        f"{normalized_volume[normalized_volume > 0].mean():.4f}"
    )

    print(
        f"Normalized std: "
        f"{normalized_volume[normalized_volume > 0].std():.4f}"
    )

    print("=" * 60)


if __name__ == "__main__":

    from nifti_loader import load_nifti

    MRI_PATH = (
        "data/raw/OAS1_0042_MR1/RAW/"
        "OAS1_0042_MR1_mpr-1_anon.hdr"
    )

    _, volume = load_nifti(MRI_PATH)

    normalized_volume = normalize_mri(volume)

    print_normalization_info(volume, normalized_volume)