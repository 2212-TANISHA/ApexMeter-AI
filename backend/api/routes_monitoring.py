import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.recognition_service import recognition_service
from backend.schemas import ProcessFrameRequest, ProcessFrameResponse
from backend.models.ml.dataset_generator import SevenSegmentRenderer

router = APIRouter(prefix="/api/monitoring", tags=["Live Monitoring"])

@router.post("/process-frame", response_model=ProcessFrameResponse)
def process_live_frame(req: ProcessFrameRequest, db: Session = Depends(get_db)):
    """Processes a live camera frame, predicts display reading with DL model, and saves valid readings."""
    try:
        frame_cv = recognition_service.decode_base64_image(req.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")

    response = recognition_service.process_frame(
        db=db,
        image=frame_cv,
        roi=req.roi,
        source=req.source,
        save_reading=req.save_reading,
        model_override=req.model_override
    )
    return response

@router.post("/simulate-frame", response_model=ProcessFrameResponse)
def simulate_live_frame(
    target_value: float = None,
    noise: bool = True,
    db: Session = Depends(get_db)
):
    """
    Generates a simulated industrial meter frame (clearly flagged as simulated).
    Allows full end-to-end testing of Mode A live monitoring even without physical camera or meter hardware.
    """
    if target_value is None:
        target_value = round(random.uniform(40.0, 78.0), 1)

    val_str = f"{target_value:.1f}"
    disp_type = random.choice(["led_red", "led_green", "lcd_green"])
    sim_img = SevenSegmentRenderer.render_full_meter_display(val_str, display_type=disp_type, add_meter_frame=False)

    response = recognition_service.process_frame(
        db=db,
        image=sim_img,
        source="simulated",
        save_reading=True
    )
    return response
