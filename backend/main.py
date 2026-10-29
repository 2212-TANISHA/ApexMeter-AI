from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import init_db
from backend.config import UPLOAD_DIR, FRAMES_DIR, SAMPLES_DIR, BASE_DIR
from backend.api.routes_health import router as health_router
from backend.api.routes_monitoring import router as monitoring_router
from backend.api.routes_video import router as video_router
from backend.api.routes_readings import router as readings_router
from backend.api.routes_config import router as config_router
from backend.api.routes_models import router as models_router

# Initialize database schema
init_db()

app = FastAPI(
    title="AI-Based Industrial Machine Parameter Monitoring API",
    description="Deep Learning Capstone Backend for Industrial Digital Display Recognition",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories for media previews
app.mount("/media/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/media/samples", StaticFiles(directory=str(SAMPLES_DIR)), name="samples")

# Register API routes
app.include_router(health_router)
app.include_router(monitoring_router)
app.include_router(video_router)
app.include_router(readings_router)
app.include_router(config_router)
app.include_router(models_router)

# Mount compiled React frontend if present
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "message": "AI-Based Industrial Machine Parameter Monitoring API is running.",
            "docs_url": "/docs",
            "health_check": "/api/health"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
