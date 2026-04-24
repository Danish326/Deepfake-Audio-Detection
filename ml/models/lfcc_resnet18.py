"""
ml/models/lfcc_resnet18.py

LFCCResNet18 architecture — ported verbatim from the training notebook
(Audio Deepfake Detection - FYP PHASE 1 Completed.ipynb, Cell 13).

DO NOT modify this class. Any change breaks weight loading from .pth files.
"""
import torch
import torch.nn as nn
from torchvision.models import resnet18


class LFCCResNet18(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.model = resnet18(weights=None)

        # Change input layer from 3 channels to 1
        self.model.conv1 = nn.Conv2d(
            1, 64, kernel_size=7, stride=2, padding=3, bias=False
        )

        # Add dropout to reduce overfitting
        self.dropout = nn.Dropout(0.3)

        # Adjust final FC layer
        self.model.fc = nn.Linear(512, num_classes)

    def forward(self, x):
        x = self.model.conv1(x)
        x = self.model.bn1(x)
        x = self.model.relu(x)
        x = self.model.maxpool(x)

        x = self.model.layer1(x)
        x = self.model.layer2(x)
        x = self.model.layer3(x)
        x = self.model.layer4(x)

        x = self.model.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.dropout(x)
        x = self.model.fc(x)

        return x
