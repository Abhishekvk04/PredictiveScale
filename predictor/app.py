# FastAPI predictor: queries Prometheus for recent rates, predicts next rps,
# exposes /predict and /metrics (predicted_rps gauge)
import os
import time
import pickle
import requests
import numpy as np
from fastapi import FastAPI
from prometheus_client import Gauge, make_asgi_app
from starlette.middleware.wsgi import WSGIMiddleware

MODEL_PATH = os.getenv("MODEL_PATH", "/app/model.pkl")
PROM_URL = os.getenv("PROM_URL", "http://prometheus-kube-prometheus-prometheus.autoscaler-demo.svc:9090")
PULL_N = int(os.getenv("PULL_N", "10"))

app = FastAPI()
# load model
model = pickle.load(open(MODEL_PATH, "rb"))

# Prometheus metric
pred_gauge = Gauge('predicted_rps', 'Predicted requests per second by predictor')

# Mount prometheus_client's WSGI app at /metrics
from prometheus_client import make_wsgi_app
app.mount("/metrics", WSGIMiddleware(make_wsgi_app()))

def fetch_last_rates(n=PULL_N):
    # Query range for the last ~n minutes with step 15s to get many points
    # Simpler: use instant vector rate over 1m; however we need a sequence of last n samples
    # We'll use query_range for rate(demo_requests_total[1m]) over the last (n*15s)
    step = "15s"
    seconds = n * 15
    end = int(time.time())
    start = end - seconds
    query = 'rate(demo_requests_total[1m])'
    params = {
        "query": query,
        "start": start,
        "end": end,
        "step": step
    }
    try:
        r = requests.get(f"{PROM_URL}/api/v1/query_range", params=params, timeout=5)
        r.raise_for_status()
        data = r.json()
        vals = []
        if data.get('data', {}).get('result'):
            values = data['data']['result'][0]['values']  # list of [timestamp, value]
            vals = [float(v[1]) for v in values]
        return vals
    except Exception as e:
        print("Error fetching rates:", e)
        return []

@app.get("/predict")
def predict():
    vals = fetch_last_rates()
    if len(vals) < PULL_N:
        return {"error": "not enough data", "have": len(vals), "need": PULL_N}
    # use last PULL_N values as lag features (ensure order newest last)
    X = np.array(vals[-PULL_N:]).reshape(1, -1)
    pred = float(model.predict(X)[0])
    pred = max(0.0, pred)  # no negative
    pred_gauge.set(pred)
    return {"predicted_rps": pred, "used_points": len(vals)}

@app.get("/")
def home():
    return {"ok": True}
