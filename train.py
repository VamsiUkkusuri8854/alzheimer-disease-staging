# ============================================================
# ALZHEIMER MRI STAGING
# MOBILENETV3-LARGE TRAINING ENTRY POINT (FOLD 1)
# ============================================================

import sys
from pathlib import Path

# Add project root to sys.path so 'src' and 'config' can be imported anywhere
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch

import config.config as cfg
from src.dataset.dataloaders import get_dataloaders
from src.dataset.class_weights import calculate_class_weights
from src.models.mobilenet import get_mobilenet_v3_model
from src.training.trainer import Trainer


def main():
    print("=" * 70)
    print("ALZHEIMER MRI STAGING - MOBILENETV3-LARGE TRAINING")
    print("=" * 70)

    # 1. Load configuration and initialize directories
    cfg.create_directories()
    cfg.print_config()

    fold = 1
    fold_file = cfg.FOLDS_DIR / f"fold_{fold}.csv"
    # Do NOT overwrite existing 3-class checkpoint; use separate 4-class checkpoint target
    checkpoint_file = cfg.CHECKPOINT_DIR / "fold_1_4class_best_model.pth"

    # 2. Verify metadata exists
    print("\nMetadata Verification")
    print("-" * 70)
    if not fold_file.exists():
        raise FileNotFoundError(
            f"Fold metadata file not found at: {fold_file}\n"
            f"Please run 'python src/dataset/patient_splitter.py' first to generate fold splits."
        )
    print(f"Using fold metadata: {fold_file}")

    # 3. Create fold-1 dataloaders
    print("\nCreating DataLoaders")
    print("-" * 70)
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

    print(f"Training slices:   {len(train_dataset)} ({len(train_loader)} batches)")
    print(f"Validation slices: {len(val_dataset)} ({len(val_loader)} batches)")
    print(f"Test slices:       {len(test_dataset)} ({len(test_loader)} batches) [HELD-OUT]")

    # 4. Calculate class weights from training patients
    print("\nCalculating Patient-Level Class Weights (4-Class Target)")
    print("-" * 70)
    class_weights, class_counts = calculate_class_weights(
        metadata_file=fold_file,
        split="train",
        num_classes=cfg.NUM_CLASSES
    )

    print("Training Patient Distribution:")
    for class_idx in range(cfg.NUM_CLASSES):
        count = int(class_counts.get(class_idx, 0))
        name = cfg.CLASS_NAMES[class_idx]
        print(f"  Class {class_idx} ({name}): {count} patients")

    print(f"Computed Class Weights: {class_weights.tolist()}")

    # 5. Verify 4-Class Training Feasibility
    class_3_count = int(class_counts.get(3, 0))
    if class_3_count == 0:
        print("\n" + "=" * 70)
        print("TRAINING HALTED: Moderate Dementia samples are currently unavailable; 4-class training cannot be performed yet.")
        print("-" * 70)
        print("Reason:")
        print("  - Class 3 (Moderate Dementia, CDR 2.0) has 0 patients in the current dataset.")
        print("  - Supervised 4-class neural network training requires real patient data for all 4 classes.")
        print("  - Fabricating fake MRI data or fake CDR=2.0 labels is strictly prohibited.")
        print("  - To preserve research integrity, training stops here before initializing 4-class weights.")
        print("  - The existing working 3-class checkpoint (checkpoints/fold_1_best_model.pth) is kept intact.")
        print(f"  - Target 4-class checkpoint ({checkpoint_file.name}) will be created once real CDR 2.0 data is available.")
        print("=" * 70)
        return

    # 6. Initialize MobileNetV3-Large trainer
    print("\nInitializing Trainer")
    print("-" * 70)
    trainer = Trainer(
        train_loader=train_loader,
        val_loader=val_loader,
        class_weights=class_weights,
        device=cfg.DEVICE,
        num_classes=cfg.NUM_CLASSES,
        learning_rate=cfg.LEARNING_RATE,
        weight_decay=cfg.WEIGHT_DECAY,
        epochs=cfg.EPOCHS,
        scheduler_factor=cfg.SCHEDULER_FACTOR,
        scheduler_patience=cfg.SCHEDULER_PATIENCE,
        min_lr=cfg.MIN_LR,
        early_stopping_patience=cfg.EARLY_STOPPING_PATIENCE,
        checkpoint_path=checkpoint_file
    )
    print("Trainer initialized successfully.")

    # 7. Train Fold 1
    print("\nStarting Model Training (Fold 1 - 4-Class Target)")
    print("-" * 70)
    history = trainer.train()

    # 8. Print training summary
    print("\n" + "=" * 70)
    print("FOLD 1 (4-CLASS) TRAINING SUMMARY")
    print("=" * 70)
    print(f"Best Epoch:               {trainer.best_epoch}")
    print(f"Best Validation Loss:     {trainer.best_val_loss:.4f}")
    print(f"Best Validation Accuracy: {trainer.best_val_accuracy:.4f}")
    print(f"Best Model Saved At:      {checkpoint_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()