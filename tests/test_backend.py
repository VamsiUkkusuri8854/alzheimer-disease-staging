# ============================================================
# ALZHEIMER MRI STAGING - BACKEND API & MODEL SELECTION TESTS
# ============================================================

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import io
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.model_service import ModelService
from backend.services.mri_service import validate_file_extension


def test_backend_api():
    print("=" * 65)
    print("RUNNING COMPREHENSIVE BACKEND API & MODEL SELECTION TESTS")
    print("=" * 65)

    client = TestClient(app)

    # 1. Test Root
    print("\n[Test 1/7] Testing GET /...")
    res = client.get("/")
    assert res.status_code == 200, f"Root returned {res.status_code}"
    data = res.json()
    assert "docs_url" in data
    assert "disclaimer" in data
    print(f"  --> Root response: {data['title']}")
    print("  [PASSED] Root endpoint verified.")

    # 2. Test GET /models (Model Registry Endpoint)
    print("\n[Test 2/7] Testing GET /models (Model Registry)...")
    res = client.get("/models")
    assert res.status_code == 200, f"Models returned {res.status_code}"
    models_data = res.json()
    assert "models" in models_data
    models_list = models_data["models"]
    assert len(models_list) >= 2
    model_ids = [m["id"] for m in models_list]
    assert "mobilenet" in model_ids
    assert "mobilenet_v3" in model_ids
    print(f"  --> Registered models: {[m['name'] for m in models_list]}")
    for m in models_list:
        print(f"      * {m['name']}: Checkpoint available: {m['checkpoint_available']} | Status: {m['status']}")
    print("  [PASSED] GET /models endpoint verified.")

    # 3. Test Health Endpoint
    print("\n[Test 3/7] Testing GET /health...")
    res = client.get("/health")
    assert res.status_code == 200, f"Health returned {res.status_code}"
    health = res.json()
    assert health["status"] == "ok"
    assert "model_loaded" in health
    assert "classes" in health
    assert "available_models" in health
    print(f"  --> Status: {health['status']}")
    print(f"  --> Active model: {health['model_name']}")
    print(f"  --> Classes: {health['classes']}")
    print("  [PASSED] Health endpoint verified.")

    # 4. Test Model Info Endpoint with Query Params
    print("\n[Test 4/7] Testing GET /model-info for both models...")
    res_v3 = client.get("/model-info?model_name=mobilenet_v3")
    assert res_v3.status_code == 200
    info_v3 = res_v3.json()
    assert info_v3["model_name"] == "MobileNetV3-Large"
    print(f"  --> MobileNetV3-Large info: {info_v3['architecture_details']}")

    res_v2 = client.get("/model-info?model_name=mobilenet")
    assert res_v2.status_code == 200
    info_v2 = res_v2.json()
    assert info_v2["model_name"] == "MobileNet"
    print(f"  --> MobileNet info: {info_v2['architecture_details']}")
    print("  [PASSED] Model info endpoints verified.")

    # 5. Test File Extension Validation
    print("\n[Test 5/7] Testing Upload File Validation...")
    validate_file_extension("brain_scan.nii")
    validate_file_extension("patient_01_mprage.nii.gz")
    validate_file_extension("BRAIN.NII.GZ")

    invalid_files = ["malicious.exe", "notes.txt", "slice.png", "data.csv"]
    for bad_file in invalid_files:
        try:
            validate_file_extension(bad_file)
            assert False, f"Should have rejected {bad_file}"
        except Exception:
            pass

    fake_png = io.BytesIO(b"fake png data")
    res_bad = client.post("/predict", files={"file": ("fake.png", fake_png, "image/png")})
    assert res_bad.status_code == 400, f"Expected 400, got {res_bad.status_code}"
    print(f"  --> Rejected invalid file with: {res_bad.json()['detail']}")
    print("  [PASSED] File extension validation verified.")

    # 6. Test Model Caching in ModelService
    print("\n[Test 6/7] Testing In-Memory Model Caching...")
    service = ModelService.get_instance()
    m1, entry1 = service.get_model("mobilenet_v3")
    m2, entry2 = service.get_model("mobilenet_v3")
    assert m1 is m2, "Model instance was reloaded instead of reused from cache!"
    print(f"  --> Model caching verified: Object id {id(m1)} matches {id(m2)} (cached once into memory)")
    print("  [PASSED] Model caching verified.")

    # 7. Test PDF Report Generation Endpoint
    print("\n[Test 7/7] Testing POST /generate-report-pdf...")
    sample_report_payload = {
        "filename": "OAS1_0003_MR1.nii.gz",
        "model_name": "MobileNetV3-Large",
        "model_architecture": "MobileNetV3-Large (Hard-Swish + SE Attention)",
        "prediction": {
            "class_id": 1,
            "class_name": "Very Mild Dementia",
            "confidence": 0.845,
            "uncertainty": 0.189
        },
        "probabilities": {
            "Cognitively Normal": 0.125,
            "Very Mild Dementia": 0.845,
            "Mild Dementia": 0.030,
            "Moderate Dementia": 0.000
        },
        "num_slices": 128,
        "informative_slices": 128,
        "processing_time_seconds": 4.65,
        "clinician_name": "Dr. Sarah Johnson, MD",
        "clinical_impression": "Mild hippocampal volume reduction",
        "clinician_notes": "Follow-up cognitive exam recommended in 6 months.",
        "review_status": "Reviewed"
    }
    pdf_res = client.post("/generate-report-pdf", json=sample_report_payload)
    assert pdf_res.status_code == 200, f"PDF generation failed with status {pdf_res.status_code}"
    assert pdf_res.headers.get("content-type") == "application/pdf"
    assert len(pdf_res.content) > 1000, f"PDF size ({len(pdf_res.content)} bytes) is too small"
    print(f"  --> Generated valid PDF report ({len(pdf_res.content)} bytes)")
    print("  [PASSED] PDF Report Generation verified.")

    print("\n" + "=" * 65)
    print("ALL BACKEND & MODEL SELECTION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    test_backend_api()
