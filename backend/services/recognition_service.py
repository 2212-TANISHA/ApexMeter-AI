import base64
import time
import cv2
import numpy as np
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from backend.config import DEFAULT_CONFIG
from backend.models.db_models import SystemConfig, Reading
from backend.models.ml.base import BaseDigitRecognizer, RecognitionResult
from backend.models.ml.pytorch_recognizer import PyTorchDigitRecognizer
from backend.models.ml.baseline_ocr import BaselineOcrRecognizer
from backend.schemas import ProcessFrameResponse, RoiBoundingBox

class RecognitionService:
    def __init__(self):
        # Lazy singleton instances
        self.pytorch_model = PyTorchDigitRecognizer()
        self.baseline_model = BaselineOcrRecognizer()

    def get_model(self, model_key: str) -> BaseDigitRecognizer:
        if model_key == "baseline_ocr":
            return self.baseline_model
        return self.pytorch_model

    @staticmethod
    def decode_base64_image(image_base64: str) -> np.ndarray:
        """Decodes base64 string (including data URI) into OpenCV BGR numpy array."""
        if ',' in image_base64:
            image_base64 = image_base64.split(',', 1)[1]
        img_bytes = base64.b64decode(image_base64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image from provided base64 data.")
        return img

    def evaluate_thresholds(self, value: Optional[float], config: SystemConfig, base_status: str) -> str:
        """Determines operational status (VALID, WARNING, CRITICAL, UNCERTAIN, INVALID) against thresholds."""
        if value is None or base_status == "INVALID":
            return "INVALID"
        if base_status == "UNCERTAIN":
            return "UNCERTAIN"

        if config.max_critical is not None and value >= config.max_critical:
            return "CRITICAL"
        if config.min_critical is not None and value <= config.min_critical:
            return "CRITICAL"
        if config.max_warning is not None and value >= config.max_warning:
            return "WARNING"
        if config.min_warning is not None and value <= config.min_warning:
            return "WARNING"

        return "VALID"

    def process_frame(
        self,
        db: Session,
        image: np.ndarray,
        roi: Optional[RoiBoundingBox] = None,
        source: str = "camera",
        save_reading: bool = True,
        model_override: Optional[str] = None,
        video_job_id: Optional[int] = None,
        video_relative_time: Optional[float] = None,
        is_inferred: int = 0
    ) -> ProcessFrameResponse:
        # Load system configuration
        cfg = db.query(SystemConfig).first()
        if not cfg:
            cfg = SystemConfig(**DEFAULT_CONFIG)
            db.add(cfg)
            db.commit()
            db.refresh(cfg)

        model_key = model_override or cfg.active_model
        model = self.get_model(model_key)

        roi_dict = roi.dict() if roi else None
        result: RecognitionResult = model.predict_display(image, roi=roi_dict)

        # Re-evaluate confidence threshold
        effective_status = result.status
        if result.confidence < cfg.confidence_threshold and result.status == "VALID":
            effective_status = "UNCERTAIN"

        final_status = self.evaluate_thresholds(result.numerical_value, cfg, effective_status)

        saved_reading_id = None
        if save_reading and final_status != "INVALID":
            reading = Reading(
                source=source,
                video_job_id=video_job_id,
                video_relative_time=video_relative_time,
                raw_text=result.raw_text,
                numerical_value=result.numerical_value,
                unit=cfg.unit,
                confidence=result.confidence,
                status=final_status,
                model_used=model_key,
                inference_time_ms=result.inference_time_ms,
                is_inferred=is_inferred
            )
            db.add(reading)
            db.commit()
            db.refresh(reading)
            saved_reading_id = reading.id

        return ProcessFrameResponse(
            raw_text=result.raw_text,
            numerical_value=result.numerical_value,
            unit=cfg.unit,
            confidence=result.confidence,
            status=final_status,
            inference_time_ms=result.inference_time_ms,
            model_used=model_key,
            annotated_image_base64=result.annotated_image_base64,
            warning_or_error=result.warning_or_error,
            reading_id=saved_reading_id
        )

# Global service instance
recognition_service = RecognitionService()
