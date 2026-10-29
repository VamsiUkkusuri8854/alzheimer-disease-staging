# ============================================================
# ALZHEIMER MRI STAGING
# MODEL TRAINER
# ============================================================

import sys
from pathlib import Path
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score

# Robust project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.mobilenet import get_mobilenet_v3_model


class Trainer:
    """
    Trainer for MobileNetV3-Large Alzheimer MRI staging.
    
    Includes:
    - CrossEntropyLoss with patient-level class weights
    - Adam optimizer with weight decay
    - ReduceLROnPlateau learning rate scheduler
    - Early stopping
    - Model checkpointing based primarily on validation loss
    - Strict isolation: TEST set is NEVER used during training or model selection
    """

    def __init__(
        self,
        train_loader,
        val_loader,
        class_weights,
        model=None,
        device=None,
        num_classes=4,
        learning_rate=1e-4,
        weight_decay=1e-4,
        epochs=10,
        scheduler_factor=0.5,
        scheduler_patience=2,
        min_lr=1e-7,
        early_stopping_patience=4,
        checkpoint_path="checkpoints/fold_1_4class_best_model.pth"
    ):
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.num_classes = num_classes
        self.epochs = epochs
        self.early_stopping_patience = early_stopping_patience

        # Setup device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Setup checkpoint path
        self.checkpoint_path = Path(checkpoint_path)
        if not self.checkpoint_path.is_absolute():
            self.checkpoint_path = PROJECT_ROOT / self.checkpoint_path

        # Setup model
        if model is None:
            self.model = get_mobilenet_v3_model(
                num_classes=self.num_classes,
                pretrained=True
            )
        else:
            self.model = model

        self.model = self.model.to(self.device)

        # Loss function with class weights
        class_weights = class_weights.to(self.device)
        self.criterion = nn.CrossEntropyLoss(weight=class_weights)

        # Optimizer
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )

        # Learning rate scheduler
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode="min",
            factor=scheduler_factor,
            patience=scheduler_patience,
            min_lr=min_lr
        )

        # Tracking metrics
        self.history = {
            "train_loss": [],
            "train_accuracy": [],
            "val_loss": [],
            "val_accuracy": []
        }

        self.best_val_loss = float("inf")
        self.best_val_accuracy = 0.0
        self.best_epoch = 0
        self.epochs_without_improvement = 0

    def train_one_epoch(self):
        """Train the model for one single epoch over train_loader."""
        self.model.train()
        running_loss = 0.0
        all_preds = []
        all_labels = []
        total_samples = 0

        for i, batch in enumerate(self.train_loader, 1):
            images = batch["image"].to(self.device)
            labels = batch["label"].to(self.device)

            self.optimizer.zero_grad()

            outputs = self.model(images)
            loss = self.criterion(outputs, labels)

            loss.backward()
            self.optimizer.step()

            batch_size = images.size(0)
            running_loss += loss.item() * batch_size
            total_samples += batch_size

            preds = torch.argmax(outputs, dim=1)
            all_preds.extend(preds.detach().cpu().numpy())
            all_labels.extend(labels.detach().cpu().numpy())

            if i % 50 == 0 or i == len(self.train_loader):
                print(f"  Batch [{i}/{len(self.train_loader)}] Loss: {loss.item():.4f}", flush=True)

        epoch_loss = running_loss / total_samples
        epoch_accuracy = accuracy_score(all_labels, all_preds)

        return epoch_loss, epoch_accuracy

    def validate(self):
        """Evaluate the model on val_loader."""
        self.model.eval()
        running_loss = 0.0
        all_preds = []
        all_labels = []
        total_samples = 0

        with torch.no_grad():
            for batch in self.val_loader:
                images = batch["image"].to(self.device)
                labels = batch["label"].to(self.device)

                outputs = self.model(images)
                loss = self.criterion(outputs, labels)

                batch_size = images.size(0)
                running_loss += loss.item() * batch_size
                total_samples += batch_size

                preds = torch.argmax(outputs, dim=1)
                all_preds.extend(preds.detach().cpu().numpy())
                all_labels.extend(labels.detach().cpu().numpy())

        epoch_loss = running_loss / total_samples
        epoch_accuracy = accuracy_score(all_labels, all_preds)

        return epoch_loss, epoch_accuracy

    def save_checkpoint(self, epoch, val_loss, val_accuracy):
        """Save model checkpoint with all required metadata."""
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "val_loss": val_loss,
            "val_accuracy": val_accuracy,
            "num_classes": self.num_classes
        }

        torch.save(checkpoint, self.checkpoint_path)

    def train(self):
        """Execute full training loop over configured epochs."""
        print("=" * 70)
        print("STARTING TRAINING")
        print("=" * 70)
        print(f"Device:               {self.device}")
        print(f"Epochs:               {self.epochs}")
        print(f"Early stop patience:  {self.early_stopping_patience}")
        print(f"Training batches:     {len(self.train_loader)}")
        print(f"Validation batches:   {len(self.val_loader)}")
        print(f"Checkpoint destination: {self.checkpoint_path}")
        print("=" * 70)

        for epoch in range(1, self.epochs + 1):
            train_loss, train_acc = self.train_one_epoch()
            val_loss, val_acc = self.validate()

            # Step scheduler based on validation loss
            self.scheduler.step(val_loss)
            current_lr = self.optimizer.param_groups[0]["lr"]

            # Record metrics
            self.history["train_loss"].append(train_loss)
            self.history["train_accuracy"].append(train_acc)
            self.history["val_loss"].append(val_loss)
            self.history["val_accuracy"].append(val_acc)

            print(
                f"Epoch [{epoch:02d}/{self.epochs:02d}] "
                f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f} | "
                f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f} | "
                f"LR: {current_lr:.7f}"
            )

            # Check for improvement (primarily validation loss)
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.best_val_accuracy = val_acc
                self.best_epoch = epoch
                self.epochs_without_improvement = 0
                self.save_checkpoint(epoch, val_loss, val_acc)
                print(f"  --> Checkpoint saved (val_loss improved to {val_loss:.4f})")
            else:
                self.epochs_without_improvement += 1
                print(f"  --> No improvement ({self.epochs_without_improvement}/{self.early_stopping_patience})")

            # Check early stopping
            if self.epochs_without_improvement >= self.early_stopping_patience:
                print(f"\nEarly stopping triggered after {epoch} epochs.")
                break

        print("\n" + "=" * 70)
        print("TRAINING FINISHED")
        print("=" * 70)
        print(f"Best Epoch:               {self.best_epoch}")
        print(f"Best Validation Loss:     {self.best_val_loss:.4f}")
        print(f"Best Validation Accuracy: {self.best_val_accuracy:.4f}")
        print(f"Best Model Checkpoint:    {self.checkpoint_path}")

        return self.history