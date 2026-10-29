import cv2
import numpy as np
import random
from typing import Tuple, List, Optional
from backend.models.ml.digit_cnn import CLASSES, CHAR_TO_IDX

# Standard 7-segment active segment definitions
# Segments: A (top), B (top-right), C (bot-right), D (bot), E (bot-left), F (top-left), G (mid)
SEGMENT_MAP = {
    '0': ['A', 'B', 'C', 'D', 'E', 'F'],
    '1': ['B', 'C'],
    '2': ['A', 'B', 'G', 'E', 'D'],
    '3': ['A', 'B', 'G', 'C', 'D'],
    '4': ['F', 'G', 'B', 'C'],
    '5': ['A', 'F', 'G', 'C', 'D'],
    '6': ['A', 'F', 'E', 'D', 'C', 'G'],
    '7': ['A', 'B', 'C'],
    '8': ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
    '9': ['A', 'B', 'C', 'D', 'F', 'G'],
    '-': ['G'],
    '.': ['DP'],
    '_': []
}

class SevenSegmentRenderer:
    """Renders realistic 7-segment LCD / LED digits and full displays with industrial augmentations."""

    @staticmethod
    def draw_digit_patch(
        char: str,
        size: int = 32,
        slant_deg: float = 8.0,
        thickness: int = 2,
        noise_level: float = 0.05
    ) -> np.ndarray:
        """
        Renders a single 32x32 character patch (white foreground on black background)
        with segment gaps, shear, and augmentations for CNN training.
        """
        img_h, img_w = 64, 48
        canvas = np.zeros((img_h, img_w), dtype=np.uint8)

        active = SEGMENT_MAP.get(char, [])

        # Dimensions inside canvas
        pad_x = 8
        pad_y = 6
        w = img_w - 2 * pad_x
        h = img_h - 2 * pad_y
        mid_y = pad_y + h // 2
        bot_y = pad_y + h

        t = max(1, thickness)
        gap = 2

        # Draw active segments
        if 'A' in active:
            cv2.line(canvas, (pad_x + gap, pad_y), (pad_x + w - gap, pad_y), 255, t)
        if 'B' in active:
            cv2.line(canvas, (pad_x + w, pad_y + gap), (pad_x + w, mid_y - gap), 255, t)
        if 'C' in active:
            cv2.line(canvas, (pad_x + w, mid_y + gap), (pad_x + w, bot_y - gap), 255, t)
        if 'D' in active:
            cv2.line(canvas, (pad_x + gap, bot_y), (pad_x + w - gap, bot_y), 255, t)
        if 'E' in active:
            cv2.line(canvas, (pad_x, mid_y + gap), (pad_x, bot_y - gap), 255, t)
        if 'F' in active:
            cv2.line(canvas, (pad_x, pad_y + gap), (pad_x, mid_y - gap), 255, t)
        if 'G' in active:
            cv2.line(canvas, (pad_x + gap, mid_y), (pad_x + w - gap, mid_y), 255, t)
        if 'DP' in active:
            cv2.circle(canvas, (img_w - pad_x, bot_y), max(2, t), 255, -1)

        # Apply slant / affine shear
        if abs(slant_deg) > 0.1:
            rad = np.radians(slant_deg)
            shear_matrix = np.array([
                [1.0, -np.tan(rad), float(img_h * np.tan(rad) * 0.5)],
                [0.0, 1.0, 0.0]
            ], dtype=np.float32)
            canvas = cv2.warpAffine(canvas, shear_matrix, (img_w, img_h), borderMode=cv2.BORDER_CONSTANT, borderValue=0)

        # Center and pad into square using exact bounding box
        coords = cv2.findNonZero(canvas)
        if coords is not None and len(coords) > 0:
            bx, by, bw, bh = cv2.boundingRect(coords)
            max_dim = max(bw, bh)
            margin = int(max_dim * 0.15)
            square_dim = max_dim + 2 * margin
            square = np.zeros((square_dim, square_dim), dtype=np.uint8)
            off_x = margin + (max_dim - bw) // 2
            off_y = margin + (max_dim - bh) // 2
            square[off_y:off_y + bh, off_x:off_x + bw] = canvas[by:by + bh, bx:bx + bw]
            resized = cv2.resize(square, (size, size), interpolation=cv2.INTER_AREA)
        else:
            # Blank / empty character
            resized = np.zeros((size, size), dtype=np.uint8)

        # Add Gaussian noise and blur variations
        if noise_level > 0:
            noise = np.random.normal(0, noise_level * 255, (size, size)).astype(np.float32)
            noisy = np.clip(resized.astype(np.float32) + noise, 0, 255).astype(np.uint8)
            if random.random() > 0.5:
                noisy = cv2.GaussianBlur(noisy, (3, 3), 0.5)
            resized = noisy

        return resized

    @classmethod
    def generate_synthetic_dataset(
        cls,
        samples_per_class: int = 400,
        size: int = 32
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates synthetic training dataset of 32x32 patches for all CLASSES.
        Returns:
            X: np.ndarray shape (N, 1, 32, 32) normalized float32 [0.0, 1.0]
            y: np.ndarray shape (N,) int64 class indices
        """
        X_list = []
        y_list = []

        for char in CLASSES:
            class_idx = CHAR_TO_IDX[char]
            for _ in range(samples_per_class):
                slant = random.uniform(3.0, 14.0)
                thick = random.choice([2, 3, 4])
                noise = random.uniform(0.01, 0.08)
                patch = cls.draw_digit_patch(char, size=size, slant_deg=slant, thickness=thick, noise_level=noise)

                # Random morphological jitter
                if random.random() > 0.7:
                    k = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                    if random.random() > 0.5:
                        patch = cv2.dilate(patch, k, iterations=1)
                    else:
                        patch = cv2.erode(patch, k, iterations=1)

                norm_patch = patch.astype(np.float32) / 255.0
                X_list.append(norm_patch)
                y_list.append(class_idx)

        X = np.expand_dims(np.array(X_list, dtype=np.float32), axis=1)  # (N, 1, 32, 32)
        y = np.array(y_list, dtype=np.int64)

        # Shuffle
        indices = np.arange(len(y))
        np.random.shuffle(indices)
        return X[indices], y[indices]

    @classmethod
    def render_full_meter_display(
        cls,
        text_value: str,
        display_type: str = "led_red",
        width: int = 360,
        height: int = 140,
        add_meter_frame: bool = True
    ) -> np.ndarray:
        """
        Renders a realistic industrial digital instrument face with bezel, unit label,
        and glowing 7-segment digital characters.
        """
        meter = np.zeros((height, width, 3), dtype=np.uint8)

        # Background style
        if display_type == "led_red":
            bg_color = (20, 20, 20)       # dark bezel
            screen_bg = (10, 10, 15)      # dark glass
            fg_color = (40, 40, 255)      # Bright Red (BGR)
            glow_color = (15, 15, 120)    # subtle glow
        elif display_type == "led_green":
            bg_color = (25, 25, 25)
            screen_bg = (12, 18, 12)
            fg_color = (50, 240, 60)      # Bright Green (BGR)
            glow_color = (15, 90, 20)
        else:  # lcd_green
            bg_color = (40, 40, 40)
            screen_bg = (130, 160, 120)   # greenish LCD backlight
            fg_color = (25, 30, 25)       # dark LCD segments
            glow_color = (110, 140, 100)

        meter[:] = bg_color

        if add_meter_frame:
            # Display bezel border
            pad_x, pad_y = 20, 20
            win_w = width - 2 * pad_x
            win_h = height - 2 * pad_y
            cv2.rectangle(meter, (pad_x, pad_y), (pad_x + win_w, pad_y + win_h), screen_bg, -1)
            cv2.rectangle(meter, (pad_x, pad_y), (pad_x + win_w, pad_y + win_h), (50, 50, 50), 2)
        else:
            pad_x, pad_y = 6, 6
            win_w = width - 2 * pad_x
            win_h = height - 2 * pad_y
            meter[:] = screen_bg

        # Render each character in text_value
        num_chars = len(text_value)
        if num_chars == 0:
            return meter

        # Character dimensions
        char_w = int(win_w / max(num_chars + 1, 5))
        char_h = int(win_h * 0.72)
        start_x = pad_x + int((win_w - (num_chars * char_w)) / 2)
        start_y = pad_y + int((win_h - char_h) / 2)

        for i, ch in enumerate(text_value):
            cx = start_x + i * char_w
            cy = start_y

            # Generate segment binary mask for character
            if ch == '.':
                # Render decimal point
                dot_r = max(3, int(char_w * 0.12))
                dot_center = (cx + int(char_w * 0.3), cy + char_h - 4)
                cv2.circle(meter, dot_center, dot_r, fg_color, -1)
            else:
                patch = cls.draw_digit_patch(ch, size=char_h, slant_deg=8.0, thickness=4, noise_level=0.0)
                # Resize patch to (char_w, char_h)
                patch_res = cv2.resize(patch, (char_w, char_h), interpolation=cv2.INTER_AREA)

                # Blend into screen
                mask = patch_res > 100
                roi = meter[cy:cy + char_h, cx:cx + char_w]
                if roi.shape[:2] == mask.shape:
                    roi[mask] = fg_color

        # Add industrial reflections and subtle gradient
        if add_meter_frame:
            # Reflection slash
            pts = np.array([
                [pad_x, pad_y + int(win_h * 0.6)],
                [pad_x + int(win_w * 0.5), pad_y],
                [pad_x + int(win_w * 0.7), pad_y],
                [pad_x, pad_y + win_h]
            ], np.int32)
            cv2.fillPoly(meter, [pts], (min(255, screen_bg[0] + 15), min(255, screen_bg[1] + 15), min(255, screen_bg[2] + 15)))

        return meter
