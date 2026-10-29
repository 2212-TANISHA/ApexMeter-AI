import torch
import torch.nn as nn
import torch.nn.functional as F

# Class mapping: 10 digits + minus + decimal + blank
CLASSES = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '.', '_']
NUM_CLASSES = len(CLASSES)
CHAR_TO_IDX = {ch: idx for idx, ch in enumerate(CLASSES)}
IDX_TO_CHAR = {idx: ch for idx, ch in enumerate(CLASSES)}

class IndustrialDigitCNN(nn.Module):
    """
    Deep Convolutional Neural Network tailored for industrial digital & 7-segment display characters.
    Takes 32x32 single-channel normalized inputs and predicts 13 classes (0-9, -, ., blank).
    Features Batch Normalization and Dropout for robust generalization against sensor noise,
    glare, slant, and uneven LED/LCD illumination.
    """
    def __init__(self, num_classes: int = NUM_CLASSES):
        super().__init__()
        # Block 1: 32x32 -> 16x16
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(2, 2)

        # Block 2: 16x16 -> 8x8
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2, 2)

        # Block 3: 8x8 -> 4x4
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(2, 2)

        # Fully Connected Head
        self.dropout = nn.Dropout(0.3)
        self.fc1 = nn.Linear(128 * 4 * 4, 128)
        self.bn_fc = nn.BatchNorm1d(128)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (B, 1, 32, 32)
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))

        x = torch.flatten(x, 1)
        x = self.dropout(x)
        x = F.relu(self.bn_fc(self.fc1(x)))
        x = self.dropout(x)
        x = self.fc2(x)
        return x
