from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base

class SystemConfig(Base):
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(64), default="BOILER-TURBINE-01")
    parameter_name = Column(String(64), default="Steam Pressure")
    unit = Column(String(16), default="PSI")
    min_critical = Column(Float, default=5.0)
    min_warning = Column(Float, default=15.0)
    max_warning = Column(Float, default=75.0)
    max_critical = Column(Float, default=90.0)
    active_model = Column(String(32), default="pytorch_cnn")
    confidence_threshold = Column(Float, default=0.65)
    sampling_interval_ms = Column(Integer, default=1000)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VideoJob(Base):
    __tablename__ = "video_jobs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    total_frames = Column(Integer, default=0)
    sample_interval_sec = Column(Float, default=1.0)
    status = Column(String(32), default="QUEUED")  # QUEUED, PROCESSING, COMPLETED, FAILED
    progress_percent = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Aggregated Summary Metrics
    total_extracted_readings = Column(Integer, default=0)
    valid_readings_count = Column(Integer, default=0)
    invalid_readings_count = Column(Integer, default=0)
    duplicate_filtered_count = Column(Integer, default=0)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    avg_value = Column(Float, nullable=True)

    readings = relationship("Reading", back_populates="video_job", cascade="all, delete-orphan")

class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String(32), default="camera")  # "camera", "video", "simulated"
    video_job_id = Column(Integer, ForeignKey("video_jobs.id", ondelete="SET NULL"), nullable=True)
    video_relative_time = Column(Float, nullable=True)  # elapsed seconds in video
    
    raw_text = Column(String(64), nullable=True)
    numerical_value = Column(Float, nullable=True)
    unit = Column(String(16), default="PSI")
    confidence = Column(Float, default=0.0)
    status = Column(String(32), default="VALID")  # VALID, WARNING, CRITICAL, UNCERTAIN, INVALID
    model_used = Column(String(64), default="pytorch_cnn")
    inference_time_ms = Column(Float, default=0.0)
    frame_path = Column(String(255), nullable=True)
    is_inferred = Column(Integer, default=0)  # 0: measured, 1: inferred / interpolated

    video_job = relationship("VideoJob", back_populates="readings")
