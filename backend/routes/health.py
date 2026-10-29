# ============================================================
# ALZHEIMER MRI STAGING - HEALTH ROUTE
# ============================================================

from fastapi import APIRouter
from backend.services.model_service import ModelService

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint returning system status and model readiness.
    """
    model_service = ModelService.get_instance()
    info = model_service.get_info()

    return {
        "status": "ok",
        "service": "Alzheimer MRI Staging API",
        "model_loaded": info["is_loaded"],
        "model_name": info["display_name"],
        "model_id": info["model_id"],
        "device": info["device"],
        "num_classes": info["num_classes"],
        "classes": info["classes"],
        "target_classes": info.get("target_classes", 4),
        "target_class_names": info.get("target_class_names", [
            "Cognitively Normal",
            "Very Mild Dementia",
            "Mild Dementia",
            "Moderate Dementia"
        ]),
        "is_4class_ready": info.get("is_4class_ready", True),
        "is_4class_trained": info.get("is_4class_trained", False),
        "model_status_message": info.get("model_status_message", ""),
        "accuracy_display": info.get("accuracy_display", "Evaluation pending"),
        "checkpoint": info.get("checkpoint_path"),
        "available_models": info.get("available_models", [])
    }
