import cv2
import numpy as np
import base64
from typing import Optional, Dict, Tuple, List, Any

class DisplayPreprocessor:
    """Industrial image preprocessing pipeline for 7-segment / digital instrument displays."""

    @staticmethod
    def crop_roi(image: np.ndarray, roi: Optional[Dict[str, float]] = None) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        Crops an ROI from the image. If roi is None, returns the entire image.
        roi coordinates are expected in normalized values (0.0 to 1.0):
        {'x': float, 'y': float, 'width': float, 'height': float}
        """
        h, w = image.shape[:2]
        if not roi:
            return image.copy(), (0, 0, w, h)

        rx = int(max(0, min(1.0, roi.get('x', 0.0))) * w)
        ry = int(max(0, min(1.0, roi.get('y', 0.0))) * h)
        rw = int(max(0.01, min(1.0 - roi.get('x', 0.0), roi.get('width', 1.0))) * w)
        rh = int(max(0.01, min(1.0 - roi.get('y', 0.0), roi.get('height', 1.0))) * h)

        # Ensure valid dimensions
        rw = max(10, min(rw, w - rx))
        rh = max(10, min(rh, h - ry))

        crop = image[ry:ry + rh, rx:rx + rw]
        return crop, (rx, ry, rw, rh)

    @staticmethod
    def enhance_and_binarize(crop: np.ndarray) -> Tuple[np.ndarray, np.ndarray, bool]:
        """
        Enhances contrast, filters noise, and produces a normalized binary image
        where digits are WHITE on BLACK background (suitable for contour analysis and CNN).
        Returns:
            gray: Enhanced grayscale image
            binary: Binary image with foreground digits in 255 (white)
            is_inverted: True if original had dark digits on light background
        """
        if len(crop.shape) == 3:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = crop.copy()

        # CLAHE for handling uneven industrial lighting and glass reflection
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Bilateral filter reduces noise while keeping crisp digit segment boundaries
        filtered = cv2.bilateralFilter(enhanced, d=5, sigmaColor=50, sigmaSpace=50)

        # Otsu thresholding
        _, otsu = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Detect whether background is white or black.
        # We sample the border pixels (top, bottom, left, right edges)
        border_pixels = np.concatenate([
            otsu[0, :], otsu[-1, :], otsu[:, 0], otsu[:, -1]
        ])
        white_border_ratio = np.mean(border_pixels == 255)

        is_dark_on_light = white_border_ratio > 0.5
        if is_dark_on_light:
            # LCD meter (dark digits on light green/gray background): invert so digits are white
            binary = cv2.bitwise_not(otsu)
        else:
            # LED meter (red/green glowing digits on black background)
            binary = otsu

        # Small morphological closing to bridge slight segment gaps if any
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return gray, binary, is_dark_on_light

    @staticmethod
    def segment_display_elements(binary: np.ndarray, min_aspect: float = 0.1, max_aspect: float = 3.5) -> List[Dict[str, Any]]:
        """
        Finds candidate characters and decimal points from the binary meter display.
        Returns sorted list of bounding boxes from left to right.
        """
        h_img, w_img = binary.shape[:2]
        contours, hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < (h_img * w_img * 0.0004):  # ignore microscopic noise
                continue

            x, y, w, h = cv2.boundingRect(cnt)

            # Ignore contours that encompass almost the entire frame (bezel or border frame)
            if w > (w_img * 0.88) and h > (h_img * 0.88):
                continue

            # Check if this might be a decimal point
            # Decimal points are compact and located in the bottom 45% of the display height
            is_near_bottom = (y + h) > (h_img * 0.58)
            is_small = (h <= h_img * 0.25) and (w <= w_img * 0.18)
            aspect = w / float(h) if h > 0 else 0

            is_decimal_candidate = is_near_bottom and is_small and (0.35 <= aspect <= 2.2)

            # Check if this might be a digit (height at least 25% of display height)
            is_digit_candidate = (h >= h_img * 0.25) and (h <= h_img * 0.95) and (0.10 <= aspect <= 1.6)

            # Check if this might be a minus sign (thin, wide, mid-height)
            is_minus_candidate = (w > h * 1.4) and (h < h_img * 0.30) and (y > h_img * 0.2) and (y < h_img * 0.8)

            if is_decimal_candidate or is_digit_candidate or is_minus_candidate:
                element_type = "decimal" if is_decimal_candidate else ("minus" if is_minus_candidate else "digit")
                candidates.append({
                    "bbox": (x, y, w, h),
                    "area": area,
                    "type": element_type,
                    "center_x": x + w / 2.0,
                    "center_y": y + h / 2.0
                })

        # Sort candidate boxes from left to right
        candidates.sort(key=lambda item: item["center_x"])

        # Filter overlapping boxes (e.g. if a decimal point was caught inside a digit contour)
        filtered = []
        for cand in candidates:
            cx, cy, cw, ch = cand["bbox"]
            overlap = False
            for existing in filtered:
                ex, ey, ew, eh = existing["bbox"]
                # If cand is significantly contained within existing, skip
                if cx >= ex and (cx + cw) <= (ex + ew) and cy >= ey and (cy + ch) <= (ey + eh):
                    overlap = True
                    break
            if not overlap:
                filtered.append(cand)

        return filtered

    @staticmethod
    def prepare_patch_for_cnn(binary: np.ndarray, bbox: Tuple[int, int, int, int], target_size: int = 32) -> np.ndarray:
        """
        Extracts digit patch from binary image, squares it with uniform padding,
        and resizes to target_size x target_size normalized to [0, 1].
        """
        x, y, w, h = bbox
        patch = binary[y:y + h, x:x + w]

        # Pad to square to preserve aspect ratio
        max_dim = max(w, h)
        # Add 15% margin
        margin = int(max_dim * 0.15)
        square_dim = max_dim + 2 * margin

        square = np.zeros((square_dim, square_dim), dtype=np.uint8)
        offset_x = margin + (max_dim - w) // 2
        offset_y = margin + (max_dim - h) // 2

        square[offset_y:offset_y + h, offset_x:offset_x + w] = patch

        # Resize to CNN input size (32x32)
        resized = cv2.resize(square, (target_size, target_size), interpolation=cv2.INTER_AREA)

        # Normalize to float32 [0.0, 1.0]
        normalized = resized.astype(np.float32) / 255.0
        return normalized

    @staticmethod
    def encode_image_base64(image: np.ndarray) -> str:
        """Encodes an OpenCV image to base64 JPEG string."""
        success, encoded = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not success:
            return ""
        return base64.b64encode(encoded.tobytes()).decode('utf-8')
