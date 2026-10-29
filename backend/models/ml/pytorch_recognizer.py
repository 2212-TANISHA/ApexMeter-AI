import time
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import cv2
import numpy as np
import torch
import torch.nn.functional as F

from backend.models.ml.base import BaseDigitRecognizer, RecognitionResult
from backend.models.ml.digit_cnn import IndustrialDigitCNN, CLASSES, IDX_TO_CHAR, NUM_CLASSES
from backend.models.ml.preprocessor import DisplayPreprocessor
from backend.config import WEIGHTS_DIR

DEFAULT_WEIGHTS_PATH = WEIGHTS_DIR / "meter_cnn.pt"

class PyTorchDigitRecognizer(BaseDigitRecognizer):
    """
    Industrial Digital Meter Deep Learning Recognizer.
    Utilizes an optimized PyTorch CNN with batch normalization and dropout
    to classify individual 7-segment display digits, minus signs, and decimal points.
    """
    def __init__(self, weights_path: Optional[str] = None, device: str = "cpu"):
        self.device = torch.device(device)
        self.model = IndustrialDigitCNN(num_classes=NUM_CLASSES).to(self.device)
        self.weights_path = Path(weights_path) if weights_path else DEFAULT_WEIGHTS_PATH
        self.is_loaded = False
        self._load_or_init_weights()

    def _load_or_init_weights(self):
        """Loads trained model weights if present, or initializes randomly."""
        if self.weights_path.exists():
            try:
                state_dict = torch.load(self.weights_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                self.model.eval()
                self.is_loaded = True
            except Exception as e:
                print(f"[PyTorchRecognizer] Warning: Failed loading weights ({e}), using initialized model.")
                self.model.eval()
        else:
            print(f"[PyTorchRecognizer] Notice: Weights file {self.weights_path} not found. Model running in initialized mode.")
            self.model.eval()

    def get_model_info(self) -> Dict[str, Any]:
        param_count = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        return {
            "name": "IndustrialMeter Deep CNN (PyTorch)",
            "type": "Deep Convolutional Neural Network",
            "backbone": "3-Block Conv-BN-ReLU-Pool + Dropout + FC",
            "input_resolution": "32x32 grayscale",
            "classes": CLASSES,
            "trainable_parameters": param_count,
            "device": str(self.device),
            "weights_loaded": self.is_loaded,
            "weights_path": str(self.weights_path)
        }

    def predict_display(
        self,
        image: np.ndarray,
        roi: Optional[Dict[str, float]] = None
    ) -> RecognitionResult:
        start_t = time.perf_counter()

        crop, (rx, ry, rw, rh) = DisplayPreprocessor.crop_roi(image, roi)
        gray, binary, is_inverted = DisplayPreprocessor.enhance_and_binarize(crop)
        candidates = DisplayPreprocessor.segment_display_elements(binary)

        if not candidates:
            elapsed = (time.perf_counter() - start_t) * 1000.0
            return RecognitionResult(
                raw_text="",
                numerical_value=None,
                confidence=0.0,
                status="INVALID",
                inference_time_ms=elapsed,
                model_name="pytorch_cnn",
                warning_or_error="No display elements detected in selected ROI."
            )

        # Process candidate characters
        recognized_items = []
        digit_patches = []
        digit_candidates = []

        for cand in candidates:
            bx, by, bw, bh = cand["bbox"]
            cand_type = cand["type"]

            if cand_type == "decimal":
                # High-confidence geometric decimal detection
                recognized_items.append({
                    "center_x": cand["center_x"],
                    "char": ".",
                    "conf": 0.95,
                    "bbox": (bx, by, bw, bh)
                })
            else:
                patch = DisplayPreprocessor.prepare_patch_for_cnn(binary, (bx, by, bw, bh), target_size=32)
                digit_patches.append(patch)
                digit_candidates.append(cand)

        # Batch CNN inference for candidate digits
        if digit_patches:
            batch_np = np.expand_dims(np.array(digit_patches, dtype=np.float32), axis=1)  # (B, 1, 32, 32)
            batch_tensor = torch.from_numpy(batch_np).to(self.device)

            with torch.no_grad():
                logits = self.model(batch_tensor)
                probs = F.softmax(logits, dim=1).cpu().numpy()

            pred_indices = np.argmax(probs, axis=1)
            pred_confs = np.max(probs, axis=1)

            for cand, class_idx, conf in zip(digit_candidates, pred_indices, pred_confs):
                pred_char = IDX_TO_CHAR[class_idx]
                bx, by, bw, bh = cand["bbox"]

                # If blank or confidence is extremely low, ignore noise
                if pred_char != '_' and conf > 0.20:
                    recognized_items.append({
                        "center_x": cand["center_x"],
                        "char": pred_char,
                        "conf": float(conf),
                        "bbox": (bx, by, bw, bh)
                    })

        # Sort items left-to-right
        recognized_items.sort(key=lambda item: item["center_x"])

        segmented_rois = []
        char_confidences = []
        annotated = crop.copy()

        for item in recognized_items:
            bx, by, bw, bh = item["bbox"]
            ch = item["char"]
            cf = item["conf"]
            char_confidences.append((ch, round(cf, 3)))
            segmented_rois.append({"bbox": (bx, by, bw, bh), "char": ch, "conf": round(cf, 3)})

            color = (0, 220, 100) if cf >= 0.70 else (0, 165, 255)
            cv2.rectangle(annotated, (bx, by), (bx + bw, by + bh), color, 1)
            cv2.putText(annotated, f"{ch}", (bx, max(12, by - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

        raw_text = "".join(item["char"] for item in recognized_items)
        confs = [item["conf"] for item in recognized_items]
        avg_conf = float(np.mean(confs)) if confs else 0.0

        # Validate numerical reading
        try:
            num_val = float(raw_text)
            status = "VALID" if avg_conf >= 0.55 else "UNCERTAIN"
        except (ValueError, TypeError):
            num_val = None
            status = "INVALID"

        elapsed = (time.perf_counter() - start_t) * 1000.0

        return RecognitionResult(
            raw_text=raw_text,
            numerical_value=num_val,
            confidence=round(avg_conf, 3),
            char_confidences=char_confidences,
            status=status,
            inference_time_ms=round(elapsed, 2),
            model_name="pytorch_cnn",
            segmented_rois=segmented_rois,
            annotated_image_base64=DisplayPreprocessor.encode_image_base64(annotated)
        )
