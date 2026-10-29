import io
import csv
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.config import DEFAULT_CONFIG
from backend.models.db_models import Reading, SystemConfig
from backend.schemas import ReadingOut, DashboardStatsOut, SystemConfigSchema

router = APIRouter(prefix="/api/readings", tags=["Readings & Telemetry"])

@router.get("", response_model=List[ReadingOut])
def get_readings(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    source: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieves paginated readings, optionally filtered by source or status."""
    query = db.query(Reading)
    if source:
        query = query.filter(Reading.source == source)
    if status:
        query = query.filter(Reading.status == status)

    readings = query.order_by(desc(Reading.timestamp)).offset(offset).limit(limit).all()
    return readings

@router.get("/latest", response_model=Optional[ReadingOut])
def get_latest_valid_reading(db: Session = Depends(get_db)):
    """Fetches the most recent valid reading."""
    latest = db.query(Reading).filter(
        Reading.status.in_(["VALID", "WARNING", "CRITICAL"])
    ).order_by(desc(Reading.timestamp)).first()
    return latest

@router.get("/stats", response_model=DashboardStatsOut)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Computes KPI statistics: latest reading, success rate, alert count, system status."""
    cfg = db.query(SystemConfig).first()
    if not cfg:
        cfg = SystemConfig(**DEFAULT_CONFIG)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)

    total_count = db.query(Reading).count()
    valid_count = db.query(Reading).filter(
        Reading.status.in_(["VALID", "WARNING", "CRITICAL"])
    ).count()

    success_rate = round((valid_count / total_count * 100.0), 1) if total_count > 0 else 100.0

    # Count recent critical or warning alerts
    alerts_count = db.query(Reading).filter(
        Reading.status.in_(["WARNING", "CRITICAL"])
    ).count()

    latest = db.query(Reading).filter(
        Reading.status.in_(["VALID", "WARNING", "CRITICAL"])
    ).order_by(desc(Reading.timestamp)).first()

    current_status = "NORMAL"
    if latest:
        if latest.status == "CRITICAL":
            current_status = "CRITICAL_ALERT"
        elif latest.status == "WARNING":
            current_status = "WARNING_ALERT"

    return DashboardStatsOut(
        latest_reading=latest,
        total_readings=total_count,
        valid_readings_count=valid_count,
        success_rate_percent=success_rate,
        active_alerts_count=alerts_count,
        current_status=current_status,
        config=SystemConfigSchema.model_validate(cfg)
    )

@router.get("/export-csv")
def export_readings_csv(
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Exports all readings history as a downloadable CSV file."""
    query = db.query(Reading)
    if source:
        query = query.filter(Reading.source == source)

    readings = query.order_by(Reading.timestamp.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Timestamp (UTC)", "Source", "Raw Text", "Numerical Value",
        "Unit", "Confidence", "Status", "Model Used", "Latency (ms)", "Is Inferred"
    ])

    for r in readings:
        writer.writerow([
            r.id,
            r.timestamp.isoformat() if r.timestamp else "",
            r.source,
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
    filename = f"industrial_meter_readings_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.delete("/clear")
def clear_readings_history(db: Session = Depends(get_db)):
    """Clears readings history for fresh testing or demo sessions."""
    deleted_count = db.query(Reading).delete()
    db.commit()
    return {"message": f"Cleared {deleted_count} readings from database."}
