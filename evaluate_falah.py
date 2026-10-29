from pathlib import Path

import torch
import torch.nn as nn
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

from src.dataset.falah_dataset import create_falah_dataloader
from src.models.mobilenet import get_mobilenet_v3_model


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

TEST_PARQUET = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "Falah_Alzheimer_MRI"
    / "data"
    / "test-00000-of-00001-44110b9df98c5585.parquet"
)

CHECKPOINT_PATH = (
    PROJECT_ROOT
    / "checkpoints"
    / "mobilenetv3_falah_weighted_best.pth"
)

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "metrics"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

BATCH_SIZE = 32
IMAGE_SIZE = 224
NUM_CLASSES = 4

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

CLASS_NAMES = [
    "Cognitively Normal",
    "Very Mild Dementia",
    "Mild Dementia",
    "Moderate Dementia",
]


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("FALAH ALZHEIMER MRI - TEST EVALUATION")
    print("=" * 70)

    print(f"Device: {DEVICE}")
    print()

    # --------------------------------------------------------
    # Check files
    # --------------------------------------------------------

    if not TEST_PARQUET.exists():
        raise FileNotFoundError(
            f"Test dataset not found:\n{TEST_PARQUET}"
        )

    if not CHECKPOINT_PATH.exists():
        raise FileNotFoundError(
            f"Checkpoint not found:\n{CHECKPOINT_PATH}"
        )

    # --------------------------------------------------------
    # Load test dataset
    # --------------------------------------------------------

    print("Loading test dataset...")

    test_dataset, test_loader = create_falah_dataloader(
        parquet_path=TEST_PARQUET,
        batch_size=BATCH_SIZE,
        image_size=IMAGE_SIZE,
        shuffle=False,
    )

    print(f"Test samples: {len(test_dataset)}")
    print(f"Test batches: {len(test_loader)}")
    print()

    # --------------------------------------------------------
    # Create model
    # --------------------------------------------------------

    print("Creating MobileNetV3-Large...")

    model = get_mobilenet_v3_model(
        num_classes=NUM_CLASSES,
        pretrained=False,
    )

    # --------------------------------------------------------
    # Load trained checkpoint
    # --------------------------------------------------------

    checkpoint = torch.load(
        CHECKPOINT_PATH,
        map_location=DEVICE,
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model = model.to(DEVICE)

    model.eval()

    print("✓ Checkpoint loaded")
    print(
        f"Training epoch: "
        f"{checkpoint.get('epoch', 'unknown')}"
    )
    print(
        f"Training loss: "
        f"{checkpoint.get('loss', 'unknown')}"
    )
    print()

    # --------------------------------------------------------
    # Loss
    # --------------------------------------------------------

    criterion = nn.CrossEntropyLoss()

    running_loss = 0.0

    all_labels = []
    all_predictions = []

    # --------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------

    print("Running test evaluation...")

    with torch.no_grad():

        for batch in test_loader:

            images = batch["image"].to(DEVICE)
            labels = batch["label"].to(DEVICE)

            outputs = model(images)

            loss = criterion(
                outputs,
                labels,
            )

            predictions = torch.argmax(
                outputs,
                dim=1,
            )

            running_loss += loss.item()

            all_labels.extend(
                labels.cpu().numpy()
            )

            all_predictions.extend(
                predictions.cpu().numpy()
            )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    test_loss = (
        running_loss / len(test_loader)
    )

    accuracy = accuracy_score(
        all_labels,
        all_predictions,
    )

    precision = precision_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0,
    )

    recall = recall_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0,
    )

    f1 = f1_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0,
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("FALAH TEST RESULTS")
    print("=" * 70)

    print(f"Test Loss      : {test_loss:.4f}")
    print(f"Accuracy       : {accuracy * 100:.2f}%")
    print(f"Macro Precision: {precision * 100:.2f}%")
    print(f"Macro Recall   : {recall * 100:.2f}%")
    print(f"Macro F1       : {f1 * 100:.2f}%")

    print("=" * 70)

    # --------------------------------------------------------
    # Classification report
    # --------------------------------------------------------

    print()
    print("CLASSIFICATION REPORT")
    print("=" * 70)

    report = classification_report(
        all_labels,
        all_predictions,
        labels=[0, 1, 2, 3],
        target_names=CLASS_NAMES,
        zero_division=0,
    )

    print(report)

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    cm = confusion_matrix(
        all_labels,
        all_predictions,
        labels=[0, 1, 2, 3],
    )

    print("CONFUSION MATRIX")
    print("=" * 70)

    print("Rows = Actual")
    print("Columns = Predicted")
    print()

    print(
        pd.DataFrame(
            cm,
            index=CLASS_NAMES,
            columns=CLASS_NAMES,
        )
    )

    # --------------------------------------------------------
    # Save metrics
    # --------------------------------------------------------

    metrics = {
        "test_loss": test_loss,
        "accuracy": accuracy,
        "macro_precision": precision,
        "macro_recall": recall,
        "macro_f1": f1,
    }

    metrics_path = (
        OUTPUT_DIR
        / "falah_test_metrics.csv"
    )

    pd.DataFrame([metrics]).to_csv(
        metrics_path,
        index=False,
    )

    # --------------------------------------------------------
    # Save confusion matrix
    # --------------------------------------------------------

    cm_path = (
        OUTPUT_DIR
        / "falah_confusion_matrix.csv"
    )

    pd.DataFrame(
        cm,
        index=CLASS_NAMES,
        columns=CLASS_NAMES,
    ).to_csv(cm_path)

    print()
    print("Saved files:")
    print(metrics_path)
    print(cm_path)

    print()
    print("=" * 70)
    print("EVALUATION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()