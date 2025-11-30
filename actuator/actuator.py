import time, requests, os
from kubernetes import client, config

NAMESPACE = os.getenv("NAMESPACE", "autoscaler-demo")
DEPLOYMENT = os.getenv("DEPLOYMENT", "demo-app")
DECISION_URL = os.getenv("DECISION_URL", "http://decision.autoscaler-demo.svc/decide")
COOLDOWN = int(os.getenv("COOLDOWN", "60"))  # secs
SIMULATE = os.getenv("SIMULATE", "true").lower() == "true"

# in-cluster or local kubeconfig
try:
    config.load_incluster_config()
except:
    config.load_kube_config()
apps = client.AppsV1Api()

last_action = 0

def get_current_replicas():
    dep = apps.read_namespaced_deployment(name=DEPLOYMENT, namespace=NAMESPACE)
    return dep.spec.replicas

def apply_scale(replicas):
    body = {'spec': {'replicas': int(replicas)}}
    apps.patch_namespaced_deployment_scale(name=DEPLOYMENT, namespace=NAMESPACE, body=body)

while True:
    try:
        r = requests.post(DECISION_URL, timeout=5)
        rec = r.json().get('recommended_replicas')
        if rec is None:
            print("[ACTUATOR] No recommendation:", r.text)
        else:
            now = time.time()
            cur = get_current_replicas()
            if rec != cur and (now - last_action) > COOLDOWN:
                print(f"[ACTUATOR] Recommendation {rec}, current {cur}")
                if SIMULATE:
                    print("[SIMULATE] Would scale to", rec)
                else:
                    apply_scale(rec)
                    print("Scaled to", rec)
                last_action = now
            else:
                print("[ACTUATOR] No action needed (or cooldown) rec", rec, "cur", cur)
    except Exception as e:
        print("[ACTUATOR] Error in actuator loop:", e)
    time.sleep(10)
