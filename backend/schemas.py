from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field

class ReadingBase(BaseModel):
    raw_text: Optional[str] = None
    numerical_value: Optional[float] = None
    unit: str = "PSI"
    confidence: float = 0.0
    status: str = "VALID"
    source: str = "camera"
    model_used: str = "pytorch_cnn"
    inference_time_ms: float = 0.0
    video_job_id: Optional[int] = None
    video_relative_time: Optional[float] = None
    is_inferred: int = 0

class ReadingCreate(ReadingBase):
    pass

class ReadingOut(ReadingBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class SystemConfigSchema(BaseModel):
    machine_id: str = "BOILER-TURBINE-01"
    parameter_name: str = "Steam Pressure"
    unit: str = "PSI"
    min_critical: float = 5.0
    min_warning: float = 15.0
    max_warning: float = 75.0
    max_critical: float = 90.0
    active_model: str = "pytorch_cnn"
    confidence_threshold: float = 0.65
    sampling_interval_ms: int = 1000

    class Config:
        from_attributes = True

class SystemConfigOut(SystemConfigSchema):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True

class RoiBoundingBox(BaseModel):
    x: float = Field(0.0, ge=0.0, le=1.0)
    y: float = Field(0.0, ge=0.0, le=1.0)
    width: float = Field(1.0, gt=0.0, le=1.0)
    height: float = Field(1.0, gt=0.0, le=1.0)

class ProcessFrameRequest(BaseModel):
    image_base64: str
    roi: Optional[RoiBoundingBox] = None
    source: str = "camera"  # "camera" or "simulated"
    save_reading: bool = True
    model_override: Optional[str] = None

class ProcessFrameResponse(BaseModel):
    raw_text: str
    numerical_value: Optional[float]
    unit: str
    confidence: float
    status: str  # VALID, WARNING, CRITICAL, UNCERTAIN, INVALID
    inference_time_ms: float
    model_used: str
    annotated_image_base64: Optional[str] = None
    warning_or_error: Optional[str] = None
    reading_id: Optional[int] = None

class VideoJobOut(BaseModel):
    id: int
    filename: str
    original_name: str
    file_size_bytes: int
    duration_seconds: float
    total_frames: int
    sample_interval_sec: float
    status: str
    progress_percent: float
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_extracted_readings: int
    valid_readings_count: int
    invalid_readings_count: int
    duplicate_filtered_count: int
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None

    class Config:
        from_attributes = True

class VideoJobDetailOut(VideoJobOut):
    readings: List[ReadingOut] = []

class DashboardStatsOut(BaseModel):
    latest_reading: Optional[ReadingOut] = None
    total_readings: int = 0
    valid_readings_count: int = 0
    success_rate_percent: float = 0.0
    active_alerts_count: int = 0
    current_status: str = "NORMAL"
    config: SystemConfigSchema
