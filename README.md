# PredictiveScale

**PredictiveScale** — a local, open-source predictive autoscaler for Kubernetes.  
It demonstrates a complete cloud-native pipeline that **predicts incoming traffic** using a simple ML model and **proactively scales** a Kubernetes deployment to optimize performance and cost. The entire system runs locally (free) on **Minikube** and uses **Prometheus** + **Grafana** for observability.

---

## TL;DR — What this project does
- Collects request metrics from a demo web service using Prometheus.  
- Uses a Random Forest model (trained on synthetic data) to predict short-term RPS (`predicted_rps`).  
- Decision service converts prediction → recommended replicas.  
- Actuator service patches the Kubernetes Deployment to scale up/down.  
- Grafana visualizes Actual vs Predicted traffic, replica count, latency, and cost.  
- Includes a cost estimator that simulates ₹ savings.

This repo is **fully free** to run locally — no cloud account required.

---

## Why this is useful / Use-cases
- Prevents latency spikes by scaling *before* load increases (proactive scaling).  
- Reduces running cost by scaling down during low traffic.  
- Useful for college projects, demos, teaching CI/CD & observability, and prototyping ML-driven autoscaling logic for production systems.

Example use-cases:
- College event registration systems (sudden spikes)  
- E-commerce sale-day pre-scaling  
- Personal websites/portfolio that see traffic spikes when promoted

---

## Repo structure
autoscaler-project/
├── app/ # demo web app (Flask) + Dockerfile
├── predictor/ # train.py, predictor FastAPI server, Dockerfile, model.pkl
├── decision/ # decision engine FastAPI server, Dockerfile
├── actuator/ # actuator script + Dockerfile
├── k8s/ # kubernetes manifests, ServiceMonitors, RBAC, poller
├── grafana/ # autoscaler-dashboard.json
├── tools/ # cost estimator (cost_estimator_rupee.py)
└── README.md


---

## High-level architecture
User Traffic --> demo-app --> Prometheus --> Predictor --> Decision --> Actuator --> Kubernetes API (scale)
↘
Grafana (visualize actual + predicted + replicas + cost)


---

## Prerequisites (local, free)
- Linux/Windows/macOS with >=4 GB RAM (8 GB recommended)  
- Docker (Engine or Docker Desktop)  
- Minikube  
- kubectl  
- Helm  
- Python 3.8+ (for local tools & training)  
- (Optional) jq for CLI JSON parsing

---

## Quick start (copy & paste)

> These instructions assume you are on Linux Mint / Ubuntu and have Docker, kubectl, minikube, helm installed. If you followed earlier steps while building the project, you likely already have everything set.

1. Start minikube:
```bash
minikube start --driver=docker --memory=8192 --cpus=4
kubectl create namespace autoscaler-demo
```

2. Build images and load to minikube (from repository root):
```bash
# demo app
docker build -t autoscaler-demo-app:0.1 ./app
minikube image load autoscaler-demo-app:0.1

# predictor (train model first)
cd predictor
python3 train.py   # creates model.pkl
cd ..
docker build -t autoscaler-predictor:0.1 ./predictor
minikube image load autoscaler-predictor:0.1

# decision
docker build -t autoscaler-decision:0.1 ./decision
minikube image load autoscaler-decision:0.1

# actuator
docker build -t autoscaler-actuator:0.1 ./actuator
minikube image load autoscaler-actuator:0.1
```

3. Deploy the core components:
```bash

kubectl apply -f k8s/app-deploy.yaml
kubectl apply -f k8s/predictor.yaml
kubectl apply -f k8s/decision.yaml
kubectl apply -f k8s/actuator.yaml
```


4. Install Prometheus + Grafana (kube-prometheus-stack):
```bash

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack --namespace autoscaler-demo --create-namespace
```

5. Add ServiceMonitors so Prometheus scrapes demo-app and predictor:
```bash

kubectl apply -f k8s/servicemonitor-demo.yaml
kubectl apply -f k8s/servicemonitor-predictor.yaml
```

6. Give actuator RBAC permission (so it can scale safely):
```bash
kubectl apply -f k8s/actuator-rbac.yaml
kubectl -n autoscaler-demo patch deployment actuator --type='merge' -p '{"spec":{"template":{"spec":{"serviceAccountName":"actuator-sa"}}}}'
```

7. Port-forward for local testing:
```bash
# Prometheus UI
kubectl -n autoscaler-demo port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 &

# Grafana UI
kubectl -n autoscaler-demo port-forward svc/prometheus-grafana 3000:80 &
# Get Grafana admin password:
kubectl -n autoscaler-demo get secret prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo

# demo app
kubectl -n autoscaler-demo port-forward svc/demo-app 8080:80 &

# predictor & decision (optional)
kubectl -n autoscaler-demo port-forward svc/predictor 8000:80 &
kubectl -n autoscaler-demo port-forward svc/decision 8001:80 &
```

8. (Optional) Import Grafana dashboard:

In Grafana → Manage → Import → upload grafana/autoscaler-dashboard.json.

Replace datasource with your Prometheus datasource (usually Prometheus).

### How to test / demo (simple script)

Open 3 terminals:

Terminal A: Grafana (browser)

Terminal B: Tail actuator logs
```bash
kubectl -n autoscaler-demo logs -l app=actuator -f
```

Terminal C: Run load & trigger predict/decide
```bash
# generate quick load
for i in {1..200}; do curl -s http://localhost:8080/ > /dev/null; done

# call predictor (sets predicted_rps gauge)
curl -s http://localhost:8000/predict | jq .

# call decision (returns recommended replicas)
curl -s -X POST http://localhost:8001/decide | jq .

```

Expected behavior:

Grafana shows actual RPS increasing

Predictor writes predicted_rps metric

Decision returns recommended replicas

Actuator logs show Recommendation X, current Y and scales (if SIMULATE=false and RBAC in place)

Cost estimator shows cost & savings

Cost estimator (Rupees)

A local script is included: tools/cost_estimator_rupee.py

Run with Prometheus port-forwarded:
```bash
kubectl -n autoscaler-demo port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 &
python3 tools/cost_estimator_rupee.py
```

This prints:

Actual pod-hours used in the last 15 minutes

Estimated cost in ₹

A before/after simulation (6 pods always vs adaptive 2 pods) and % savings.

Note: This is simulated cost — you set the COST_PER_POD_HOUR parameter to express currency/scale.

Key design choices & reasons

RandomForest for prediction — robust, fast, works with small/noisy datasets and is easy to explain.

FastAPI for microservices — lightweight, performant, async-ready, and common for ML inference.

Prometheus to collect runtime metrics and be the single source of truth.

Grafana to visualize actual vs predicted, replicas, latency, and cost.

Actuator as separate service for clear separation of concerns (decision vs action).

Extending / Customization

Use Locust for realistic traffic patterns. Add a load/ folder with locustfile for demo.

Replace RandomForest with LSTM/Prophet for longer horizon forecasting.

Deploy to real cloud (EKS/GKE) — note: cloud deployment will incur cost.

Add a Prometheus exporter for custom metrics (latency buckets, error rates).

Automate /predict calls with k8s/predict-loop.yaml (simple poller Deployment).

Connecting a real website

Yes if you control the website and can add a /metrics endpoint in Prometheus format.

If you cannot modify the website, build a thin proxy/exporter that requests the target site and exposes Prometheus metrics (latency, success rate).