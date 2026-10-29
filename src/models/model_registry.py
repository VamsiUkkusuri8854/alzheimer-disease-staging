# ============================================================
# ALZHEIMER MRI STAGING - MODEL REGISTRY & FACTORY
# ============================================================

from typing import Dict, Any, Callable, Optional, List
from pathlib import Path
import torch
import torch.nn as nn

from src.models.mobilenet_v2 import get_mobilenet_v2_model
from src.models.mobilenet_v3 import get_mobilenet_v3_model

FINAL_4_CLASSES = [
    "Cognitively Normal",
    "Very Mild Dementia",
    "Mild Dementia",
    "Moderate Dementia"
]

# Model definitions and metadata
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "mobilenet": {
        "id": "mobilenet",
        "name": "MobileNetV2",
        "family": "MobileNetV2",
        "display_name": "MobileNetV2",
        "description": "Lightweight convolutional neural network designed for efficient image classification.",
        "architecture_details": "MobileNet-V2 inverted residual blocks with linear bottlenecks",
        "input_resolution": "224 × 224 × 3",
        "badges": ["Lightweight", "Fast", "Efficient"],
        "builder": get_mobilenet_v2_model,
        "primary_checkpoint": "mobilenetv2_best.pth",
        "fallback_checkpoints": ["mobilenet_v2_best.pth", "mobilenet_best.pth"],
        "classifier_key": "classifier.1.weight",
        "accuracy_display": "Evaluation pending",
    },
    "mobilenet_v3": {
        "id": "mobilenet_v3",
        "name": "MobileNetV3-Large",
        "family": "MobileNetV3-Large",
        "display_name": "MobileNetV3-Large",
        "description": "Lightweight modern CNN architecture optimized for efficient feature extraction and image classification.",
        "architecture_details": "MobileNetV3-Large with Hard-Swish and Squeeze-and-Excitation attention",
        "input_resolution": "224 × 224 × 3",
        "badges": ["Lightweight", "Advanced", "Efficient"],
        "builder": get_mobilenet_v3_model,
        "primary_checkpoint": "mobilenetv3_falah_best.pth",
        "fallback_checkpoints": ["mobilenetv3_falah_weighted_best.pth", "fold_1_best_model.pth"],
        "classifier_key": "classifier.3.weight",
        "accuracy_display": "Evaluation pending",
    }
}

# Alias mapping for flexibility
MODEL_ALIASES: Dict[str, str] = {
    "mobilenet": "mobilenet",
    "mobilenet_v2": "mobilenet",
    "mobilenetv2": "mobilenet",
    "mobilenet_v3": "mobilenet_v3",
    "mobilenet_v3_large": "mobilenet_v3",
    "mobilenetv3": "mobilenet_v3",
    "mobilenetv3_large": "mobilenet_v3",
    "mobilenetv3-large": "mobilenet_v3"
}


def normalize_model_id(model_name: Optional[str]) -> str:
    """Normalize user/client requested model name to canonical registry key."""
    if not model_name:
        return "mobilenet_v3"
    clean = str(model_name).strip().lower().replace(" ", "_").replace("-", "_")
    return MODEL_ALIASES.get(clean, "mobilenet_v3")


def get_model_spec(model_name: Optional[str]) -> Dict[str, Any]:
    """Retrieve model specification metadata from registry."""
    key = normalize_model_id(model_name)
    return MODEL_REGISTRY[key]


def list_registered_models() -> List[Dict[str, Any]]:
    """Return all registered models in order."""
    return [MODEL_REGISTRY["mobilenet"], MODEL_REGISTRY["mobilenet_v3"]]
