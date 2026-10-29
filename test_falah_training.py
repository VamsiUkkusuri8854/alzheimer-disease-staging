import sys
sys.path.insert(0, "src")

import torch
import torch.nn as nn
import torch.optim as optim

from dataset.falah_dataset import create_falah_dataloader
from models.mobilenet import get_mobilenet_v3_model


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PARQUET_PATH = (
    "data/raw/Falah_Alzheimer_MRI/data/"
    "train-00000-of-00001-c08a401c53fe5312.parquet"
)

BATCH_SIZE = 16
TEST_BATCHES = 10

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Device:", DEVICE)


# --------------------------------------------------
# Dataset
# --------------------------------------------------

dataset, loader = create_falah_dataloader(
    parquet_path=PARQUET_PATH,
    batch_size=BATCH_SIZE,
    shuffle=True,
)

print("Total samples:", len(dataset))


# --------------------------------------------------
# Model
# --------------------------------------------------

model = get_mobilenet_v3_model(
    num_classes=4,
    pretrained=True,
)

model = model.to(DEVICE)

criterion = nn.CrossEntropyLoss()

optimizer = optim.Adam(
    model.parameters(),
    lr=1e-4,
)


# --------------------------------------------------
# Small training sanity check
# --------------------------------------------------

model.train()

running_loss = 0.0
correct = 0
total = 0

for batch_index, batch in enumerate(loader):

    if batch_index >= TEST_BATCHES:
        break

    images = batch["image"].to(DEVICE)
    labels = batch["label"].to(DEVICE)

    optimizer.zero_grad()

    outputs = model(images)

    loss = criterion(
        outputs,
        labels,
    )

    loss.backward()

    optimizer.step()

    running_loss += loss.item()

    predictions = outputs.argmax(dim=1)

    correct += (
        predictions == labels
    ).sum().item()

    total += labels.size(0)

    print(
        f"Batch {batch_index + 1}/{TEST_BATCHES} "
        f"| Loss: {loss.item():.4f}"
    )


# --------------------------------------------------
# Results
# --------------------------------------------------

accuracy = 100.0 * correct / total

print()
print("=" * 50)
print("FALAH TRAINING SANITY TEST")
print("=" * 50)
print(f"Batches tested : {TEST_BATCHES}")
print(f"Samples tested : {total}")
print(f"Average loss   : {running_loss / TEST_BATCHES:.4f}")
print(f"Accuracy       : {accuracy:.2f}%")
print("=" * 50)