# ============================================================
# ALZHEIMER MRI STAGING
# TRAINING CONFIGURATION
# ============================================================

from pathlib import Path
import torch


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"
FOLDS_DIR = METADATA_DIR / "folds"
OASIS_METADATA_FILE = METADATA_DIR / "oasis_metadata.csv"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"

OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
METRICS_DIR = OUTPUT_DIR / "metrics"
PREDICTIONS_DIR = OUTPUT_DIR / "predictions"


# ============================================================
# DATASET / CLASSES (4-CLASS TARGET ARCHITECTURE)
# ============================================================

NUM_CLASSES = 4

CLASS_NAMES = [
    "Cognitively Normal",
    "Very Mild Dementia",
    "Mild Dementia",
    "Moderate Dementia"
]

CDR_TO_CLASS = {
    0.0: 0,  # Cognitively Normal
    0.5: 1,  # Very Mild Dementia
    1.0: 2,  # Mild Dementia
    2.0: 3,  # Moderate Dementia
}


# ============================================================
# IMAGE
# ============================================================

IMAGE_SIZE = 224
IMAGE_CHANNELS = 3


# ============================================================
# MODEL
# ============================================================

MODEL_NAME = "MobileNetV3-Large"
PRETRAINED = True


# ============================================================
# TRAINING HYPERPARAMETERS
# ============================================================

BATCH_SIZE = 16
EPOCHS = 10
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4

OPTIMIZER = "Adam"

SCHEDULER = "ReduceLROnPlateau"
SCHEDULER_FACTOR = 0.5
SCHEDULER_PATIENCE = 2
MIN_LR = 1e-7

EARLY_STOPPING_PATIENCE = 4


# ============================================================
# CROSS VALIDATION
# ============================================================

N_FOLDS = 5
RANDOM_STATE = 42


# ============================================================
# DATA LOADING
# ============================================================

NUM_WORKERS = 0
PIN_MEMORY = False


# ============================================================
# DEVICE
# ============================================================

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# ============================================================
# CHECKPOINT
# ============================================================

# Existing working 3-class checkpoint (kept intact)
BEST_MODEL_NAME = "fold_1_best_model.pth"

# Target checkpoint for 4-class model when real CDR=2.0 data becomes available
BEST_MODEL_4CLASS_NAME = "mobilenetv3_falah_best.pth"


# ============================================================
# CREATE REQUIRED DIRECTORIES
# ============================================================

def create_directories():
    """Create all required project directories if they do not exist."""
    directories = [
        METADATA_DIR,
        FOLDS_DIR,
        PROCESSED_DIR,
        RAW_DIR,
        CHECKPOINT_DIR,
        OUTPUT_DIR,
        FIGURES_DIR,
        METRICS_DIR,
        PREDICTIONS_DIR
    ]

    for directory in directories:
        directory.mkdir(
            parents=True,
            exist_ok=True
        )


# ============================================================
# PRINT CONFIGURATION
# ============================================================

def print_config():
    """Print project configuration summary."""
    print("=" * 60)
    print("ALZHEIMER MRI STAGING CONFIGURATION")
    print("=" * 60)

    print("\nDataset")
    print("-" * 60)
    print("Number of classes:", NUM_CLASSES)
    print("Classes:")
    for index, name in enumerate(CLASS_NAMES):
        print(f"  {index}: {name}")

    print("\nModel")
    print("-" * 60)
    print("Model:", MODEL_NAME)
    print("Pretrained:", PRETRAINED)
    print("Image size:", IMAGE_SIZE)
    print("Channels:", IMAGE_CHANNELS)

    print("\nTraining")
    print("-" * 60)
    print("Batch size:", BATCH_SIZE)
    print("Epochs:", EPOCHS)
    print("Learning rate:", LEARNING_RATE)
    print("Weight decay:", WEIGHT_DECAY)
    print("Early stopping patience:", EARLY_STOPPING_PATIENCE)

    print("\nCross Validation")
    print("-" * 60)
    print("Number of folds:", N_FOLDS)
    print("Random state:", RANDOM_STATE)

    print("\nDevice")
    print("-" * 60)
    print("Device:", DEVICE)
    print("CUDA available:", torch.cuda.is_available())

    print("\nConfiguration loaded successfully.")


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    create_directories()
    print_config()