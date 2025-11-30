from flask import Flask
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import time, random

app = Flask(__name__)
REQS = Counter('demo_requests_total', 'Total requests')

@app.route('/')
def home():
    REQS.inc()
    # simulate a bit of work
    time.sleep(random.uniform(0.01, 0.08))
    return "OK", 200

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
