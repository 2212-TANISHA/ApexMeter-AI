import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader, random_split

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import WEIGHTS_DIR
from backend.models.ml.digit_cnn import IndustrialDigitCNN, NUM_CLASSES, CLASSES
from backend.models.ml.dataset_generator import SevenSegmentRenderer

def train_model(
    epochs: int = 15,
    batch_size: int = 64,
    learning_rate: float = 0.001,
    samples_per_class: int = 400,
    save_path: Path = WEIGHTS_DIR / "meter_cnn.pt"
):
    print("=" * 60)
    print("AI-Based Industrial Machine Parameter Monitoring - Model Training")
    print("Architecture: IndustrialDigitCNN (3-block Conv-BN-ReLU-Pool)")
    print(f"Target classes ({NUM_CLASSES}): {CLASSES}")
    print("=" * 60)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Training on device: {device}")

    print(f"[*] Generating synthetic 7-segment & digital display dataset ({samples_per_class} per class)...")
    start_gen = time.perf_counter()
    X_np, y_np = SevenSegmentRenderer.generate_synthetic_dataset(samples_per_class=samples_per_class, size=32)
    gen_time = time.perf_counter() - start_gen
    total_samples = len(y_np)
    print(f"[OK] Generated {total_samples} samples in {gen_time:.2f}s.")

    # Convert to PyTorch Tensors
    X_tensor = torch.from_numpy(X_np)
    y_tensor = torch.from_numpy(y_np)

    dataset = TensorDataset(X_tensor, y_tensor)
    val_size = int(total_samples * 0.20)
    train_size = total_samples - val_size

    torch.manual_seed(42)
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    model = IndustrialDigitCNN(num_classes=NUM_CLASSES).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    history = {
        "train_loss": [],
        "val_loss": [],
        "val_accuracy": [],
        "epoch_times": []
    }

    best_val_acc = 0.0
    start_train = time.perf_counter()

    for epoch in range(1, epochs + 1):
        epoch_start = time.perf_counter()
        model.train()
        running_loss = 0.0

        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)

        scheduler.step()
        epoch_train_loss = running_loss / train_size

        # Validation
        model.eval()
        val_loss = 0.0
        correct = 0

        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)

                preds = torch.argmax(outputs, dim=1)
                correct += (preds == labels).sum().item()

        epoch_val_loss = val_loss / val_size
        epoch_val_acc = (correct / val_size) * 100.0
        epoch_time = time.perf_counter() - epoch_start

        history["train_loss"].append(round(epoch_train_loss, 4))
        history["val_loss"].append(round(epoch_val_loss, 4))
        history["val_accuracy"].append(round(epoch_val_acc, 2))
        history["epoch_times"].append(round(epoch_time, 2))

        print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {epoch_train_loss:.4f} | Val Loss: {epoch_val_loss:.4f} | Val Acc: {epoch_val_acc:.2f}% | Time: {epoch_time:.2f}s")

        if epoch_val_acc > best_val_acc:
            best_val_acc = epoch_val_acc
            save_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), save_path)

    total_train_time = time.perf_counter() - start_train
    print("=" * 60)
    print(f"[OK] Training Completed in {total_train_time:.2f}s")
    print(f"[OK] Best Validation Accuracy: {best_val_acc:.2f}%")
    print(f"[OK] Saved model weights to: {save_path}")

    # Save training metadata
    metrics_path = save_path.parent / "train_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump({
            "model_name": "IndustrialDigitCNN",
            "epochs": epochs,
            "total_samples": total_samples,
            "best_validation_accuracy": round(best_val_acc, 2),
            "training_duration_seconds": round(total_train_time, 2),
            "device": str(device),
            "history": history
        }, f, indent=2)
    print(f"[OK] Saved metrics to: {metrics_path}")

if __name__ == "__main__":
    train_model()
