import time
from typing import Dict, Any, List, Optional
import numpy as np
import torch
import torch.nn.functional as F
from backend.services.gradcam_service import compute_model_gradcam

DISCLAIMER_TEXT = (
    "Research prototype only. This prediction is not a medical diagnosis "
    "and must not be used for clinical decision-making."
)

# Configurable MC Dropout passes
MC_DROPOUT_PASSES = 5

# Maximum slices to use for MC Dropout uncertainty estimation.
# The deterministic pass uses ALL informative slices for accuracy.
# MC subsampling preserves representative brain coverage via uniform spacing.
MC_MAX_SLICES = 48


def enable_classifier_dropout(model: torch.nn.Module) -> None:
    """
    Enable only the classifier Dropout layer for Monte Carlo Dropout,
    while keeping batch normalization and convolutional backbone in eval mode.
    Works for both MobileNetV2 and MobileNetV3-Large classifiers.
    """
    model.eval()
    if hasattr(model, "classifier"):
        for module in model.classifier.modules():
            if isinstance(module, torch.nn.Dropout):
                module.train()


def _subsample_indices(total: int, max_count: int) -> List[int]:
    """
    Select up to max_count evenly-spaced indices from range(total).
    Preserves representative coverage of the full volume.
    """
    if total <= max_count:
        return list(range(total))
    step = total / max_count
    return [int(i * step) for i in range(max_count)]


def predict_patient_staging(
    slices_tensor: torch.Tensor,
    model: torch.nn.Module,
    class_names: List[str],
    device: torch.device,
    batch_size: int = 32,
    num_mc_passes: int = None,
    model_name: str = "MobileNetV3-Large",
    model_architecture: str = "MobileNetV3-Large",
    model_accuracy: str = "Evaluation pending",
    model_status_message: str = "",
    is_4class_trained: bool = False,
    target_classes: int = 4,
    representative_slice_tensor: Optional[torch.Tensor] = None,
    representative_slice_uint8: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Run patient-level Alzheimer's disease staging over extracted MRI slices.

    Pipeline:
    1. Slice-level predictions: Forward pass of 224x224 RGB slices through selected CNN model.
    2. Primary aggregation: Mean probability pooling across all valid axial slices.
    3. Uncertainty estimation: Stochastic inference via Monte Carlo Dropout across multiple forward passes.
    4. Confidence calculation: Maximum patient-level probability.

    Args:
        slices_tensor: [N, 3, 224, 224] tensor of normalized slices.
        model: Loaded PyTorch neural network model in eval mode.
        class_names: Names corresponding to active class indices.
        device: CPU or CUDA device.
        batch_size: Inference batch size.
        num_mc_passes: Number of Monte Carlo stochastic passes for uncertainty estimation.
        model_name: Display name of the selected model.
        model_architecture: Specific architecture identifier.
        model_accuracy: Stored evaluation metric or 'Evaluation pending'.
        is_4class_trained: Whether the loaded checkpoint was trained on 4 classes.
        target_classes: Target number of classes in the final 4-class architecture.

    Returns:
        JSON-compliant Dict containing prediction, probabilities, confidence, uncertainty,
        and structured analysis metadata.
    """
    if num_mc_passes is None:
        num_mc_passes = MC_DROPOUT_PASSES

    timings = {}
    t_total_start = time.perf_counter()

    num_slices = slices_tensor.size(0)
    num_classes = len(class_names)

    # --------------------------------------------------------
    # 1. Deterministic Standard Forward Pass (ALL slices)
    # --------------------------------------------------------
    t_inference_start = time.perf_counter()
    model.eval()
    all_slice_probs = []

    with torch.inference_mode():
        for i in range(0, num_slices, batch_size):
            batch = slices_tensor[i : i + batch_size].to(device)
            logits = model(batch)
            probs = F.softmax(logits, dim=1)
            all_slice_probs.append(probs.cpu().numpy())

    slice_probs_matrix = np.concatenate(all_slice_probs, axis=0)  # Shape [N, num_classes]

    # Primary Patient-Level Aggregation: Mean Probability
    patient_probs_mean = np.mean(slice_probs_matrix, axis=0)  # Shape [num_classes]

    timings["model_inference"] = time.perf_counter() - t_inference_start

    # --------------------------------------------------------
    # 2. Uncertainty-Aware Monte Carlo Dropout Inference
    #    Uses subsampled slices for performance optimization
    # --------------------------------------------------------
    t_uncertainty_start = time.perf_counter()

    # Subsample slices for MC Dropout to reduce computation
    mc_indices = _subsample_indices(num_slices, MC_MAX_SLICES)
    mc_slices = slices_tensor[mc_indices]  # [M, 3, 224, 224] where M <= MC_MAX_SLICES
    mc_num_slices = mc_slices.size(0)

    mc_patient_probs = []

    # Activate dropout in the classifier head
    enable_classifier_dropout(model)

    with torch.inference_mode():
        for _ in range(num_mc_passes):
            pass_slice_probs = []
            for i in range(0, mc_num_slices, batch_size):
                batch = mc_slices[i : i + batch_size].to(device)
                logits = model(batch)
                probs = F.softmax(logits, dim=1)
                pass_slice_probs.append(probs.cpu().numpy())

            pass_matrix = np.concatenate(pass_slice_probs, axis=0)
            mc_patient_probs.append(np.mean(pass_matrix, axis=0))

    model.eval()  # Reset back to complete eval mode

    mc_patient_probs_arr = np.array(mc_patient_probs)  # Shape [num_mc_passes, num_classes]

    # Mean across MC passes (smooth estimate)
    smoothed_probs = np.mean(mc_patient_probs_arr, axis=0)

    # Blend deterministic mean and smoothed MC mean for stability
    final_probs = 0.5 * patient_probs_mean + 0.5 * smoothed_probs
    # Re-normalize to ensure sum == 1.0
    final_probs = final_probs / np.sum(final_probs)

    # Uncertainty Calculation:
    # 1) Variance of predicted class across stochastic passes
    # 2) Predictive entropy across classes
    pred_class_idx = int(np.argmax(final_probs))
    pred_class_variance = float(np.var(mc_patient_probs_arr[:, pred_class_idx]))

    # Normalized predictive entropy H(p) / log(C) in [0, 1]
    entropy = -float(np.sum(final_probs * np.log(final_probs + 1e-12)))
    max_entropy = np.log(num_classes) if num_classes > 1 else 1.0
    normalized_entropy = float(entropy / max_entropy)

    # Documented uncertainty measure: combination of predictive entropy and pass variance
    uncertainty_score = float(np.clip(0.7 * normalized_entropy + 0.3 * (pred_class_variance * 10), 0.0, 1.0))

    confidence_score = float(np.max(final_probs))

    timings["uncertainty"] = time.perf_counter() - t_uncertainty_start
    timings["total"] = time.perf_counter() - t_total_start

    # Build probabilities dictionary (preserving exact active class values)
    probabilities_dict = {
        name: round(float(final_probs[i]), 4)
        for i, name in enumerate(class_names)
    }

    # ------------------------------------------------------------------
    # 4-Class UI Integration:
    # When the current checkpoint is a 3-class model, append Moderate
    # Dementia with probability 0.0 so the UI displays all 4 classes.
    # The three existing probabilities are NOT changed and NOT renormalized.
    # Class 3 is a placeholder only; it is never the predicted class while
    # the 3-class checkpoint is active.
    # ------------------------------------------------------------------
    if not is_4class_trained and "Moderate Dementia" not in probabilities_dict:
        probabilities_dict["Moderate Dementia"] = 0.0

    # ------------------------------------------------------------------
    # Genuine Model Attention (Grad-CAM)
    # ------------------------------------------------------------------
    gradcam_b64 = None
    if representative_slice_tensor is not None and representative_slice_uint8 is not None:
        try:
            gradcam_b64 = compute_model_gradcam(
                model=model,
                slice_tensor=representative_slice_tensor,
                slice_uint8=representative_slice_uint8,
                target_class_idx=pred_class_idx,
                device=device
            )
        except Exception as e:
            print(f"[Grad-CAM execution notice]: {e}")
            gradcam_b64 = None

    predicted_class_name = class_names[pred_class_idx]

    # Generate structured summary strictly from model output (matching screenshot reference)
    ai_analysis_summary = (
        f"The model assigned the highest patient-level probability to {predicted_class_name} "
        f"({confidence_score * 100:.1f}%). This result was obtained by aggregating probability distributions "
        f"across informative MRI slices using the selected deep learning model ({model_name})."
    )

    default_status = (
        f"4-Class Alzheimer's Disease Staging model ({model_name}) loaded and active." if is_4class_trained
        else (
            f"Current model: {model_name}. Active checkpoint supports 3 trained classes (CN, Very Mild, Mild). "
            "Moderate Dementia (Class 3 / CDR 2.0) is not trained in this checkpoint and shown as unavailable."
        )
    )

    # Print detailed timing breakdown
    print(f"\n{'='*60}")
    print(f"PREDICTION TIMING BREAKDOWN ({model_name})")
    print(f"{'='*60}")
    print(f"  Deterministic inference   : {timings['model_inference']:.3f} s  ({num_slices} slices)")
    print(f"  MC Dropout uncertainty    : {timings['uncertainty']:.3f} s  ({num_mc_passes} passes × {mc_num_slices} slices)")
    print(f"  Prediction total          : {timings['total']:.3f} s")
    print(f"{'='*60}\n")

    return {
        "success": True,
        "prediction": {
            "class_id": pred_class_idx,
            "class_name": predicted_class_name,
            "confidence": round(confidence_score, 4),
            "uncertainty": round(uncertainty_score, 4),
        },
        "probabilities": probabilities_dict,
        "num_slices": num_slices,
        "informative_slices": num_slices,
        "mc_slices_used": mc_num_slices,
        "mc_passes": num_mc_passes,
        "model": model_name,
        "model_name": model_name,
        "model_architecture": model_architecture,
        "model_accuracy": model_accuracy,
        "input_type": "3D T1-weighted MRI",
        "analysis_level": "Patient-level",
        "aggregation_method": "Mean probability aggregation",
        "processing_time_seconds": round(timings["total"], 3),
        "device": str(device).upper(),
        "ai_analysis_summary": ai_analysis_summary,
        "model_status_message": model_status_message or default_status,
        "heatmap_thumbnail": gradcam_b64,
        "has_attention_visualization": gradcam_b64 is not None,
        "target_num_classes": target_classes,
        "active_num_classes": num_classes,
        "is_4class_ready": True,
        "is_4class_trained": is_4class_trained,
        "uncertainty_details": {
            "method": f"Monte Carlo Dropout ({num_mc_passes} stochastic forward passes)",
            "normalized_entropy": round(normalized_entropy, 4),
            "stochastic_variance": round(pred_class_variance, 6),
            "mc_slices_used": mc_num_slices,
            "total_informative_slices": num_slices,
            "explanation": (
                "The uncertainty estimate reflects model variability across stochastic inference passes. "
                "Higher uncertainty indicates that the model is less consistent in its predictions."
            )
        },
        "timing_breakdown": {
            "model_inference_seconds": round(timings["model_inference"], 3),
            "uncertainty_seconds": round(timings["uncertainty"], 3),
            "prediction_total_seconds": round(timings["total"], 3),
        },
        "disclaimer": DISCLAIMER_TEXT
    }
