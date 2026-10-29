import nibabel as nib
from pathlib import Path


MRI_PATH = Path(
    "data/raw/OAS1_0042_MR1/RAW/OAS1_0042_MR1_mpr-1_anon.hdr"
)


def check_mri(path: Path):
    print("=" * 50)
    print("OASIS MRI CHECK")
    print("=" * 50)

    if not path.exists():
        print(f"ERROR: MRI file not found:\n{path}")
        return

    try:
        image = nib.load(str(path))

        print(f"File: {path.name}")
        print(f"Shape: {image.shape}")
        print(f"Data type: {image.get_data_dtype()}")
        print(f"Voxel size: {image.header.get_zooms()}")
        print(f"Number of dimensions: {len(image.shape)}")

        print("\nMRI loaded successfully!")

    except Exception as e:
        print(f"ERROR loading MRI: {e}")


if __name__ == "__main__":
    check_mri(MRI_PATH)