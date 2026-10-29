import os
import io
import csv
import uuid
import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.config import UPLOAD_DIR
from backend.models.db_models import VideoJob, Reading
from backend.schemas import VideoJobOut, VideoJobDetailOut, ReadingOut
from backend.services.video_service import video_service, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES
from backend.models.ml.dataset_generator import SevenSegmentRenderer

router = APIRouter(prefix="/api/video", tags=["Mode B - Video Analysis"])

@router.post("/upload", response_model=VideoJobOut)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sample_interval_sec: float = Form(1.0),
    roi_x: Optional[float] = Form(None),
    roi_y: Optional[float] = Form(None),
    roi_w: Optional[float] = Form(None),
    roi_h: Optional[float] = Form(None),
    db: Session = Depends(get_db)
):
    """Uploads an industrial video (MP4/AVI), validates format, and queues frame extraction & DL analysis."""
    # Validate extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '{file_ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Save to disk while checking size
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    saved_path = UPLOAD_DIR / unique_filename

    total_bytes = 0
    try:
        with open(saved_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE_BYTES:
                    saved_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=400, detail="File exceeds maximum allowed size of 100MB.")
                buffer.write(chunk)
    except Exception as e:
        saved_path.unlink(missing_ok=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")

    # Parse ROI if provided
    roi_dict = None
    if all(v is not None for v in [roi_x, roi_y, roi_w, roi_h]):
        roi_dict = {"x": roi_x, "y": roi_y, "width": roi_w, "height": roi_h}

    # Create job in database
    job = VideoJob(
        filename=unique_filename,
        original_name=file.filename,
        file_size_bytes=total_bytes,
        sample_interval_sec=sample_interval_sec,
        status="QUEUED",
        progress_percent=0.0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Launch background extraction and recognition pipeline
    background_tasks.add_task(
        video_service.process_video_job_background,
        job_id=job.id,
        video_path=str(saved_path),
        sample_interval_sec=sample_interval_sec,
        roi=roi_dict
    )

    return job

@router.get("/jobs", response_model=List[VideoJobOut])
def list_video_jobs(db: Session = Depends(get_db)):
    """Lists all video analysis jobs ordered by most recent."""
    return db.query(VideoJob).order_by(desc(VideoJob.created_at)).all()

@router.get("/jobs/{job_id}", response_model=VideoJobDetailOut)
def get_video_job(job_id: int, db: Session = Depends(get_db)):
    """Fetches video job status, progress, summary statistics, and extracted readings."""
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found.")
    return job

@router.get("/jobs/{job_id}/readings", response_model=List[ReadingOut])
def get_video_job_readings(job_id: int, db: Session = Depends(get_db)):
    """Fetches time-series readings extracted from the specified video job."""
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found.")

    readings = db.query(Reading).filter(Reading.video_job_id == job_id).order_by(Reading.video_relative_time.asc()).all()
    return readings

@router.get("/jobs/{job_id}/csv")
def export_video_job_csv(job_id: int, db: Session = Depends(get_db)):
    """Exports the time-series readings of this video job as a CSV file."""
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found.")

    readings = db.query(Reading).filter(Reading.video_job_id == job_id).order_by(Reading.video_relative_time.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Relative Time (s)", "Timestamp", "Raw Text", "Numerical Value",
        "Unit", "Confidence", "Status", "Model Used", "Inference Time (ms)", "Is Inferred"
    ])

    for r in readings:
        writer.writerow([
            f"{r.video_relative_time:.2f}" if r.video_relative_time is not None else "",
            r.timestamp.isoformat() if r.timestamp else "",
            r.raw_text,
            r.numerical_value if r.numerical_value is not None else "",
            r.unit,
            f"{r.confidence:.3f}",
            r.status,
            r.model_used,
            f"{r.inference_time_ms:.2f}",
            r.is_inferred
        ])

    csv_data = output.getvalue()
    filename = f"video_analysis_job_{job_id}_{job.original_name}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/generate-demo", response_model=VideoJobOut)
def generate_and_analyze_demo_video(
    background_tasks: BackgroundTasks,
    duration_seconds: int = 10,
    db: Session = Depends(get_db)
):
    """
    Generates a realistic synthetic industrial instrument MP4 video showing changing parameters,
    and automatically queues it for Mode B video analysis.
    """
    demo_filename = f"demo_industrial_meter_{uuid.uuid4().hex[:8]}.mp4"
    demo_path = UPLOAD_DIR / demo_filename

    fps = 10
    total_frames = duration_seconds * fps
    width, height = 480, 240

    # Video writer with mp4v codec
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(demo_path), fourcc, fps, (width, height))

    base_pressure = 48.0
    for i in range(total_frames):
        # Simulate gentle pressure rise and subtle oscillation
        t_sec = i / fps
        val = base_pressure + (t_sec * 2.5) + np.sin(t_sec * 1.5) * 1.2
        val_str = f"{val:.1f}"

        # Generate realistic meter face
        meter_face = SevenSegmentRenderer.render_full_meter_display(
            val_str, display_type="led_red", width=width, height=height, add_meter_frame=True
        )
        out.write(meter_face)

    out.release()

    file_size = demo_path.stat().st_size
    job = VideoJob(
        filename=demo_filename,
        original_name="simulated_boiler_pressure_10s.mp4",
        file_size_bytes=file_size,
        duration_seconds=float(duration_seconds),
        total_frames=total_frames,
        sample_interval_sec=1.0,
        status="QUEUED",
        progress_percent=0.0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Launch processing
    background_tasks.add_task(
        video_service.process_video_job_background,
        job_id=job.id,
        video_path=str(demo_path),
        sample_interval_sec=1.0,
        roi=None
    )

    return job
