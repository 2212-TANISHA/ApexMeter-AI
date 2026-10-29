import os
import sys
import json
import time
import random
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import WEIGHTS_DIR
from backend.models.ml.pytorch_recognizer import PyTorchDigitRecognizer
from backend.models.ml.baseline_ocr import BaselineOcrRecognizer
from backend.models.ml.dataset_generator import SevenSegmentRenderer

def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein edit distance between two character strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def evaluate_models(num_test_samples: int = 60, seed: int = 101) -> Dict[str, Any]:
    random.seed(seed)
    np.random.seed(seed)

    print("=" * 70)
    print("AI-Based Industrial Machine Parameter Monitoring - Model Benchmark")
    print(f"Comparing PyTorch CNN vs Conventional OCR Baseline on {num_test_samples} displays")
    print("=" * 70)

    # Initialize models
    dl_model = PyTorchDigitRecognizer()
    baseline_model = BaselineOcrRecognizer()

    # Generate diverse test ground truths
    display_types = ["led_red", "led_green", "lcd_green"]
    test_cases = []

    for i in range(num_test_samples):
        val_type = random.choice(["int", "float1", "float2", "negative"])
        if val_type == "int":
            val_str = str(random.randint(10, 999))
        elif val_type == "float1":
            val_str = f"{random.uniform(5.0, 99.9):.1f}"
        elif val_type == "float2":
            val_str = f"{random.uniform(10.0, 99.9):.2f}"
        else:
            val_str = f"-{random.uniform(1.0, 45.0):.1f}"

        disp_type = random.choice(display_types)
        img = SevenSegmentRenderer.render_full_meter_display(val_str, display_type=disp_type, add_meter_frame=False)
        test_cases.append({"ground_truth": val_str, "image": img, "display_type": disp_type})

    # Metrics accumulators
    results = {
        "dl_model": {
            "name": "IndustrialMeter PyTorch CNN",
            "exact_matches": 0,
            "total_chars": 0,
            "correct_chars": 0,
            "total_edit_distance": 0,
            "inference_times": [],
            "predictions": []
        },
        "baseline_ocr": {
            "name": "Conventional 7-Segment OCR",
            "exact_matches": 0,
            "total_chars": 0,
            "correct_chars": 0,
            "total_edit_distance": 0,
            "inference_times": [],
            "predictions": []
        }
    }

    print("[*] Running evaluations...")
    for idx, case in enumerate(test_cases):
        gt = case["ground_truth"]
        img = case["image"]
        n_chars = len(gt)

        # 1. Evaluate DL model
        res_dl = dl_model.predict_display(img)
        pred_dl = res_dl.raw_text
        ed_dl = levenshtein_distance(gt, pred_dl)

        results["dl_model"]["total_chars"] += n_chars
        results["dl_model"]["total_edit_distance"] += ed_dl
        results["dl_model"]["inference_times"].append(res_dl.inference_time_ms)
        if pred_dl == gt:
            results["dl_model"]["exact_matches"] += 1
        results["dl_model"]["correct_chars"] += max(0, n_chars - ed_dl)

        # 2. Evaluate Baseline OCR
        res_base = baseline_model.predict_display(img)
        pred_base = res_base.raw_text
        ed_base = levenshtein_distance(gt, pred_base)

        results["baseline_ocr"]["total_chars"] += n_chars
        results["baseline_ocr"]["total_edit_distance"] += ed_base
        results["baseline_ocr"]["inference_times"].append(res_base.inference_time_ms)
        if pred_base == gt:
            results["baseline_ocr"]["exact_matches"] += 1
        results["baseline_ocr"]["correct_chars"] += max(0, n_chars - ed_base)

        if (idx + 1) % 15 == 0 or (idx + 1) == num_test_samples:
            print(f"    Progress: {idx + 1}/{num_test_samples} samples evaluated")

    # Aggregate percentages
    total = num_test_samples
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_test_samples": total,
        "models": {
            "pytorch_cnn": {
                "name": "IndustrialMeter PyTorch CNN",
                "exact_accuracy_percent": round((results["dl_model"]["exact_matches"] / total) * 100.0, 2),
                "digit_accuracy_percent": round((results["dl_model"]["correct_chars"] / results["dl_model"]["total_chars"]) * 100.0, 2),
                "character_error_rate": round(results["dl_model"]["total_edit_distance"] / results["dl_model"]["total_chars"], 4),
                "avg_inference_time_ms": round(float(np.mean(results["dl_model"]["inference_times"])), 2),
                "min_inference_time_ms": round(float(np.min(results["dl_model"]["inference_times"])), 2),
                "max_inference_time_ms": round(float(np.max(results["dl_model"]["inference_times"])), 2),
                "trainable_parameters": dl_model.get_model_info()["trainable_parameters"]
            },
            "baseline_ocr": {
                "name": "Conventional 7-Segment OCR",
                "exact_accuracy_percent": round((results["baseline_ocr"]["exact_matches"] / total) * 100.0, 2),
                "digit_accuracy_percent": round((results["baseline_ocr"]["correct_chars"] / results["baseline_ocr"]["total_chars"]) * 100.0, 2),
                "character_error_rate": round(results["baseline_ocr"]["total_edit_distance"] / results["baseline_ocr"]["total_chars"], 4),
                "avg_inference_time_ms": round(float(np.mean(results["baseline_ocr"]["inference_times"])), 2),
                "min_inference_time_ms": round(float(np.min(results["baseline_ocr"]["inference_times"])), 2),
                "max_inference_time_ms": round(float(np.max(results["baseline_ocr"]["inference_times"])), 2),
                "trainable_parameters": 0
            }
        }
    }

    # Print summary table
    p_dl = summary["models"]["pytorch_cnn"]
    p_bl = summary["models"]["baseline_ocr"]

    print("\n" + "=" * 70)
    print(f"{'EVALUATION METRIC':<30} | {'PYTORCH CNN':<16} | {'BASELINE OCR':<16}")
    print("-" * 70)
    print(f"{'Exact Reading Accuracy':<30} | {p_dl['exact_accuracy_percent']:>14.2f}% | {p_bl['exact_accuracy_percent']:>14.2f}%")
    print(f"{'Digit-Level Accuracy':<30} | {p_dl['digit_accuracy_percent']:>14.2f}% | {p_bl['digit_accuracy_percent']:>14.2f}%")
    print(f"{'Character Error Rate (CER)':<30} | {p_dl['character_error_rate']:>16.4f} | {p_bl['character_error_rate']:>16.4f}")
    print(f"{'Avg Inference Latency (ms)':<30} | {p_dl['avg_inference_time_ms']:>14.2f}ms | {p_bl['avg_inference_time_ms']:>14.2f}ms")
    print(f"{'Trainable Parameters':<30} | {p_dl['trainable_parameters']:>16,d} | {p_bl['trainable_parameters']:>16,d}")
    print("=" * 70)

    report_path = WEIGHTS_DIR / "evaluation_report.json"
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[OK] Evaluation report saved to: {report_path}")

    return summary

if __name__ == "__main__":
    evaluate_models()
