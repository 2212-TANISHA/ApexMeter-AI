from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass, field
import numpy as np

@dataclass
class RecognitionResult:
    raw_text: str = ""
    numerical_value: Optional[float] = None
    confidence: float = 0.0
    char_confidences: List[Tuple[str, float]] = field(default_factory=list)
    status: str = "INVALID"  # VALID, UNCERTAIN, INVALID
    inference_time_ms: float = 0.0
    model_name: str = "unknown"
    segmented_rois: List[Dict[str, Any]] = field(default_factory=list)
    annotated_image_base64: Optional[str] = None
    warning_or_error: Optional[str] = None

class BaseDigitRecognizer(ABC):
    """Modular abstract interface for industrial digital instrument display recognition."""

    @abstractmethod
    def predict_display(
        self,
        image: np.ndarray,
        roi: Optional[Dict[str, float]] = None
    ) -> RecognitionResult:
        """
        Processes an image frame (or ROI crop) and returns predicted text, value, and confidence.
        
        Args:
            image: BGR numpy image array.
            roi: Optional bounding box dict {'x': float, 'y': float, 'width': float, 'height': float}
                 with normalized coordinates (0.0 to 1.0).
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Returns metadata about the recognition architecture, version, and parameters."""
        pass
