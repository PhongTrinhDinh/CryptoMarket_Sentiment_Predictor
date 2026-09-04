import sys
from pathlib import Path
from fastapi.testclient import TestClient

FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from apps.api.main import app

def test_predict_endpoint():
    with TestClient(app) as client:
        response = client.get("/predict?symbol=BTC/USDT&entity=BTC")
        
        assert response.status_code in [200, 503], f"Unexpected status code: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "symbol" in data
            assert data["symbol"] == "BTC/USDT"
            assert "prediction" in data
            assert data["prediction"] in [-1, 0, 1]
            assert "label" in data
            assert data["label"] in ["Down", "Sideways", "Up"]
            assert "probabilities" in data
            assert "timestamp" in data
            
            probs = data["probabilities"]
            assert "down" in probs
            assert "sideways" in probs
            assert "up" in probs
            
            # Check if sum of probabilities is approx 1
            total_prob = probs["down"] + probs["sideways"] + probs["up"]
            assert abs(total_prob - 1.0) < 1e-4

if __name__ == "__main__":
    test_predict_endpoint()
    print("All tests passed (or model not yet loaded).")
