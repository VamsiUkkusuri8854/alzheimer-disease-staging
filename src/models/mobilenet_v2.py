# ============================================================
# ALZHEIMER MRI STAGING - MOBILENET (V2) ARCHITECTURE
# ============================================================

import torch.nn as nn
from torchvision.models import (
    mobilenet_v2,
    MobileNet_V2_Weights,
)


def get_mobilenet_v2_model(
    num_classes: int = 4,
    pretrained: bool = True,
) -> nn.Module:
    """
    MobileNet (V2) for Alzheimer's disease staging.
    Lightweight convolutional neural network with inverted residual blocks.

    Classes:
        0 = Cognitively Normal
        1 = Very Mild Dementia
        2 = Mild Dementia
        3 = Moderate Dementia
    """
    weights = (
        MobileNet_V2_Weights.DEFAULT
        if pretrained
        else None
    )

    model = mobilenet_v2(weights=weights)
    
    # Replace final linear layer in classifier
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)

    return model
