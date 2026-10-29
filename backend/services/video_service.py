import os
import time
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from backend.config import UPLOAD_DIR
from backend.database import SessionLocal
from backend.models.db_models import VideoJob, Reading, SystemConfig
from backend.services.recognition_service import recognition_service
from backend.schemas import RoiBoundingBox

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB

class VideoService:
    @staticmethod
    def validate_video_file(file_name: str, file_size: int) -> Tuple[bool, Optional[str]]:
        ext = Path(file_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Unsupported video format '{ext}'. Supported formats: {', '.join(ALLOWED_EXTENSIONS)}"
        if file_size > MAX_FILE_SIZE_BYTES:
            max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
            return False, f"File size ({file_size // (1024 * 1024)} MB) exceeds {max_mb} MB limit."
        return True, None

    @classmethod
    def process_video_job_background(
        cls,
        job_id: int,
        video_path: str,
        sample_interval_sec: float = 1.0,
        roi: Optional[dict] = None
    ):
        """
        Background task to extract frames from video, run recognition pipeline,
        filter duplicates, compute metrics, and persist to SQLite.
        """
        db = SessionLocal()
        try:
            job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
            if not job:
                return

            job.status = "PROCESSING"
            job.progress_percent = 5.0
            db.commit()

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                job.status = "FAILED"
                job.error_message = "Could not open video file for processing."
                db.commit()
                return

            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration_sec = total_frames / fps if fps > 0 else 0.0

            job.total_frames = total_frames
            job.duration_seconds = round(duration_sec, 2)
            job.sample_interval_sec = sample_interval_sec
            db.commit()

            frame_step = max(1, int(fps * sample_interval_sec))
            extracted_count = 0
            valid_values = []
            invalid_count = 0
            duplicate_count = 0
            last_valid_val = None

            roi_bbox = RoiBoundingBox(**roi) if roi else None

            current_frame_idx = 0
            while current_frame_idx < total_frames:
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_idx)
                ret, frame = cap.read()
                if not ret:
                    break

                rel_time = round(current_frame_idx / fps, 2)
                extracted_count += 1

                # Recognize frame
                resp = recognition_service.process_frame(
                    db=db,
                    image=frame,
                    roi=roi_bbox,
                    source="video",
                    save_reading=False,  # We will save below with deduplication logic
                    video_job_id=job.id,
                    video_relative_time=rel_time
                )

                is_duplicate = False
                is_valid_reading = (resp.numerical_value is not None) and (resp.status in ["VALID", "WARNING", "CRITICAL"])

                if is_valid_reading:
                    # Check for duplicate reading
                    if last_valid_val is not None and abs(resp.numerical_value - last_valid_val) < 1e-4:
                        duplicate_count += 1
                        is_duplicate = True
                    else:
                        last_valid_val = resp.numerical_value
                    valid_values.append(resp.numerical_value)
                else:
                    invalid_count += 1

                # Persist Reading linked to this VideoJob
                new_reading = Reading(
                    source="video",
                    video_job_id=job.id,
                    video_relative_time=rel_time,
                    raw_text=resp.raw_text,
                    numerical_value=resp.numerical_value,
                    unit=resp.unit,
                    confidence=resp.confidence,
                    status=resp.status,
                    model_used=resp.model_used,
                    inference_time_ms=resp.inference_time_ms,
                    is_inferred=1 if is_duplicate else 0
                )
                db.add(new_reading)

                # Update progress
                progress = min(98.0, 5.0 + (current_frame_idx / total_frames) * 90.0)
                job.progress_percent = round(progress, 1)
                db.commit()

                current_frame_idx += frame_step

            cap.release()

            # Finalize summary statistics
            valid_count = len(valid_values)
            job.total_extracted_readings = extracted_count
            job.valid_readings_count = valid_count
            job.invalid_readings_count = invalid_count
            job.duplicate_filtered_count = duplicate_count

            if valid_values:
                job.min_value = round(float(np.min(valid_values)), 2)
                job.max_value = round(float(np.max(valid_values)), 2)
                job.avg_value = round(float(np.mean(valid_values)), 2)

            job.status = "COMPLETED"
            job.progress_percent = 100.0
            job.completed_at = datetime.utcnow()
            db.commit()

        except Exception as e:
            db.rollback()
            try:
                job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
                if job:
                    job.status = "FAILED"
                    job.error_message = str(e)
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

video_service = VideoService()
