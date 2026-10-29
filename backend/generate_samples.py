import os
import sys
from pathlib import Path
import numpy as np
import cv2

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import SAMPLES_DIR
from backend.models.ml.dataset_generator import SevenSegmentRenderer

def generate_sample_videos_and_images():
    print(f"[*] Generating sample industrial meter assets in {SAMPLES_DIR}...")

    # 1. Red LED Meter Image (Normal pressure)
    img_red = SevenSegmentRenderer.render_full_meter_display("48.5", display_type="led_red", add_meter_frame=True)
    red_path = SAMPLES_DIR / "sample_meter_led_red_48_5.jpg"
    cv2.imwrite(str(red_path), img_red)
    print(f"[OK] Created {red_path.name}")

    # 2. Green LCD Meter Image (Warning temperature)
    img_lcd = SevenSegmentRenderer.render_full_meter_display("82.0", display_type="lcd_green", add_meter_frame=True)
    lcd_path = SAMPLES_DIR / "sample_meter_lcd_green_82_0.jpg"
    cv2.imwrite(str(lcd_path), img_lcd)
    print(f"[OK] Created {lcd_path.name}")

    # 3. 15-second Normal Boiler Pressure Video (MP4)
    norm_vid_path = SAMPLES_DIR / "boiler_pressure_normal_15s.mp4"
    fps = 10
    total_frames = 15 * fps
    width, height = 480, 240
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_norm = cv2.VideoWriter(str(norm_vid_path), fourcc, fps, (width, height))

    for i in range(total_frames):
        t = i / fps
        val = 45.0 + np.sin(t * 0.8) * 3.5 + (t * 0.4)
        frame = SevenSegmentRenderer.render_full_meter_display(f"{val:.1f}", display_type="led_red", width=width, height=height, add_meter_frame=True)
        out_norm.write(frame)
    out_norm.release()
    print(f"[OK] Created {norm_vid_path.name}")

    # 4. 12-second Overpressure Critical Alert Video (MP4)
    alert_vid_path = SAMPLES_DIR / "boiler_overpressure_alert_12s.mp4"
    total_frames_alert = 12 * fps
    out_alert = cv2.VideoWriter(str(alert_vid_path), fourcc, fps, (width, height))

    for i in range(total_frames_alert):
        t = i / fps
        val = 60.0 + (t * 2.8) + np.sin(t * 2.0) * 0.8
        frame = SevenSegmentRenderer.render_full_meter_display(f"{val:.1f}", display_type="led_red", width=width, height=height, add_meter_frame=True)
        out_alert.write(frame)
    out_alert.release()
    print(f"[OK] Created {alert_vid_path.name}")

    print("[OK] All sample assets generated successfully.")

if __name__ == "__main__":
    generate_sample_videos_and_images()
