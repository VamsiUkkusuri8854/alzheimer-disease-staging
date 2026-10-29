# ============================================================
# ALZHEIMER MRI STAGING - END-TO-END PREDICTION TEST
# ============================================================

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import io
import numpy as np
import nibabel as nib
from fastapi.testclient import TestClient
from backend.main import app


def test_predict_pipeline():
    print("=" * 65)
    print("TESTING POST /predict END-TO-END WITH NIFTI VOLUME")
    print("=" * 65)

    client = TestClient(app)

    # 1. Create a synthetic 3D MRI volume (simulating brain MRI)
    print("\nCreating synthetic 3D NIfTI MRI scan...")
    shape = (64, 64, 32)
    data = np.zeros(shape, dtype=np.float32)

    # Create an ellipsoidal intensity region simulating brain tissue
    x, y, z = np.ogrid[:shape[0], :shape[1], :shape[2]]
    center = (shape[0] // 2, shape[1] // 2, shape[2] // 2)
    dist_sq = (
        ((x - center[0]) / 20.0) ** 2
        + ((y - center[1]) / 20.0) ** 2
        + ((z - center[2]) / 12.0) ** 2
    )
    brain_mask = dist_sq <= 1.0
    data[brain_mask] = np.random.uniform(50.0, 200.0, size=np.count_nonzero(brain_mask))

    # Wrap in NIfTI image
    affine = np.eye(4)
    nii_img = nib.Nifti1Image(data, affine)

    # Save to temporary file
    temp_nii_path = PROJECT_ROOT / "backend" / "uploads" / "temp_test_scan.nii"
    temp_nii_path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nii_img, str(temp_nii_path))
    with open(temp_nii_path, "rb") as f:
        file_bytes = f.read()
    temp_nii_path.unlink(missing_ok=True)

    print(f"  --> Synthetic scan size: {len(file_bytes)} bytes, Shape: {shape}")

    # 2. Call POST /predict
    print("\nSending POST /predict request...")
    files = {"file": ("test_patient_mprage.nii", io.BytesIO(file_bytes), "application/octet-stream")}
    response = client.post("/predict", files=files)

    print(f"  --> Status Code: {response.status_code}")
    assert response.status_code == 200, f"Predict failed: {response.text}"

    result = response.json()
    print("\nPrediction Result:")
    print(f"  --> Success:          {result['success']}")
    print(f"  --> Predicted Stage:  {result['prediction']['class_name']} (Class {result['prediction']['class_id']})")
    print(f"  --> Confidence:       {result['prediction']['confidence'] * 100:.1f}%")
    print(f"  --> Uncertainty:      {result['prediction']['uncertainty']}")
    print(f"  --> Probabilities:    {result['probabilities']}")
    print(f"  --> Slices Analyzed:  {result['num_slices']}")
    print(f"  --> Model:            {result['model']}")
    print(f"  --> Thumbnails count: {len(result.get('slice_thumbnails', []))}")

    assert result["success"] is True
    assert "class_id" in result["prediction"]
    assert "confidence" in result["prediction"]
    assert "uncertainty" in result["prediction"]
    assert result["num_slices"] > 0
    assert len(result["probabilities"]) in (3, 4)

    print("\n" + "=" * 65)
    print("END-TO-END PREDICTION PIPELINE VERIFIED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    test_predict_pipeline()
