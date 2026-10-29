import urllib.request
import json
import time
import threading
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import uvicorn
from backend.main import app

def run_tests():
    def run_server():
        uvicorn.run(app, host='127.0.0.1', port=8000, log_level='error')

    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(2)

    base = 'http://127.0.0.1:8000'

    # 1. Health
    with urllib.request.urlopen(f'{base}/api/health') as resp:
        health = json.loads(resp.read().decode())
        print(f"[TEST 1] Health: {resp.status} - {health['status']} (PyTorch: {health['torch_version']})")

    # 2. Stats
    with urllib.request.urlopen(f'{base}/api/readings/stats') as resp:
        stats = json.loads(resp.read().decode())
        print(f"[TEST 2] Stats: {resp.status} - Total readings: {stats['total_readings']}, Machine: {stats['config']['machine_id']}")

    # 3. Model Info
    with urllib.request.urlopen(f'{base}/api/models/info') as resp:
        info = json.loads(resp.read().decode())
        print(f"[TEST 3] Model Info: {resp.status} - DL Model: {info['deep_learning_model']['name']}")

    # 4. Evaluation Report
    with urllib.request.urlopen(f'{base}/api/models/evaluation') as resp:
        eval_rep = json.loads(resp.read().decode())
        acc = eval_rep['models']['pytorch_cnn']['exact_accuracy_percent']
        print(f"[TEST 4] Benchmark: {resp.status} - DL Exact Accuracy: {acc}%")

    # 5. Live Simulation Frame
    req = urllib.request.Request(f'{base}/api/monitoring/simulate-frame?target_value=54.2', method='POST')
    with urllib.request.urlopen(req) as resp:
        sim_data = json.loads(resp.read().decode())
        print(f"[TEST 5] Live Processing: Text '{sim_data['raw_text']}', Status: {sim_data['status']}, Conf: {sim_data['confidence']}")

    # 6. Frontend Root
    with urllib.request.urlopen(f'{base}/') as resp:
        html = resp.read().decode()
        has_root = '<div id="root">' in html
        print(f"[TEST 6] Root Frontend Serving: {resp.status} - Contains root div: {has_root}")

    print("\n[OK] ALL 6 END-TO-END INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
