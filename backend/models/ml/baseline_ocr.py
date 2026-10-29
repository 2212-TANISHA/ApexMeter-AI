import time
import cv2
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from backend.models.ml.base import BaseDigitRecognizer, RecognitionResult
from backend.models.ml.preprocessor import DisplayPreprocessor

# Truth table mapping bit pattern (A, B, C, D, E, F, G) to character
# 1 means segment is lit, 0 means unlit
BASELINE_7SEG_TABLE = {
    (1, 1, 1, 1, 1, 1, 0): '0',
    (0, 1, 1, 0, 0, 0, 0): '1',
    (1, 1, 0, 1, 1, 0, 1): '2',
    (1, 1, 1, 1, 0, 0, 1): '3',
    (0, 1, 1, 0, 0, 1, 1): '4',
    (1, 0, 1, 1, 0, 1, 1): '5',
    (1, 0, 1, 1, 1, 1, 1): '6',
    (1, 1, 1, 0, 0, 0, 0): '7',
    (1, 1, 1, 1, 1, 1, 1): '8',
    (1, 1, 1, 1, 0, 1, 1): '9',
    (0, 0, 0, 0, 0, 0, 1): '-',
    (0, 0, 0, 0, 0, 0, 0): '_'
}

class BaselineOcrRecognizer(BaseDigitRecognizer):
    """
    Conventional OCR baseline recognizer using segment occupancy ratio analysis.
    Serves as the classical benchmark against which the Deep Learning CNN model is compared.
    """
    def __init__(self, segment_threshold: float = 0.35):
        self.segment_threshold = segment_threshold

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": "Conventional 7-Segment Topological OCR",
            "type": "Classical Computer Vision (Non-DL)",
            "technique": "Otsu thresholding + 7-segment occupancy zone projection",
            "trainable_parameters": 0
        }

    def _classify_digit_patch(self, patch: np.ndarray) -> Tuple[str, float]:
        """
        Samples the 7 zones (A..G) of the digit patch and computes Hamming similarity
        to known segment templates.
        """
        h, w = patch.shape[:2]
        if h < 6 or w < 3:
            return '_', 0.0

        # Define 7 sampling regions (relative coords: y1, y2, x1, x2)
        # Segments:
        # A: top horizontal (y: 0 to 0.2, x: 0.2 to 0.8)
        # B: top-right vertical (y: 0.15 to 0.45, x: 0.7 to 1.0)
        # C: bot-right vertical (y: 0.55 to 0.85, x: 0.7 to 1.0)
        # D: bot horizontal (y: 0.8 to 1.0, x: 0.2 to 0.8)
        # E: bot-left vertical (y: 0.55 to 0.85, x: 0.0 to 0.3)
        # F: top-left vertical (y: 0.15 to 0.45, x: 0.0 to 0.3)
        # G: middle horizontal (y: 0.4 to 0.6, x: 0.2 to 0.8)

        def get_density(y1_r, y2_r, x1_r, x2_r):
            y1, y2 = int(y1_r * h), max(int(y1_r * h) + 1, int(y2_r * h))
            x1, x2 = int(x1_r * w), max(int(x1_r * w) + 1, int(x2_r * w))
            sub = patch[y1:y2, x1:x2]
            if sub.size == 0:
                return 0.0
            return float(np.mean(sub > 127))

        densities = [
            get_density(0.00, 0.22, 0.20, 0.80),  # A
            get_density(0.15, 0.45, 0.65, 1.00),  # B
            get_density(0.55, 0.85, 0.65, 1.00),  # C
            get_density(0.78, 1.00, 0.20, 0.80),  # D
            get_density(0.55, 0.85, 0.00, 0.35),  # E
            get_density(0.15, 0.45, 0.00, 0.35),  # F
            get_density(0.40, 0.60, 0.20, 0.80)   # G
        ]

        observed_bits = tuple(1 if d >= self.segment_threshold else 0 for d in densities)

        # Find best matching character by minimum bit difference
        best_char = '_'
        best_diff = 8
        best_conf = 0.0

        for pattern, char in BASELINE_7SEG_TABLE.items():
            diff = sum(b1 != b2 for b1, b2 in zip(pattern, observed_bits))
            if diff < best_diff:
                best_diff = diff
                best_char = char
                # Confidence proportional to pattern match (7 - diff) / 7.0
                best_conf = max(0.0, (7.0 - diff) / 7.0)

        # Penalize if observed pattern has ambiguous bits near threshold
        margin = np.mean(np.abs(np.array(densities) - self.segment_threshold))
        final_conf = min(1.0, best_conf * (0.6 + 0.4 * margin))
        return best_char, float(final_conf)

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
                model_name="baseline_ocr",
                warning_or_error="No display segment contours detected."
            )

        chars_found: List[Tuple[str, float]] = []
        annotated = crop.copy()
        segmented_rois = []

        for cand in candidates:
            bx, by, bw, bh = cand["bbox"]
            cand_type = cand["type"]

            if cand_type == "decimal":
                chars_found.append(('.', 0.90))
                segmented_rois.append({"bbox": (bx, by, bw, bh), "char": ".", "conf": 0.90})
                cv2.rectangle(annotated, (bx, by), (bx + bw, by + bh), (255, 128, 0), 1)
            else:
                patch = binary[by:by + bh, bx:bx + bw]
                char, conf = self._classify_digit_patch(patch)
                if char != '_':
                    chars_found.append((char, conf))
                    segmented_rois.append({"bbox": (bx, by, bw, bh), "char": char, "conf": conf})
                    cv2.rectangle(annotated, (bx, by), (bx + bw, by + bh), (0, 165, 255), 1)
                    cv2.putText(annotated, char, (bx, max(12, by - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)

        raw_text = "".join(c[0] for c in chars_found)
        avg_conf = float(np.mean([c[1] for c in chars_found])) if chars_found else 0.0

        # Parse numerical value
        try:
            num_val = float(raw_text)
            status = "VALID" if avg_conf >= 0.60 else "UNCERTAIN"
        except (ValueError, TypeError):
            num_val = None
            status = "INVALID"

        elapsed = (time.perf_counter() - start_t) * 1000.0

        return RecognitionResult(
            raw_text=raw_text,
            numerical_value=num_val,
            confidence=round(avg_conf, 3),
            char_confidences=chars_found,
            status=status,
            inference_time_ms=round(elapsed, 2),
            model_name="baseline_ocr",
            segmented_rois=segmented_rois,
            annotated_image_base64=DisplayPreprocessor.encode_image_base64(annotated)
        )
