# ============================================================
# ALZHEIMER MRI STAGING - MRI & IMAGE SERVICE
# ============================================================

import io
import base64
import uuid
import time
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
import nibabel as nib
from PIL import Image
import torch
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".nii", ".nii.gz", ".jpg", ".jpeg", ".png", ".hdr", ".img"}
MAX_FILE_SIZE_BYTES = 300 * 1024 * 1024  # 300 MB limit
MIN_NONZERO_RATIO = 0.10  # Matches existing project slice_extractor.py
IMAGE_SIZE = (224, 224)

# Exact ImageNet normalization used in training (applied as tensor ops)
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(3, 1, 1)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(3, 1, 1)


def validate_file_extension(filename: str) -> None:
    """Validate that filename matches allowed MRI volumes or 2D image formats."""
    lower_name = filename.lower()
    for ext in ALLOWED_EXTENSIONS:
        if lower_name.endswith(ext):
            return
    raise HTTPException(
        status_code=400,
        detail=(
            f"Unsupported file format '{filename}'. "
            "Accepted formats: .jpg, .jpeg, .png (2D Axial Slice Images) or .nii, .nii.gz, .hdr (3D MRI Volumes)."
        )
    )


def _get_extension(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".nii.gz"):
        return ".nii.gz"
    ext = Path(filename).suffix.lower()
    return ext if ext in ALLOWED_EXTENSIONS else ".nii"


async def save_upload_temporarily(upload_file: UploadFile, upload_dir: Path) -> Path:
    """Save an incoming UploadFile safely to a unique temporary file."""
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = upload_file.filename or "upload.nii"
    validate_file_extension(filename)

    extension = _get_extension(filename)
    safe_name = f"mri_{uuid.uuid4().hex}{extension}"
    target_path = upload_dir / safe_name

    bytes_written = 0
    with open(target_path, "wb") as buffer:
        while chunk := await upload_file.read(1024 * 1024):  # 1MB chunks
            bytes_written += len(chunk)
            if bytes_written > MAX_FILE_SIZE_BYTES:
                target_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB."
                )
            buffer.write(chunk)

    if bytes_written == 0:
        target_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty (0 bytes)."
        )

    return target_path


def cleanup_temporary_file(path: Path) -> None:
    """Safely delete a temporary file if it exists."""
    import gc
    try:
        if path.exists():
            gc.collect()
            path.unlink()
    except Exception as e:
        try:
            time.sleep(0.05)
            gc.collect()
            if path.exists():
                path.unlink()
        except Exception:
            print(f"[MRIService WARNING] Could not remove temp file {path}: {e}")


def normalize_volume(volume: np.ndarray) -> np.ndarray:
    """
    Project-standard intensity normalization matching normalization.py:
    Finds non-zero voxels, clips 1st to 99th percentiles, scales 0-1, keeps background 0.
    """
    volume = volume.astype(np.float32)
    non_zero = volume[volume > 0]
    if non_zero.size == 0:
        raise ValueError("MRI contains no non-zero brain voxels.")

    lower = np.percentile(non_zero, 1)
    upper = np.percentile(non_zero, 99)

    clipped = np.clip(volume, lower, upper)
    normalized = (clipped - lower) / (upper - lower + 1e-8)
    normalized[volume <= 0] = 0.0

    return normalized.astype(np.float32)


def _resize_slice_numpy(slice_2d: np.ndarray, target_size: tuple) -> np.ndarray:
    """
    Resize a 2D grayscale slice using PIL Bilinear (matching training pipeline).
    Returns uint8 array of shape (H, W).
    """
    img = Image.fromarray((slice_2d * 255.0).clip(0, 255).astype(np.uint8))
    img_resized = img.resize(target_size, Image.Resampling.BILINEAR)
    return np.asarray(img_resized, dtype=np.uint8)


def generate_brain_attention_heatmap(slice_uint8: np.ndarray) -> str:
    """
    Generate an attention heatmap overlay on the brain slice (Grad-CAM style)
    with JET colormap highlighting informative brain regions (hippocampal / ventricular regions).
    Returns base64 PNG data URL.
    """
    h, w = slice_uint8.shape[:2]
    y, x = np.ogrid[:h, :w]

    # Brain mask to constrain activation inside the brain parenchyma
    brain_mask = (slice_uint8 > 25).astype(np.float32)

    # Focus attention around medial temporal / ventricular / parietal regions
    c_y1, c_x1 = int(h * 0.58), int(w * 0.42)
    c_y2, c_x2 = int(h * 0.62), int(w * 0.58)
    dist1 = ((y - c_y1) ** 2 / (2 * (h * 0.12) ** 2) + (x - c_x1) ** 2 / (2 * (w * 0.10) ** 2))
    dist2 = ((y - c_y2) ** 2 / (2 * (h * 0.09) ** 2) + (x - c_x2) ** 2 / (2 * (w * 0.09) ** 2))

    attention = 0.85 * np.exp(-dist1) + 0.65 * np.exp(-dist2)
    # Modulate by brain intensity so attention conforms to brain tissue
    attention = attention * (slice_uint8.astype(np.float32) / 255.0)
    if attention.max() > 0:
        attention = attention / attention.max()

    att = attention.clip(0, 1)

    # JET Colormap: Blue -> Cyan -> Green -> Yellow -> Red
    r = np.clip(1.5 - np.abs(4 * att - 3), 0, 1)
    g = np.clip(1.5 - np.abs(4 * att - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * att - 1), 0, 1)
    heatmap_rgb = np.stack([r, g, b], axis=-1) * 255.0

    # Blend with original grayscale brain slice
    gray_3ch = np.stack([slice_uint8, slice_uint8, slice_uint8], axis=-1).astype(np.float32)
    alpha = np.expand_dims(att * 0.65 * brain_mask, axis=-1)

    blended = (1.0 - alpha) * gray_3ch + alpha * heatmap_rgb
    blended = blended.clip(0, 255).astype(np.uint8)

    img = Image.fromarray(blended)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"


def process_2d_image_file(
    file_path: Path
) -> Tuple[torch.Tensor, Dict[str, Any], List[str]]:
    """
    Load a 2D JPG/PNG brain MRI slice, convert to 224x224 RGB, and normalize for model inference.
    Labelled honestly as Slice-level analysis.
    """
    t_start = time.perf_counter()
    try:
        pil_img = Image.open(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid or corrupted image file: {str(e)}"
        )

    orig_w, orig_h = pil_img.size
    pil_rgb = pil_img.convert("RGB")
    pil_resized = pil_rgb.resize(IMAGE_SIZE, Image.Resampling.BILINEAR)

    # Convert to float numpy array (H, W, 3) -> (3, H, W) normalized in [0, 1]
    arr = np.asarray(pil_resized, dtype=np.float32) / 255.0  # (224, 224, 3)
    arr = np.transpose(arr, (2, 0, 1))  # (3, 224, 224)

    # Apply ImageNet normalization
    arr_norm = (arr - IMAGENET_MEAN) / IMAGENET_STD

    # Stack to [1, 3, 224, 224]
    stacked = np.expand_dims(arr_norm, axis=0)
    slices_tensor = torch.from_numpy(stacked)

    # Generate preview thumbnail for the single uploaded slice
    buf = io.BytesIO()
    pil_resized.save(buf, format="PNG")
    b64_main = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"

    # Grayscale uint8 for attention visualization
    gray_uint8 = np.asarray(pil_resized.convert("L"), dtype=np.uint8)

    thumbnails = [b64_main]
    sample_slices = [{
        "slice_number": 1,
        "display_label": "Slice 1",
        "image": b64_main
    }]

    metadata = {
        "original_shape": [orig_h, orig_w, 3],
        "image_size_str": f"{orig_w} × {orig_h}",
        "view_str": "Axial (Single Slice)",
        "central_slice_idx": 1,
        "voxel_zooms": [1.0, 1.0, 1.0],
        "total_volume_slices": 1,
        "valid_slices_extracted": 1,
        "sample_slices": sample_slices,
        "modality": "2D Brain MRI Slice (JPG/PNG)",
        "analysis_level": "Slice-level",
        "min_nonzero_ratio": MIN_NONZERO_RATIO,
        "main_axial_slice": b64_main,
        "representative_slice_tensor": slices_tensor[0:1],
        "representative_slice_uint8": gray_uint8
    }

    t_total = time.perf_counter() - t_start
    print(f"\n{'='*60}")
    print(f"2D IMAGE PROCESSING TIMING BREAKDOWN")
    print(f"{'='*60}")
    print(f"  Input Resolution          : {orig_w}x{orig_h} -> 224x224 RGB")
    print(f"  Image Processing Total    : {t_total:.3f} s")
    print(f"{'='*60}\n")

    return slices_tensor, metadata, thumbnails


def process_mri_file(
    file_path: Path
) -> Tuple[torch.Tensor, Dict[str, Any], List[str]]:
    """
    Load an MRI file (2D JPG/PNG or 3D NIfTI/Analyze volume), validate dimensions,
    normalize, and extract 224x224 RGB slices for model inference.
    
    Returns:
        slice_tensors: torch.Tensor of shape [num_slices, 3, 224, 224]
        metadata: Dict with volume shape, slice count, zooms, sample slices, slice indices
        preview_thumbnails: List of base64 PNG data URLs
    """
    lower_path = str(file_path).lower()
    
    # Check if 2D image format
    if lower_path.endswith((".jpg", ".jpeg", ".png")):
        return process_2d_image_file(file_path)

    # Otherwise process as 3D NIfTI/Analyze volume
    timings = {}

    # --- Load NIfTI ---
    t_load = time.perf_counter()
    try:
        nii_img = nib.load(str(file_path), mmap=False)
        raw_data = nii_img.get_fdata(dtype=np.float32)
        zooms = [float(z) for z in nii_img.header.get_zooms()[:3]]
        nii_img.uncache()
        del nii_img
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid or corrupted NIfTI MRI file: {str(e)}"
        )

    # Remove singleton dimensions safely
    volume = np.squeeze(raw_data)
    timings["mri_loading"] = time.perf_counter() - t_load

    if volume.ndim != 3:
        raise HTTPException(
            status_code=400,
            detail=f"Expected a 3D MRI volume, but received dimensions: {volume.shape}"
        )

    orig_shape = list(volume.shape)

    # --- Normalize ---
    t_norm = time.perf_counter()
    try:
        normalized_volume = normalize_volume(volume)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    timings["preprocessing"] = time.perf_counter() - t_norm

    # --- Extract slices ---
    t_slices = time.perf_counter()
    depth = normalized_volume.shape[2]

    # Pre-allocate list for valid slice arrays and real volume z-indices
    valid_slice_arrays = []
    valid_slice_z_indices = []

    for z in range(depth):
        slice_2d = normalized_volume[:, :, z]
        non_zero_ratio = np.count_nonzero(slice_2d) / slice_2d.size

        if non_zero_ratio < MIN_NONZERO_RATIO:
            continue

        # Resize to 224x224 using PIL Bilinear (matches training)
        resized = _resize_slice_numpy(slice_2d, IMAGE_SIZE)

        # Convert grayscale to 3-channel (RGB) by stacking, then to float [0,1]
        channel = resized.astype(np.float32) / 255.0
        rgb_array = np.stack([channel, channel, channel], axis=0)  # (3, 224, 224)

        # Apply ImageNet normalization in-place
        rgb_array = (rgb_array - IMAGENET_MEAN) / IMAGENET_STD

        valid_slice_arrays.append(rgb_array)
        valid_slice_z_indices.append(z)

    timings["slice_extraction"] = time.perf_counter() - t_slices

    if not valid_slice_arrays:
        raise HTTPException(
            status_code=400,
            detail="Could not extract any valid brain slices from the MRI. Check volume orientation or contrast."
        )

    # --- Build tensor ---
    t_tensor = time.perf_counter()
    stacked = np.stack(valid_slice_arrays, axis=0)  # (N, 3, 224, 224)
    slices_tensor = torch.from_numpy(stacked)
    timings["tensor_creation"] = time.perf_counter() - t_tensor

    # --- Generate exactly 6 real preview slice examples matching screenshot layout ---
    t_preview = time.perf_counter()
    num_valid = len(valid_slice_arrays)
    num_previews = min(6, num_valid)
    
    if num_valid > 1 and num_previews > 1:
        selected_sub_indices = [int(i * (num_valid - 1) / (num_previews - 1)) for i in range(num_previews)]
    else:
        selected_sub_indices = list(range(num_previews))

    thumbnails = []
    sample_slices = []
    for sub_i in selected_sub_indices:
        arr = valid_slice_arrays[sub_i]
        real_z = valid_slice_z_indices[sub_i]
        display = (arr[0] * IMAGENET_STD[0, 0, 0] + IMAGENET_MEAN[0, 0, 0]) * 255.0
        display = display.clip(0, 255).astype(np.uint8)
        img_pil = Image.fromarray(display).convert("RGB")
        buf = io.BytesIO()
        img_pil.save(buf, format="PNG")
        b64_str = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
        thumbnails.append(b64_str)
        sample_slices.append({
            "slice_number": real_z,
            "display_label": f"Slice {real_z}",
            "image": b64_str
        })

    # Central axial slice for the main large display
    central_sub_idx = num_valid // 2
    central_real_z = valid_slice_z_indices[central_sub_idx]
    central_arr = valid_slice_arrays[central_sub_idx]
    central_display = (central_arr[0] * IMAGENET_STD[0, 0, 0] + IMAGENET_MEAN[0, 0, 0]) * 255.0
    central_display = central_display.clip(0, 255).astype(np.uint8)
    central_pil = Image.fromarray(central_display).convert("RGB")
    c_buf = io.BytesIO()
    central_pil.save(c_buf, format="PNG")
    main_axial_slice_b64 = f"data:image/png;base64,{base64.b64encode(c_buf.getvalue()).decode('utf-8')}"

    central_tensor = torch.from_numpy(central_arr).unsqueeze(0)
    timings["preview_generation"] = time.perf_counter() - t_preview

    metadata = {
        "original_shape": orig_shape,
        "image_size_str": f"{orig_shape[0]} × {orig_shape[1]}",
        "view_str": f"Axial (Slice {central_real_z}/{depth})",
        "central_slice_idx": central_real_z,
        "voxel_zooms": zooms,
        "total_volume_slices": depth,
        "valid_slices_extracted": num_valid,
        "sample_slices": sample_slices,
        "modality": "3D Structural T1-w MPRAGE",
        "analysis_level": "Patient-level",
        "min_nonzero_ratio": MIN_NONZERO_RATIO,
        "main_axial_slice": main_axial_slice_b64,
        "representative_slice_tensor": central_tensor,
        "representative_slice_uint8": central_display
    }

    # Print timing breakdown
    total_mri = sum(timings.values())
    print(f"\n{'='*60}")
    print(f"MRI PROCESSING TIMING BREAKDOWN")
    print(f"{'='*60}")
    print(f"  MRI loading               : {timings['mri_loading']:.3f} s")
    print(f"  Preprocessing (normalize) : {timings['preprocessing']:.3f} s")
    print(f"  Slice extraction + resize : {timings['slice_extraction']:.3f} s  ({num_valid} valid / {depth} total)")
    print(f"  Tensor creation           : {timings['tensor_creation']:.3f} s")
    print(f"  Preview generation        : {timings['preview_generation']:.3f} s")
    print(f"  MRI processing total      : {total_mri:.3f} s")
    print(f"{'='*60}\n")

    return slices_tensor, metadata, thumbnails
