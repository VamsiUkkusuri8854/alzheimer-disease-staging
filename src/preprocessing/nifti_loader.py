import nibabel as nib
import numpy as np
from pathlib import Path


def load_nifti(mri_path):
    """
    Load an MRI NIfTI or Analyze (.hdr/.img) volume.

    Returns:
        image: nibabel image object
        volume: 3D NumPy array
    """

    mri_path = Path(mri_path)

    if not mri_path.exists():
        raise FileNotFoundError(f"MRI file not found: {mri_path}")

    image = nib.load(str(mri_path))

    volume = image.get_fdata(dtype=np.float32)

    # Remove dimensions of size 1.
    volume = np.squeeze(volume)

    if volume.ndim != 3:
        raise ValueError(
            f"Expected a 3D MRI volume, but got shape {volume.shape}"
        )

    return image, volume


def print_mri_info(mri_path):
    """Print basic information about an MRI volume."""

    image, volume = load_nifti(mri_path)

    print("=" * 60)
    print("MRI INFORMATION")
    print("=" * 60)

    print(f"File: {mri_path}")
    print(f"Original shape: {image.shape}")
    print(f"Clean 3D shape: {volume.shape}")
    print(f"Data type: {volume.dtype}")
    print(f"Voxel size: {image.header.get_zooms()[:3]}")
    print(f"Minimum intensity: {volume.min():.4f}")
    print(f"Maximum intensity: {volume.max():.4f}")
    print(f"Mean intensity: {volume.mean():.4f}")
    print(f"Non-zero voxels: {np.count_nonzero(volume):,}")

    print("=" * 60)


if __name__ == "__main__":

    MRI_PATH = (
        "data/raw/OAS1_0042_MR1/RAW/"
        "OAS1_0042_MR1_mpr-1_anon.hdr"
    )

    print_mri_info(MRI_PATH)