import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
FRAMES_DIR = DATA_DIR / "extracted_frames"
WEIGHTS_DIR = BASE_DIR / "models" / "weights"
SAMPLES_DIR = PROJECT_DIR / "sample_data"

# Ensure runtime directories exist
for path in [DATA_DIR, UPLOAD_DIR, FRAMES_DIR, WEIGHTS_DIR, SAMPLES_DIR]:
    path.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'industrial_meter.db'}"

# Default machine monitoring parameters
DEFAULT_CONFIG = {
    "machine_id": "BOILER-TURBINE-01",
    "parameter_name": "Steam Pressure",
    "unit": "PSI",
    "min_critical": 5.0,
    "min_warning": 15.0,
    "max_warning": 75.0,
    "max_critical": 90.0,
    "active_model": "pytorch_cnn",  # "pytorch_cnn" or "baseline_ocr"
    "confidence_threshold": 0.65,
    "sampling_interval_ms": 1000
}
