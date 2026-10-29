from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.config import DEFAULT_CONFIG
from backend.models.db_models import SystemConfig
from backend.schemas import SystemConfigSchema, SystemConfigOut

router = APIRouter(prefix="/api/config", tags=["Configuration & Thresholds"])

@router.get("/thresholds", response_model=SystemConfigOut)
def get_system_config(db: Session = Depends(get_db)):
    cfg = db.query(SystemConfig).first()
    if not cfg:
        cfg = SystemConfig(**DEFAULT_CONFIG)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg

@router.put("/thresholds", response_model=SystemConfigOut)
def update_system_config(update_data: SystemConfigSchema, db: Session = Depends(get_db)):
    cfg = db.query(SystemConfig).first()
    if not cfg:
        cfg = SystemConfig(**DEFAULT_CONFIG)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)

    # Validate logical thresholds: min_critical <= min_warning < max_warning <= max_critical
    if update_data.min_critical > update_data.min_warning:
        raise HTTPException(status_code=400, detail="Lower critical threshold cannot exceed lower warning threshold.")
    if update_data.max_warning > update_data.max_critical:
        raise HTTPException(status_code=400, detail="Upper warning threshold cannot exceed upper critical threshold.")
    if update_data.min_warning >= update_data.max_warning:
        raise HTTPException(status_code=400, detail="Lower warning threshold must be less than upper warning threshold.")

    cfg.machine_id = update_data.machine_id
    cfg.parameter_name = update_data.parameter_name
    cfg.unit = update_data.unit
    cfg.min_critical = update_data.min_critical
    cfg.min_warning = update_data.min_warning
    cfg.max_warning = update_data.max_warning
    cfg.max_critical = update_data.max_critical
    cfg.active_model = update_data.active_model
    cfg.confidence_threshold = update_data.confidence_threshold
    cfg.sampling_interval_ms = update_data.sampling_interval_ms

    db.commit()
    db.refresh(cfg)
    return cfg
