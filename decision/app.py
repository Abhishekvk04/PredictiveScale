from fastapi import FastAPI
import requests, math, os

app = FastAPI()

# Config via env
PREDICTOR_SVC = os.getenv("PREDICTOR_URL", "http://predictor.autoscaler-demo.svc")
PER_POD_CAPACITY = float(os.getenv("PER_POD_CAPACITY", "20.0"))
MIN_REPLICAS = int(os.getenv("MIN_REPLICAS", "1"))
MAX_REPLICAS = int(os.getenv("MAX_REPLICAS", "10"))
SAFETY_FACTOR = float(os.getenv("SAFETY_FACTOR", "1.2"))

@app.post("/decide")
def decide():
    try:
        r = requests.get(PREDICTOR_SVC + "/predict", timeout=5)
        j = r.json()
        pred = j.get('predicted_rps')
        if pred is None:
            return {"error": "no prediction", "raw": j}
        needed = math.ceil((pred * SAFETY_FACTOR) / PER_POD_CAPACITY)
        needed = max(MIN_REPLICAS, min(MAX_REPLICAS, needed))
        return {"predicted": pred, "recommended_replicas": int(needed)}
    except Exception as e:
        return {"error": str(e)}
