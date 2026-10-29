# ============================================================
# ALZHEIMER MRI STAGING - DYNAMIC MODEL REGISTRY SERVICE
# ============================================================

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import torch
import torch.nn as nn

# Ensure project root is accessible
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.model_registry import (
    MODEL_REGISTRY,
    normalize_model_id,
    get_model_spec,
    list_registered_models,
    FINAL_4_CLASSES
)


class ModelService:
    """
    Model Registry and Lifecycle Service for Alzheimer's MRI Staging.
    Supports dynamic selection between MobileNet and MobileNetV3-Large.
    Implements in-memory model caching so models are loaded only once.
    Safely inspects checkpoints without fabricating weights or metrics.
    """
    _instance: Optional["ModelService"] = None

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.checkpoint_dir = PROJECT_ROOT / "checkpoints"
        self.default_model_id = "mobilenet_v3"
        
        # In-memory model cache: { model_id: { "model": nn.Module, "metadata": dict } }
        self._model_cache: Dict[str, Dict[str, Any]] = {}
        
        # Scan and initialize metadata for all registered models on startup
        self._scan_and_preload_models()

    @classmethod
    def get_instance(cls) -> "ModelService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        entry = self._model_cache.get(self.default_model_id, {})
        return entry.get("is_loaded", False)

    @property
    def num_classes(self) -> int:
        entry = self._model_cache.get(self.default_model_id, {})
        return entry.get("num_classes", 4)

    @property
    def classes(self) -> List[str]:
        entry = self._model_cache.get(self.default_model_id, {})
        return entry.get("classes", list(FINAL_4_CLASSES))

    @property
    def class_names(self) -> List[str]:
        return self.classes

    @property
    def error_message(self) -> Optional[str]:
        entry = self._model_cache.get(self.default_model_id, {})
        return entry.get("error_message")

    @property
    def model_status_message(self) -> str:
        entry = self._model_cache.get(self.default_model_id, {})
        return entry.get("status_message", "")

    @property
    def is_4class_trained(self) -> bool:
        entry = self._model_cache.get(self.default_model_id, {})
        return entry.get("is_4class_trained", False)

    @property
    def target_classes(self) -> int:
        return 4

    def _find_checkpoint(self, spec: Dict[str, Any]) -> Optional[Path]:
        """Find the best available checkpoint file for a model specification."""
        # 1. Environment variable override
        env_key = f"{spec['id'].upper()}_MODEL_PATH"
        if os.getenv(env_key):
            p = Path(os.getenv(env_key))
            if p.exists():
                return p
        
        # 2. Primary checkpoint
        p = self.checkpoint_dir / spec["primary_checkpoint"]
        if p.exists():
            return p
            
        # 3. Fallback checkpoints in priority order
        for fb in spec.get("fallback_checkpoints", []):
            p = self.checkpoint_dir / fb
            if p.exists():
                return p
                
        return None

    def _load_single_model(self, model_id: str) -> Dict[str, Any]:
        """Load and cache a specific model from checkpoint."""
        spec = MODEL_REGISTRY.get(model_id)
        if not spec:
            raise ValueError(f"Unknown model architecture requested: '{model_id}'")

        ckpt_path = self._find_checkpoint(spec)

        if ckpt_path is None or not ckpt_path.exists():
            return {
                "id": spec["id"],
                "name": spec["name"],
                "display_name": spec["display_name"],
                "description": spec["description"],
                "architecture_details": spec["architecture_details"],
                "input_resolution": spec["input_resolution"],
                "badges": spec["badges"],
                "is_loaded": False,
                "checkpoint_available": False,
                "checkpoint_path": None,
                "num_classes": 3,
                "classes": FINAL_4_CLASSES[:3],
                "target_classes": 4,
                "target_class_names": FINAL_4_CLASSES,
                "is_4class_trained": False,
                "is_4class_ready": True,
                "accuracy_display": spec.get("accuracy_display", "Evaluation pending"),
                "status": "CHECKPOINT NOT AVAILABLE",
                "status_message": f"Model '{spec['name']}' is selected, but a trained checkpoint is not available yet.",
                "error_message": f"Checkpoint not found for {spec['name']}. Train the model before running inference.",
                "model": None
            }

        try:
            print(f"[ModelService] Loading checkpoint for {spec['name']} from: {ckpt_path.name}")
            checkpoint = torch.load(ckpt_path, map_location=self.device)
            state_dict = checkpoint["model_state_dict"] if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint else checkpoint

            # Determine number of classes from state_dict weights
            detected_classes = 4  # Default to 4
            for key in ["classifier.3.weight", "classifier.1.weight", "classifier.2.weight", "classifier.weight"]:
                if key in state_dict:
                    detected_classes = state_dict[key].shape[0]
                    break

            is_4class_trained = (detected_classes == 4)
            active_classes = list(FINAL_4_CLASSES[:detected_classes])

            # Build model architecture
            builder_fn = spec["builder"]
            model = builder_fn(num_classes=detected_classes, pretrained=False)
            model.load_state_dict(state_dict)
            model.to(self.device)
            model.eval()

            epoch = checkpoint.get("epoch") if isinstance(checkpoint, dict) else None
            val_loss = checkpoint.get("val_loss") or checkpoint.get("loss") if isinstance(checkpoint, dict) else None
            val_acc = checkpoint.get("val_accuracy") or checkpoint.get("accuracy") if isinstance(checkpoint, dict) else None

            status_msg = (
                f"4-Class Alzheimer's Disease Staging model loaded and ready."
                if is_4class_trained
                else "Current trained checkpoint supports 3 classes (CN, Very Mild, Mild). Moderate Dementia is reserved for future CDR 2.0 data."
            )

            print(f"[ModelService] Successfully loaded {spec['name']} ({detected_classes} classes) on {self.device}")

            # Check for saved evaluation metrics from actual runs
            metrics_display = spec.get("accuracy_display", "Evaluation pending")
            metrics_filename = "mobilenetv2_metrics.json" if spec["id"] == "mobilenet" else "mobilenetv3_metrics.json"
            metrics_path = PROJECT_ROOT / "outputs" / "metrics" / metrics_filename
            if metrics_path.exists():
                try:
                    import json
                    with open(metrics_path, "r") as mf:
                        m_data = json.load(mf)
                        if "accuracy_percent" in m_data:
                            metrics_display = f"{m_data['accuracy_percent']}%"
                except Exception:
                    pass

            return {
                "id": spec["id"],
                "name": spec["name"],
                "display_name": spec["display_name"],
                "description": spec["description"],
                "architecture_details": spec["architecture_details"],
                "input_resolution": spec["input_resolution"],
                "badges": spec["badges"],
                "is_loaded": True,
                "checkpoint_available": True,
                "checkpoint_path": str(ckpt_path),
                "num_classes": detected_classes,
                "classes": active_classes,
                "target_classes": 4,
                "target_class_names": FINAL_4_CLASSES,
                "is_4class_trained": is_4class_trained,
                "is_4class_ready": True,
                "accuracy_display": metrics_display,
                "status": "READY",
                "status_message": status_msg,
                "epoch": epoch,
                "val_loss": val_loss,
                "val_accuracy": val_acc,
                "error_message": None,
                "model": model
            }

        except Exception as e:
            err_msg = f"Failed to load checkpoint for {spec['name']}: {str(e)}"
            print(f"[ModelService ERROR] {err_msg}")
            return {
                "id": spec["id"],
                "name": spec["name"],
                "display_name": spec["display_name"],
                "description": spec["description"],
                "architecture_details": spec["architecture_details"],
                "input_resolution": spec["input_resolution"],
                "badges": spec["badges"],
                "is_loaded": False,
                "checkpoint_available": False,
                "checkpoint_path": str(ckpt_path),
                "num_classes": 3,
                "classes": FINAL_4_CLASSES[:3],
                "target_classes": 4,
                "target_class_names": FINAL_4_CLASSES,
                "is_4class_trained": False,
                "is_4class_ready": True,
                "accuracy_display": spec.get("accuracy_display", "Evaluation pending"),
                "status": "ERROR",
                "status_message": err_msg,
                "error_message": err_msg,
                "model": None
            }

    def _scan_and_preload_models(self):
        """Scan and preload all registered models into memory cache."""
        print("\n" + "=" * 65)
        print("INITIALIZING MODEL REGISTRY & PRELOADING WEIGHTS")
        print("=" * 65)
        for model_id in MODEL_REGISTRY.keys():
            info = self._load_single_model(model_id)
            self._model_cache[model_id] = info
        print("=" * 65 + "\n")

    def get_model(self, model_name: Optional[str] = None) -> Tuple[nn.Module, Dict[str, Any]]:
        """
        Get loaded model instance and its metadata by model name.
        Uses in-memory cache to guarantee zero reload overhead.
        """
        model_id = normalize_model_id(model_name)
        
        # Check in cache
        if model_id not in self._model_cache or not self._model_cache[model_id]["is_loaded"]:
            # Try reloading once in case a new checkpoint was placed
            self._model_cache[model_id] = self._load_single_model(model_id)
            
        entry = self._model_cache[model_id]
        if not entry["is_loaded"] or entry["model"] is None:
            if model_id == "mobilenet":
                raise RuntimeError("MobileNetV2 checkpoint is not available.")
            raise RuntimeError(f"{entry['name']} checkpoint is not available.")
            
        return entry["model"], entry

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Return public list of all registered models with their availability status."""
        result = []
        for model_id in ["mobilenet", "mobilenet_v3"]:
            entry = self._model_cache.get(model_id)
            if not entry:
                entry = self._load_single_model(model_id)
                self._model_cache[model_id] = entry
                
            result.append({
                "id": entry["id"],
                "name": entry["name"],
                "display_name": entry["display_name"],
                "description": entry["description"],
                "architecture_details": entry["architecture_details"],
                "input_resolution": entry["input_resolution"],
                "badges": entry["badges"],
                "checkpoint_available": entry["checkpoint_available"],
                "is_loaded": entry["is_loaded"],
                "status": entry["status"],
                "status_message": entry["status_message"],
                "num_classes": entry["num_classes"],
                "classes": entry["classes"],
                "target_classes": entry["target_classes"],
                "target_class_names": entry["target_class_names"],
                "is_4class_trained": entry["is_4class_trained"],
                "accuracy_display": entry["accuracy_display"],
                "device": str(self.device)
            })
        return result

    def get_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Return information for the requested model (or default model)."""
        model_id = normalize_model_id(model_name)
        entry = self._model_cache.get(model_id)
        if not entry:
            entry = self._load_single_model(model_id)
            self._model_cache[model_id] = entry

        return {
            "model_id": entry["id"],
            "model_name": entry["name"],
            "display_name": entry["display_name"],
            "description": entry["description"],
            "architecture_details": entry["architecture_details"],
            "input_resolution": entry["input_resolution"],
            "badges": entry["badges"],
            "is_loaded": entry["is_loaded"],
            "checkpoint_available": entry["checkpoint_available"],
            "device": str(self.device),
            "checkpoint_path": entry.get("checkpoint_path"),
            "num_classes": entry["num_classes"],
            "classes": entry["classes"],
            "target_classes": entry["target_classes"],
            "target_class_names": entry["target_class_names"],
            "is_4class_ready": entry["is_4class_ready"],
            "is_4class_trained": entry["is_4class_trained"],
            "model_status_message": entry["status_message"],
            "accuracy_display": entry["accuracy_display"],
            "epoch": entry.get("epoch"),
            "val_loss": entry.get("val_loss"),
            "val_accuracy": entry.get("val_accuracy"),
            "error_message": entry.get("error_message"),
            "available_models": self.get_available_models()
        }

    def set_default_model(self, model_name: str) -> Dict[str, Any]:
        """Set the active default model."""
        model_id = normalize_model_id(model_name)
        if model_id not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model architecture: '{model_name}'")
        self.default_model_id = model_id
        return self.get_info(model_id)

