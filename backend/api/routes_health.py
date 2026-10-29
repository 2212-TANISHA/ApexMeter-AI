import sys
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import torch
import cv2

from backend.database import get_db
from backend.config import WEIGHTS_DIR

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("")
def get_health(db: Session = Depends(get_db)):
    # Test database connectivity
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    weights_file = WEIGHTS_DIR / "meter_cnn.pt"
    weights_available = weights_file.exists()

    return {
        "status": "healthy" if db_ok else "degraded",
        "service": "AI Industrial Meter Monitoring Backend",
        "python_version": sys.version.split(" ")[0],
        "torch_version": torch.__version__,
        "opencv_version": cv2.__version__,
        "database_connected": db_ok,
        "deep_learning_model_weights_loaded": weights_available,
        "device": "cuda" if torch.cuda.is_available() else "cpu"
    }
