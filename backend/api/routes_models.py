import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks

from backend.config import WEIGHTS_DIR
from backend.services.recognition_service import recognition_service
from backend.evaluate import evaluate_models

router = APIRouter(prefix="/api/models", tags=["Model Evaluation & Benchmark"])

@router.get("/info")
def get_models_info():
    """Returns technical metadata for both Deep Learning and Conventional Baseline models."""
    pt_info = recognition_service.pytorch_model.get_model_info()
    bl_info = recognition_service.baseline_model.get_model_info()

    return {
        "deep_learning_model": pt_info,
        "baseline_model": bl_info
    }

@router.get("/evaluation")
def get_evaluation_report():
    """Fetches the latest measured benchmark metrics comparing PyTorch CNN vs Conventional OCR."""
    report_path = WEIGHTS_DIR / "evaluation_report.json"
    if not report_path.exists():
        # Generate initial report if not existing
        return evaluate_models(num_test_samples=40)

    try:
        with open(report_path, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read evaluation report: {str(e)}")

@router.post("/run-evaluation")
def trigger_evaluation(num_samples: int = 50):
    """Executes a benchmark evaluation run across both models and updates the report."""
    safe_samples = max(10, min(100, num_samples))
    results = evaluate_models(num_test_samples=safe_samples)
    return {
        "message": f"Successfully evaluated {safe_samples} test displays.",
        "results": results
    }
