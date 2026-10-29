import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def main():
    print("=" * 75)
    print("  AI-BASED INDUSTRIAL MACHINE PARAMETER MONITORING SYSTEM")
    print("  Deep Learning Capstone Project | PyTorch CNN + OpenCV + FastAPI + React")
    print("=" * 75)

    weights_file = BASE_DIR / "backend" / "models" / "weights" / "meter_cnn.pt"
    if not weights_file.exists():
        print("[*] Model weights not found. Launching training pipeline...")
        subprocess.run([sys.executable, str(BASE_DIR / "backend" / "train.py")], check=True)

    samples_dir = BASE_DIR / "sample_data"
    if not any(samples_dir.glob("*.mp4")):
        print("[*] Sample videos not found. Generating sample industrial meter assets...")
        subprocess.run([sys.executable, str(BASE_DIR / "backend" / "generate_samples.py")], check=True)

    print("[*] Starting ApexMeter AI Backend Server...")
    print("    URL: http://127.0.0.1:8000")
    print("    API Docs: http://127.0.0.1:8000/docs")
    print("    Frontend: http://127.0.0.1:8000 (Built UI) or http://localhost:5173 (Vite Dev)")
    print("=" * 75)

    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
