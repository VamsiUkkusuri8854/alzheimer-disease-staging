from pathlib import Path

import torch
import torch.nn as nn
from torch.optim import Adam
from tqdm import tqdm

from src.dataset.falah_dataset import create_falah_dataloader
from src.models.mobilenet import get_mobilenet_v3_model


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

TRAIN_PARQUET = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "Falah_Alzheimer_MRI"
    / "data"
    / "train-00000-of-00001-c08a401c53fe5312.parquet"
)

CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

BATCH_SIZE = 32
IMAGE_SIZE = 224
NUM_CLASSES = 4

EPOCHS = 3
LEARNING_RATE = 1e-4

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
    print("FALAH - CLASS WEIGHTED TRAINING")
    print("=" * 70)

    print(f"Device: {DEVICE}")
    print()

    # --------------------------------------------------------
    # Check dataset
    # --------------------------------------------------------

    if not TRAIN_PARQUET.exists():
        raise FileNotFoundError(
            f"Training dataset not found:\n{TRAIN_PARQUET}"
        )

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    dataset, train_loader = create_falah_dataloader(
        parquet_path=TRAIN_PARQUET,
        batch_size=BATCH_SIZE,
        image_size=IMAGE_SIZE,
        shuffle=True,
    )

    print(f"Training samples: {len(dataset)}")
    print(f"Training batches : {len(train_loader)}")
    print()

    # --------------------------------------------------------
    # Calculate class counts
    # --------------------------------------------------------

    labels = dataset.df["label"].astype(int)

    class_counts = []

    for class_id in range(NUM_CLASSES):
        count = int((labels == class_id).sum())
        class_counts.append(count)

    print("Class distribution:")

    for i in range(NUM_CLASSES):
        print(
            f"  {i}: {CLASS_NAMES[i]:25s} "
            f"{class_counts[i]}"
        )

    # --------------------------------------------------------
    # Calculate class weights
    # --------------------------------------------------------

    total_samples = sum(class_counts)

    class_weights = [
        total_samples / (NUM_CLASSES * count)
        if count > 0 else 0.0
        for count in class_counts
    ]

    weights = torch.tensor(
        class_weights,
        dtype=torch.float32,
        device=DEVICE,
    )

    print()
    print("Class weights:")

    for i in range(NUM_CLASSES):
        print(
            f"  {i}: {weights[i].item():.4f}"
        )

    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    print()
    print("Creating MobileNetV3-Large...")

    model = get_mobilenet_v3_model(
        num_classes=NUM_CLASSES,
        pretrained=True,
    )

    model = model.to(DEVICE)

    # --------------------------------------------------------
    # Weighted loss
    # --------------------------------------------------------

    criterion = nn.CrossEntropyLoss(
        weight=weights
    )

    # --------------------------------------------------------
    # Optimizer
    # --------------------------------------------------------

    optimizer = Adam(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    # --------------------------------------------------------
    # Best model tracking
    # --------------------------------------------------------

    best_loss = float("inf")

    checkpoint_path = (
        CHECKPOINT_DIR
        / "mobilenetv3_falah_weighted_best.pth"
    )

    # ========================================================
    # TRAINING
    # ========================================================

    for epoch in range(EPOCHS):

        model.train()

        running_loss = 0.0
        correct = 0
        total = 0

        print()
        print("=" * 70)
        print(f"Epoch {epoch + 1}/{EPOCHS}")
        print("=" * 70)

        progress_bar = tqdm(
            train_loader,
            desc=f"Epoch {epoch + 1}",
        )

        for batch in progress_bar:

            images = batch["image"].to(DEVICE)
            labels_batch = batch["label"].to(DEVICE)

            optimizer.zero_grad()

            outputs = model(images)

            loss = criterion(
                outputs,
                labels_batch,
            )

            loss.backward()

            optimizer.step()

            running_loss += loss.item()

            predictions = torch.argmax(
                outputs,
                dim=1,
            )

            correct += (
                predictions == labels_batch
            ).sum().item()

            total += labels_batch.size(0)

            accuracy = (
                correct / total
            ) * 100

            progress_bar.set_postfix(
                loss=f"{loss.item():.4f}",
                accuracy=f"{accuracy:.2f}%",
            )

        # ----------------------------------------------------
        # Epoch statistics
        # ----------------------------------------------------

        epoch_loss = (
            running_loss / len(train_loader)
        )

        epoch_accuracy = (
            correct / total
        ) * 100

        print()
        print(
            f"Epoch {epoch + 1} "
            f"| Loss: {epoch_loss:.4f} "
            f"| Accuracy: {epoch_accuracy:.2f}%"
        )

        # ----------------------------------------------------
        # Save best model
        # ----------------------------------------------------

        if epoch_loss < best_loss:

            best_loss = epoch_loss

            torch.save(
                {
                    "epoch": epoch + 1,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "loss": epoch_loss,
                    "accuracy": epoch_accuracy,
                    "num_classes": NUM_CLASSES,
                    "class_names": CLASS_NAMES,
                    "class_weights": weights.cpu(),
                    "image_size": IMAGE_SIZE,
                },
                checkpoint_path,
            )

            print()
            print("✓ BEST WEIGHTED MODEL SAVED")
            print(checkpoint_path)

    # ========================================================
    # COMPLETE
    # ========================================================

    print()
    print("=" * 70)
    print("WEIGHTED TRAINING COMPLETED")
    print("=" * 70)

    print(f"Best loss: {best_loss:.4f}")
    print()
    print("Checkpoint:")
    print(checkpoint_path)


if __name__ == "__main__":
    main()