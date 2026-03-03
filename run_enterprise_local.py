import subprocess
import time
import os
import sys

def run():
    print("=" * 60)
    print("SWIFTEDGE ENTERPRISE: LOCAL DISTRIBUTED ORCHESTRATOR")
    print("=" * 60)

    # 1. Start Origin
    if not os.path.exists('origin'): os.makedirs('origin')
    with open('origin/index.html', 'w') as f: f.write("<html><body>Enterprise Origin Content</body></html>")
    with open('origin/style.css', 'w') as f: f.write("body { background: #f0f0f0; }")
    with open('origin/script.js', 'w') as f: f.write("console.log('SwiftEdge Active');")
    with open('origin/logo.png', 'w') as f: f.write("FAKE_IMAGE_DATA")
    origin = subprocess.Popen([sys.executable, "-m", "http.server", "8001"], cwd="origin")

    print("[System] Origin Server started at port 8001")

    # 2. Start Edge Cluster
    edges = []
    ports = [8081, 8082, 8083]
    for p in ports:
        proc = subprocess.Popen([sys.executable, "edge/edge_server.py", "--port", str(p), "--origin", "http://127.0.0.1:8001"])
        edges.append(proc)
        print(f"[System] Edge Node started at port {p}")

    # 3. Start Load Balancer
    # We set the env var so it knows to use localhost
    os.environ["EDGE_NODES"] = "127.0.0.1:8081,127.0.0.1:8082,127.0.0.1:8083"
    lb = subprocess.Popen([sys.executable, "load_balancer.py"])
    print("[System] Load Balancer started at port 8080")

    time.sleep(3) # Wait for bootstrap

    # 4. Run Validation Suite
    try:
        subprocess.run([sys.executable, "validate_enterprise.py"])
    finally:
        print("\n" + "=" * 60)
        print("Stopping Enterprise Cluster...")
        lb.terminate()
        for e in edges: e.terminate()
        origin.terminate()
        print("System stopped.")

if __name__ == "__main__":
    run()
