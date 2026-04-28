# 📈 PredictiveScale

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Minikube-326ce5?logo=kubernetes)
![Docker](https://img.shields.io/badge/Docker-Build-2496ed?logo=docker)
![License](https://img.shields.io/badge/License-MIT-green)

**PredictiveScale** is a local, open-source predictive autoscaler for Kubernetes.

It demonstrates a complete cloud-native pipeline that **predicts incoming traffic** using a Machine Learning model (Random Forest) and **proactively scales** a Kubernetes deployment to optimize performance and cost. The entire system runs locally (free) on **Minikube** and uses **Prometheus** + **Grafana** for observability.

---

## 📖 Table of Contents
- [Overview](#-overview)
- [Architecture](#-architecture)
- [Use Cases](#-why-is-this-useful--use-cases)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Quick Start Guide](#-quick-start-guide)
- [How to Test & Demo](#-how-to-test--demo)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Overview
Traditional autoscalers (like HPA) react *after* a load spike occurs (reactive). **PredictiveScale** anticipates the spike (proactive).

1.  **Collects** request metrics from a demo web service using Prometheus.
2.  **Predicts** short-term RPS (`predicted_rps`) using a Random Forest model trained on synthetic data.
3.  **Decides** the optimal replica count via a dedicated Decision Engine.
4.  **Actuates** scaling by patching the Kubernetes Deployment.
5.  **Visualizes** everything (Traffic, Latency, Cost) on Grafana.

**💡 Cost Estimator Included:** The project includes a tool that simulates cost savings in Rupees (₹), comparing static provisioning vs. predictive autoscaling.

---

## 🏗 Architecture

```mermaid
graph LR
    User((User Traffic)) --> App[Demo App]
    App -->|Scrape Metrics| Prom[Prometheus]
    Prom -->|Query Metrics| Pred[Predictor Service]
    Pred -->|Predicted RPS| Dec[Decision Engine]
    Dec -->|Rec. Replicas| Act[Actuator Service]
    Act -->|Scale Command| K8s[Kubernetes API]
    K8s -->|Scale Up/Down| App
    
    subgraph Observability
    Prom <--> Grafana
    end
````

-----

## 🎯 Why is this useful / Use-cases

  - **Proactive Scaling:** Prevents latency spikes by scaling *before* load increases.
  - **Cost Optimization:** Aggressively scales down during low traffic windows.
  - **Educational Value:** Perfect for college projects, learning CI/CD, and understanding ML Ops.

**Real-world scenarios:**

  * 🎓 College event registration systems (predictable spikes).
  * 🛍️ E-commerce flash sales.
  * 📰 News sites or portfolios after a marketing push.

-----

## 🛠 Tech Stack

  * **Containerization:** Docker
  * **Orchestration:** Kubernetes (Minikube)
  * **Observability:** Prometheus, Grafana
  * **ML & Backend:** Python, Scikit-Learn, FastAPI
  * **Scripting:** Bash, Helm

-----

## 📋 Prerequisites

  * **OS:** Linux / Windows / macOS
  * **Hardware:** 4GB RAM minimum (8GB recommended)
  * **Tools:**
      * Docker (Engine or Desktop)
      * Minikube
      * `kubectl`
      * Helm
      * Python 3.8+ (for local training tools)

-----

## ⚡ Quick Start Guide

> **Note:** These steps assume you have the prerequisites installed.

### 1\. Start Minikube

```bash
minikube start --driver=docker --memory=8192 --cpus=4
kubectl create namespace autoscaler-demo
```

### 2\. Build & Load Images

Run these commands from the repository root to build Docker images and load them directly into the Minikube environment:

```bash
# 1. Build Demo App
docker build -t autoscaler-demo-app:0.1 ./app
minikube image load autoscaler-demo-app:0.1

# 2. Train Model & Build Predictor
cd predictor
python3 train.py   # Generates model.pkl
cd ..
docker build -t autoscaler-predictor:0.1 ./predictor
minikube image load autoscaler-predictor:0.1

# 3. Build Decision Engine
docker build -t autoscaler-decision:0.1 ./decision
minikube image load autoscaler-decision:0.1

# 4. Build Actuator
docker build -t autoscaler-actuator:0.1 ./actuator
minikube image load autoscaler-actuator:0.1
```

### 3\. Deploy Core Components

```bash
kubectl apply -f k8s/app-deploy.yaml
kubectl apply -f k8s/predictor.yaml
kubectl apply -f k8s/decision.yaml
kubectl apply -f k8s/actuator.yaml
```

### 4\. Install Observability Stack (Prometheus & Grafana)

We use the official Helm chart for the kube-prometheus-stack.

```bash
helm repo add prometheus-community [https://prometheus-community.github.io/helm-charts](https://prometheus-community.github.io/helm-charts)
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack --namespace autoscaler-demo --create-namespace

# Apply Service Monitors so Prometheus knows to scrape our apps
kubectl apply -f k8s/servicemonitor-demo.yaml
kubectl apply -f k8s/servicemonitor-predictor.yaml
```

### 5\. Configure Permissions (RBAC)

Allow the actuator service to modify kubernetes deployments:

```bash
kubectl apply -f k8s/actuator-rbac.yaml
kubectl -n autoscaler-demo patch deployment actuator --type='merge' -p '{"spec":{"template":{"spec":{"serviceAccountName":"actuator-sa"}}}}'
```

### 6\. Port Forwarding (Access UIs)

Open a new terminal to keep these running:

```bash
# Prometheus UI (localhost:9090)
kubectl -n autoscaler-demo port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 &

# Grafana UI (localhost:3000)
kubectl -n autoscaler-demo port-forward svc/prometheus-grafana 3000:80 &

# Demo App (localhost:8080)
kubectl -n autoscaler-demo port-forward svc/demo-app 8080:80 &

# Optional: Predictor & Decision APIs
kubectl -n autoscaler-demo port-forward svc/predictor 8000:80 &
kubectl -n autoscaler-demo port-forward svc/decision 8001:80 &
```

> **To get Grafana Password:**
> `kubectl -n autoscaler-demo get secret prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo`

-----

## 🧪 How to Test / Demo

### Step 1: Import Dashboard

1.  Log in to Grafana (`localhost:3000`).
2.  Go to **Dashboards** → **New** → **Import**.
3.  Upload `grafana/autoscaler-dashboard.json` from this repo.
4.  Select your Prometheus datasource.

### Step 2: Run the Simulation

Open 2 separate terminals:

**Terminal A: Watch Actuator Logs**

```bash
kubectl -n autoscaler-demo logs -l app=actuator -f
```

**Terminal B: Generate Load & Trigger Prediction**

```bash
# 1. Generate traffic load (simulate users)
for i in {1..200}; do curl -s http://localhost:8080/ > /dev/null; done

# 2. Trigger Prediction (Updates metrics)
curl -s http://localhost:8000/predict | jq .

# 3. Trigger Decision (Returns recommended replicas)
curl -s -X POST http://localhost:8001/decide | jq .
```

### Step 3: View Results

1.  **Grafana:** Watch the "Actual RPS" spike and "Predicted RPS" follow.
2.  **Logs:** Terminal A will show: `Recommendation: X, Current: Y, Scaling...`
3.  **K8s:** Run `kubectl get pods` to see new pods spinning up automatically.

### Step 4: Calculate Savings

Run the included cost estimator tool to see how much money this saves:

```bash
python3 tools/cost_estimator_rupee.py
```

*Output will show estimated cost in ₹ and % savings compared to static scaling.*

-----

## 📂 Project Structure

```text
autoscaler-project/
├── app/             # Demo Flask web app + Dockerfile
├── predictor/       # ML Model (RandomForest), Train script, FastAPI
├── decision/        # Logic engine (Prediction -> Replicas)
├── actuator/        # K8s Client script to apply scaling
├── k8s/             # Manifests, ServiceMonitors, RBAC
├── grafana/         # JSON Dashboard export
├── tools/           # Cost estimator script (Python)
└── README.md
```

-----

## 🔧 Troubleshooting

  * **`kubectl logs` are empty?**
      * Set `PYTHONUNBUFFERED=1` in the Dockerfile or deployment env vars to flush logs immediately.
  * **Predictor returns "Not enough data"?**
      * Wait 2–3 minutes for Prometheus to scrape enough data points.
  * **Actuator 403 Forbidden?**
      * Re-run the **RBAC** step in the Quick Start guide.
  * **Images not found (ErrImagePull)?**
      * Ensure you ran `minikube image load <image_name>` for every built image.

-----

## 📜 License

MIT License. Free to use for educational and personal projects.

**Author:** Abhishek V K

-----------------2025-------------------
