# ============================================================
# ALZHEIMER MRI STAGING
# MOBILENETV2 TRAINING & PATIENT-LEVEL EVALUATION PIPELINE
# ============================================================

import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config.config as cfg
from src.dataset.dataloaders import get_dataloaders
from src.dataset.class_weights import calculate_class_weights
from src.dataset.mri_dataset import MRISliceDataset
from src.models.mobilenet_v2 import get_mobilenet_v2_model
from src.models.mobilenet_v3 import get_mobilenet_v3_model
from src.training.trainer import Trainer

CLASS_NAMES_4 = [
    "Cognitively Normal",
    "Very Mild Dementia",
    "Mild Dementia",
    "Moderate Dementia"
]

CLASS_NAMES_3 = [
    "Cognitively Normal",
    "Very Mild Dementia",
    "Mild Dementia"
]


def inspect_metadata_and_classes():
    """Inspect OASIS metadata and report actual class distribution."""
    metadata_file = cfg.OASIS_METADATA_FILE
    all_folds_file = cfg.FOLDS_DIR / "all_folds.csv"
    fold_1_file = cfg.FOLDS_DIR / "fold_1.csv"

    print("=" * 70)
    print("1. METADATA & CLASS DISTRIBUTION INSPECTION")
    print("=" * 70)

    if not metadata_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

    df_meta = pd.read_csv(metadata_file)
    print(f"Total raw metadata rows: {len(df_meta)}")
    print(f"Unique patient IDs: {df_meta['patient_id'].nunique()}")

    label_counts = {}
    if "class_id" in df_meta.columns:
        counts = df_meta["class_id"].value_counts().to_dict()
    elif "cdr" in df_meta.columns:
        counts = df_meta["cdr"].map({0.0: 0, 0.5: 1, 1.0: 2, 2.0: 3}).value_counts().to_dict()
    else:
        counts = {}

    print("\nActual Dataset Class Distribution:")
    for idx, name in enumerate(CLASS_NAMES_4):
        cnt = int(counts.get(idx, 0))
        label_counts[idx] = cnt
        print(f"  Class {idx} ({name:20s}): {cnt} subjects")

    print("\nFold 1 Split Distribution:")
    if fold_1_file.exists():
        f1_df = pd.read_csv(fold_1_file)
        crosstab = pd.crosstab(f1_df["split"], f1_df["label"])
        print(crosstab)

    # Statistical Validity check for 4-class experiment
    class_3_count = label_counts.get(3, 0)
    print("\n" + "-" * 70)
    print("4-CLASS STATISTICAL VALIDITY CHECK:")
    if class_3_count == 0:
        print("  [ALERT] Class 3 (Moderate Dementia, CDR=2.0) has 0 samples in OASIS cohort.")
        print("  [ALERT] 4-class stratified cross-validation is NOT statistically possible.")
        print("  [ACTION] Training MobileNetV2 on the valid 3-class cohort (76 patients, Fold 1)")
        print("           with 4-class architecture support, matching MobileNetV3-Large.")
    else:
        print(f"  [OK] Class 3 has {class_3_count} samples.")
    print("-" * 70)

    return label_counts


def evaluate_patient_level(model, split="test", fold=1, device=None, model_name="MobileNetV2"):
    """
    Perform patient-level evaluation by aggregating slice predictions with mean pooling.
    Returns comprehensive metrics dictionary.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model.eval()
    fold_file = cfg.FOLDS_DIR / f"fold_{fold}.csv"
    fold_df = pd.read_csv(fold_file)
    split_df = fold_df[fold_df["split"] == split].reset_index(drop=True)

    processed_dir = cfg.PROCESSED_DIR
    patient_ids = []
    y_true = []
    y_pred = []
    y_probs = []
    patient_inference_times = []

    slice_transform = MRISliceDataset(metadata_file=fold_file, split=split, fold=fold).transform

    print(f"\nEvaluating {model_name} at PATIENT LEVEL on Fold {fold} '{split}' split ({len(split_df)} patients)...")

    with torch.no_grad():
        for row in split_df.itertuples():
            pid = row.patient_id
            true_label = int(row.label)

            slice_dir = processed_dir / pid / "slices"
            if not slice_dir.exists():
                print(f"  Warning: Slice dir not found for {pid}")
                continue

            slice_files = sorted(slice_dir.glob("*.png"))
            if not slice_files:
                continue

            t0 = time.perf_counter()

            # Load and batch slices for this patient
            from PIL import Image
            tensors = []
            for sf in slice_files:
                img = Image.open(sf).convert("RGB")
                tensors.append(slice_transform(img))

            batch_tensor = torch.stack(tensors).to(device)  # [S, 3, 224, 224]

            # Forward pass through model
            logits = model(batch_tensor)  # [S, num_classes]
            slice_probs = F.softmax(logits, dim=-1)  # [S, num_classes]

            # Patient-level mean probability aggregation
            patient_mean_probs = slice_probs.mean(dim=0).cpu().numpy()  # [num_classes]
            predicted_class = int(np.argmax(patient_mean_probs))

            t_elapsed = time.perf_counter() - t0

            patient_ids.append(pid)
            y_true.append(true_label)
            y_pred.append(predicted_class)
            y_probs.append(patient_mean_probs.tolist())
            patient_inference_times.append(t_elapsed)

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    # Calculate actual metrics
    accuracy = float(accuracy_score(y_true, y_pred))
    macro_prec = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    macro_rec = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    weighted_prec = float(precision_score(y_true, y_pred, average="weighted", zero_division=0))
    weighted_rec = float(recall_score(y_true, y_pred, average="weighted", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    present_classes = sorted(list(set(y_true) | set(y_pred)))
    class_labels = [CLASS_NAMES_3[c] for c in present_classes]

    cm = confusion_matrix(y_true, y_pred, labels=present_classes).tolist()
    avg_inference_time = float(np.mean(patient_inference_times)) if patient_inference_times else 0.0
    total_inference_time = float(np.sum(patient_inference_times)) if patient_inference_times else 0.0

    report = classification_report(
        y_true,
        y_pred,
        labels=present_classes,
        target_names=class_labels,
        zero_division=0,
        output_dict=True
    )

    metrics = {
        "model_name": model_name,
        "evaluation_type": "patient_level_mean_aggregation",
        "fold": fold,
        "split": split,
        "total_patients": len(y_true),
        "num_classes": len(present_classes),
        "classes": class_labels,
        "accuracy": round(accuracy, 4),
        "accuracy_percent": round(accuracy * 100, 2),
        "macro_precision": round(macro_prec, 4),
        "macro_precision_percent": round(macro_prec * 100, 2),
        "macro_recall": round(macro_rec, 4),
        "macro_recall_percent": round(macro_rec * 100, 2),
        "macro_f1": round(macro_f1, 4),
        "macro_f1_percent": round(macro_f1 * 100, 2),
        "weighted_precision": round(weighted_prec, 4),
        "weighted_precision_percent": round(weighted_prec * 100, 2),
        "weighted_recall": round(weighted_rec, 4),
        "weighted_recall_percent": round(weighted_rec * 100, 2),
        "weighted_f1": round(weighted_f1, 4),
        "weighted_f1_percent": round(weighted_f1 * 100, 2),
        "confusion_matrix": cm,
        "confusion_matrix_classes": class_labels,
        "classification_report": report,
        "avg_inference_time_seconds_per_volume": round(avg_inference_time, 4),
        "total_inference_time_seconds": round(total_inference_time, 4),
        "patient_predictions": [
            {
                "patient_id": pid,
                "true_label": int(yt),
                "true_class": CLASS_NAMES_3[yt],
                "pred_label": int(yp),
                "pred_class": CLASS_NAMES_3[yp],
                "correct": bool(yt == yp),
                "probabilities": probs
            }
            for pid, yt, yp, probs in zip(patient_ids, y_true, y_pred, y_probs)
        ]
    }

    print("\n" + "=" * 70)
    print(f"PATIENT-LEVEL TEST RESULTS: {model_name}")
    print("=" * 70)
    print(f"Accuracy         : {metrics['accuracy_percent']}% ({int(sum(y_true == y_pred))}/{len(y_true)} patients)")
    print(f"Macro Precision  : {metrics['macro_precision_percent']}%")
    print(f"Macro Recall     : {metrics['macro_recall_percent']}%")
    print(f"Macro F1-Score   : {metrics['macro_f1_percent']}%")
    print(f"Weighted F1-Score: {metrics['weighted_f1_percent']}%")
    print(f"Avg Time / Volume: {metrics['avg_inference_time_seconds_per_volume']:.4f} s")
    print(f"Confusion Matrix (Rows=True, Cols=Pred):\n{np.array(cm)}")
    print("=" * 70)

    return metrics


def train_and_evaluate_mobilenet_v2():
    """Train MobileNetV2 on Fold 1 and evaluate patient-level metrics."""
    cfg.create_directories()
    device = torch.device(cfg.DEVICE)
    fold = 1
    fold_file = cfg.FOLDS_DIR / f"fold_{fold}.csv"
    num_classes = 3  # 3 classes available in OASIS-1

    checkpoint_file = cfg.CHECKPOINT_DIR / "mobilenetv2_best.pth"

    print("\n" + "=" * 70)
    print("STARTING MOBILENETV2 TRAINING ON FOLD 1")
    print("=" * 70)

    # 1. Dataloaders
    (
        train_loader,
        val_loader,
        test_loader,
        train_dataset,
        val_dataset,
        test_dataset
    ) = get_dataloaders(
        fold=fold,
        batch_size=cfg.BATCH_SIZE,
        num_workers=cfg.NUM_WORKERS,
        pin_memory=cfg.PIN_MEMORY,
        metadata_file=fold_file
    )

    # 2. Class weights
    class_weights, class_counts = calculate_class_weights(
        metadata_file=fold_file,
        split="train",
        num_classes=num_classes
    )
    print(f"Computed Class Weights: {class_weights.tolist()}")

    # 3. Model
    model = get_mobilenet_v2_model(num_classes=num_classes, pretrained=True)

    # 4. Trainer
    trainer = Trainer(
        train_loader=train_loader,
        val_loader=val_loader,
        class_weights=class_weights,
        model=model,
        device=device,
        num_classes=num_classes,
        learning_rate=cfg.LEARNING_RATE,
        weight_decay=cfg.WEIGHT_DECAY,
        epochs=3,
        scheduler_factor=cfg.SCHEDULER_FACTOR,
        scheduler_patience=cfg.SCHEDULER_PATIENCE,
        min_lr=cfg.MIN_LR,
        early_stopping_patience=cfg.EARLY_STOPPING_PATIENCE,
        checkpoint_path=checkpoint_file
    )

    history = trainer.train()

    print(f"\nLoading best checkpoint for evaluation: {checkpoint_file}")
    ckpt = torch.load(checkpoint_file, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])

    # 5. Evaluate MobileNetV2 on Test Set at Patient Level
    metrics_v2 = evaluate_patient_level(
        model=model,
        split="test",
        fold=fold,
        device=device,
        model_name="MobileNetV2"
    )

    # Save metrics JSON
    metrics_v2_json_path = cfg.METRICS_DIR / "mobilenetv2_metrics.json"
    metrics_v2_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_v2_json_path, "w") as f:
        json.dump(metrics_v2, f, indent=2)
    print(f"Saved MobileNetV2 metrics to: {metrics_v2_json_path}")

    # Also evaluate MobileNetV3-Large for exact head-to-head comparison
    v3_ckpt_path = cfg.CHECKPOINT_DIR / "fold_1_best_model.pth"
    if v3_ckpt_path.exists():
        print(f"\nEvaluating MobileNetV3-Large from: {v3_ckpt_path}")
        model_v3 = get_mobilenet_v3_model(num_classes=num_classes, pretrained=False)
        ckpt_v3 = torch.load(v3_ckpt_path, map_location=device)
        model_v3.load_state_dict(ckpt_v3["model_state_dict"])
        model_v3.to(device)

        metrics_v3 = evaluate_patient_level(
            model=model_v3,
            split="test",
            fold=fold,
            device=device,
            model_name="MobileNetV3-Large"
        )

        metrics_v3_json_path = cfg.METRICS_DIR / "mobilenetv3_metrics.json"
        with open(metrics_v3_json_path, "w") as f:
            json.dump(metrics_v3, f, indent=2)
        print(f"Saved MobileNetV3 metrics to: {metrics_v3_json_path}")

        # Summary comparison table
        print("\n" + "=" * 70)
        print("HEAD-TO-HEAD MODEL COMPARISON (PATIENT-LEVEL TEST SET)")
        print("=" * 70)
        print(f"{'Metric':<25} | {'MobileNetV2':<18} | {'MobileNetV3-Large':<18}")
        print("-" * 70)
        print(f"{'Accuracy':<25} | {metrics_v2['accuracy_percent']:>17.2f}% | {metrics_v3['accuracy_percent']:>17.2f}%")
        print(f"{'Macro Precision':<25} | {metrics_v2['macro_precision_percent']:>17.2f}% | {metrics_v3['macro_precision_percent']:>17.2f}%")
        print(f"{'Macro Recall':<25} | {metrics_v2['macro_recall_percent']:>17.2f}% | {metrics_v3['macro_recall_percent']:>17.2f}%")
        print(f"{'Macro F1-Score':<25} | {metrics_v2['macro_f1_percent']:>17.2f}% | {metrics_v3['macro_f1_percent']:>17.2f}%")
        print(f"{'Weighted F1-Score':<25} | {metrics_v2['weighted_f1_percent']:>17.2f}% | {metrics_v3['weighted_f1_percent']:>17.2f}%")
        print(f"{'Inference Time/Vol (s)':<25} | {metrics_v2['avg_inference_time_seconds_per_volume']:>18.4f} | {metrics_v3['avg_inference_time_seconds_per_volume']:>18.4f}")
        print("=" * 70)

    return metrics_v2


if __name__ == "__main__":
    inspect_metadata_and_classes()
    train_and_evaluate_mobilenet_v2()
