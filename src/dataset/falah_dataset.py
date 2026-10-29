import io
from pathlib import Path

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms


class FalahAlzheimerDataset(Dataset):
    """
    Falah Alzheimer MRI dataset.

    Input:
        Parquet files containing:
        - image: JPEG bytes
        - label: 0, 1, 2, 3

    This is an IMAGE-LEVEL dataset.
    It does not contain patient IDs.
    """

    CLASS_NAMES = [
        "Cognitively Normal",
        "Very Mild Dementia",
        "Mild Dementia",
        "Moderate Dementia",
    ]

    def __init__(self, parquet_path, image_size=224):
        self.parquet_path = Path(parquet_path)

        self.df = pd.read_parquet(self.parquet_path)

        required_columns = {"image", "label"}
        missing = required_columns - set(self.df.columns)

        if missing:
            raise ValueError(
                f"Missing required columns: {missing}"
            )

        self.transform = transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.Grayscale(num_output_channels=3),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
        ])

        # Verify labels
        valid_labels = {0, 1, 2, 3}

        actual_labels = set(self.df["label"].unique())

        invalid_labels = actual_labels - valid_labels

        if invalid_labels:
            raise ValueError(
                f"Invalid labels found: {invalid_labels}"
            )

    def __len__(self):
        return len(self.df)

    def __getitem__(self, index):

        row = self.df.iloc[index]

        image_data = row["image"]

        # Hugging Face Parquet stores image bytes in a dictionary
        if isinstance(image_data, dict):
            image_bytes = image_data["bytes"]
        else:
            image_bytes = image_data

        image = Image.open(
            io.BytesIO(image_bytes)
        ).convert("L")

        image = self.transform(image)

        label = int(row["label"])

        return {
            "image": image,
            "label": torch.tensor(label, dtype=torch.long),
            "index": index,
        }


def create_falah_dataloader(
    parquet_path,
    batch_size=16,
    image_size=224,
    shuffle=True,
):
    dataset = FalahAlzheimerDataset(
        parquet_path=parquet_path,
        image_size=image_size,
    )

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=0,
        pin_memory=False,
    )

    return dataset, loader