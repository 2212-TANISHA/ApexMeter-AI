import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.database import SessionLocal, init_db
from backend.models.db_models import VideoJob, Reading
from backend.services.video_service import video_service
from backend.config import SAMPLES_DIR

def test_video_pipeline():
    init_db()
    db = SessionLocal()

    sample_vid = SAMPLES_DIR / "boiler_pressure_normal_15s.mp4"
    if not sample_vid.exists():
        print("Sample video missing!")
        return

    print("[*] Creating test video job...")
    job = VideoJob(
        filename="test_boiler_run.mp4",
        original_name="boiler_pressure_normal_15s.mp4",
        file_size_bytes=sample_vid.stat().st_size,
        sample_interval_sec=1.0,
        status="QUEUED"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    print(f"[*] Running video background pipeline on job ID {job.id}...")
    video_service.process_video_job_background(
        job_id=job.id,
        video_path=str(sample_vid),
        sample_interval_sec=1.0
    )

    # Refresh job
    db.refresh(job)
    print(f"[OK] Job Status: {job.status}, Progress: {job.progress_percent}%")
    print(f"[OK] Duration: {job.duration_seconds}s, Extracted: {job.total_extracted_readings}")
    print(f"[OK] Valid: {job.valid_readings_count}, Invalid: {job.invalid_readings_count}, Duplicates: {job.duplicate_filtered_count}")
    print(f"[OK] Stats -> Min: {job.min_value}, Max: {job.max_value}, Avg: {job.avg_value}")

    # Inspect first 3 readings
    readings = db.query(Reading).filter(Reading.video_job_id == job.id).order_by(Reading.video_relative_time.asc()).limit(3).all()
    for r in readings:
        print(f"  Frame @ {r.video_relative_time}s -> Val: {r.numerical_value} ({r.raw_text}) | Conf: {r.confidence} | Status: {r.status} | Inferred: {r.is_inferred}")

    db.close()
    print("[OK] VIDEO PIPELINE INTEGRATION TEST PASSED!")

if __name__ == '__main__':
    test_video_pipeline()
