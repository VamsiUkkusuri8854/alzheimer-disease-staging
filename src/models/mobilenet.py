# ============================================================
# ALZHEIMER MRI STAGING - MOBILENET BACKWARDS COMPATIBILITY
# ============================================================

from src.models.mobilenet_v3 import get_mobilenet_v3_model
from src.models.mobilenet_v2 import get_mobilenet_v2_model

__all__ = [
    "get_mobilenet_v3_model",
    "get_mobilenet_v2_model"
]