# ============================================================
# ALZHEIMER MRI STAGING - GENUINE MODEL ATTENTION (GRAD-CAM)
# ============================================================

import io
import base64
from typing import Optional
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image


def compute_model_gradcam(
    model: torch.nn.Module,
    slice_tensor: torch.Tensor,
    slice_uint8: np.ndarray,
    target_class_idx: int,
    device: Optional[torch.device] = None
) -> Optional[str]:
    """
    Compute genuine Grad-CAM attention heatmap for a specific model prediction.
    Extracts gradient activations from the final convolutional feature layer of the
    active CNN model (MobileNetV2 or MobileNetV3-Large).

    Returns:
        Base64 PNG data URL if successfully generated, or None if unavailable.
    """
    try:
        # 1. Locate the final convolutional block of the model
        if hasattr(model, "features") and len(model.features) > 0:
            target_layer = model.features[-1]
        else:
            return None

        activations = []
        gradients = []

        def forward_hook(module, input, output):
            activations.append(output)

        def backward_hook(module, grad_input, grad_output):
            if grad_output and len(grad_output) > 0:
                gradients.append(grad_output[0])

        h_fwd = target_layer.register_forward_hook(forward_hook)
        h_bwd = target_layer.register_full_backward_hook(backward_hook)

        # 2. Prepare single-slice tensor with gradient tracking
        if device is None:
            device = next(model.parameters()).device

        x = slice_tensor.clone().detach().to(device)
        if x.dim() == 3:
            x = x.unsqueeze(0)  # Shape: [1, 3, 224, 224]
        x.requires_grad_(True)

        model.eval()
        model.zero_grad()

        # Forward pass
        logits = model(x)
        num_classes = logits.size(1)
        if target_class_idx >= num_classes:
            target_class_idx = int(logits.argmax(dim=1).item())

        score = logits[0, target_class_idx]
        score.backward()

        h_fwd.remove()
        h_bwd.remove()

        if not activations or not gradients:
            return None

        act = activations[0]  # Shape: [1, C, H', W']
        grad = gradients[0]   # Shape: [1, C, H', W']

        # 3. Channel-wise gradient pooling and weighted activation sum
        weights = grad.mean(dim=(2, 3), keepdim=True)
        cam = F.relu((weights * act).sum(dim=1, keepdim=True))

        # 4. Upsample to slice resolution 224x224
        cam = F.interpolate(cam, size=(224, 224), mode="bilinear", align_corners=False)
        cam_arr = cam.squeeze().cpu().detach().numpy()

        cam_min, cam_max = cam_arr.min(), cam_arr.max()
        if cam_max - cam_min > 1e-7:
            cam_norm = (cam_arr - cam_min) / (cam_max - cam_min)
        else:
            cam_norm = np.zeros_like(cam_arr)

        # Brain parenchyma mask
        h, w = slice_uint8.shape[:2]
        brain_mask = (slice_uint8 > 20).astype(np.float32)
        cam_norm = cam_norm * brain_mask

        # 5. Apply JET Colormap: Blue -> Cyan -> Green -> Yellow -> Red
        att = np.clip(cam_norm, 0.0, 1.0)
        r = np.clip(1.5 - np.abs(4 * att - 3), 0.0, 1.0)
        g = np.clip(1.5 - np.abs(4 * att - 2), 0.0, 1.0)
        b = np.clip(1.5 - np.abs(4 * att - 1), 0.0, 1.0)
        heatmap_rgb = np.stack([r, g, b], axis=-1) * 255.0

        # Blend with grayscale brain slice
        gray_3ch = np.stack([slice_uint8, slice_uint8, slice_uint8], axis=-1).astype(np.float32)
        alpha = np.expand_dims(att * 0.65 * brain_mask, axis=-1)

        blended = (1.0 - alpha) * gray_3ch + alpha * heatmap_rgb
        blended = np.clip(blended, 0, 255).astype(np.uint8)

        img = Image.fromarray(blended)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"

    except Exception as e:
        print(f"[Grad-CAM Notice] Model attention visualization unavailable: {e}")
        return None
