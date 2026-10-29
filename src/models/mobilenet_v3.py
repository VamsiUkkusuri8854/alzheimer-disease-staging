# ============================================================
# ALZHEIMER MRI STAGING - MOBILENETV3-LARGE ARCHITECTURE
# ============================================================

import torch.nn as nn
from torchvision.models import (
    mobilenet_v3_large,
    MobileNet_V3_Large_Weights,
)


def get_mobilenet_v3_model(
    num_classes: int = 4,
    pretrained: bool = True,
) -> nn.Module:
    """
    MobileNetV3-Large for Alzheimer's disease staging.
    Modern lightweight CNN architecture with hard-swish activations and squeeze-and-excitation blocks.

    Classes:
        0 = Cognitively Normal
        1 = Very Mild Dementia
        2 = Mild Dementia
        3 = Moderate Dementia
    """
    weights = (
        MobileNet_V3_Large_Weights.DEFAULT
        if pretrained
        else None
    )

    model = mobilenet_v3_large(weights=weights)

    input_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(input_features, num_classes)

    return model
