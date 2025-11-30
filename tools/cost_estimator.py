import requests
import time

# Prometheus endpoint (port-forwarding enabled)
PROM = "http://localhost:9090"

# Your deployment details
DEPLOY = "demo-app"
NAMESPACE = "autoscaler-demo"

# Cost settings (In Rupees)
COST_PER_POD_HOUR = 0.50     # 50 paise per pod-hour

def query_replicas_range(seconds=900, step="15s"):
    """
    Query number of running pods (replicas) from Prometheus for last N seconds.
    """
    end = int(time.time())
    start = end - seconds
    query = f'kube_deployment_status_replicas{{deployment="{DEPLOY}",namespace="{NAMESPACE}"}}'

    r = requests.get(
        f"{PROM}/api/v1/query_range",
        params={"query": query, "start": start, "end": end, "step": step},
    )
    data = r.json()

    if not data["data"]["result"]:
        return []

    # [(timestamp, replica_count), ...]
    return [(float(ts), float(val)) for ts, val in data["data"]["result"][0]["values"]]


def calculate_cost(data_points):
    """
    Calculate cost using trapezoidal integration on time-series pod counts.
    """

    if len(data_points) < 2:
        return 0.0

    total_pod_seconds = 0.0

    for i in range(1, len(data_points)):
        t0, v0 = data_points[i - 1]
        t1, v1 = data_points[i]
        dt = t1 - t0          # time difference in seconds
        avg_pods = (v0 + v1) / 2.0
        total_pod_seconds += avg_pods * dt

    # Convert pod-seconds → pod-hours → ₹
    pod_hours = total_pod_seconds / 3600
    cost_rupees = pod_hours * COST_PER_POD_HOUR

    return pod_hours, cost_rupees


def simulate_before_after(before_pods, after_pods, seconds=900):
    """
    Simulate hypothetical before/after pod hours for comparison.
    """
    before_pod_hours = (before_pods * seconds) / 3600
    after_pod_hours = (after_pods * seconds) / 3600

    before_cost = before_pod_hours * COST_PER_POD_HOUR
    after_cost = after_pod_hours * COST_PER_POD_HOUR

    savings = before_cost - after_cost
    percent = (savings / before_cost * 100) if before_cost > 0 else 0

    return before_cost, after_cost, savings, percent


if __name__ == "__main__":
    print("\n=== Predictive Autoscaler Cost Analysis (₹ Rupees) ===\n")

    print("Fetching replica history from Prometheus...")
    data_points = query_replicas_range(seconds=900)  # last 15 minutes

    pod_hours, actual_cost = calculate_cost(data_points)

    print(f"\nActual pod-hours consumed in last 15 minutes: {pod_hours:.4f} pod-hours")
    print(f"Actual estimated cost (₹): {actual_cost:.4f}\n")

    # Example before-after comparison
    print("=== Before vs After Autoscaling (Simulation) ===\n")

    before_cost, after_cost, savings, percent = simulate_before_after(
        before_pods=6,   # what it would cost if you always used 6 pods
        after_pods=2,    # your autoscaler reduces to 2 during low load
        seconds=900      # 15 minutes
    )

    print(f"Cost without autoscaler (6 pods always): ₹{before_cost:.4f}")
    print(f"Cost with autoscaler (adaptive 2 pods): ₹{after_cost:.4f}")

    print(f"\nSavings: ₹{savings:.4f} ({percent:.2f}%)\n")
    print("==================================================\n")
