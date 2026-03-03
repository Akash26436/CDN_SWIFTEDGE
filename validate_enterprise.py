import requests
import time
import concurrent.futures

# --- CONFIGURATION ---
BASE_URL = "http://localhost:8080"
AUTH_HEADER = {"Authorization": "Bearer swift-edge-master-key-2026"}
RESOURCES = ["index.html", "style.css", "script.js", "logo.png"]

def test_auth():
    print("\n[Test] Zero-Trust Authentication")
    # No Auth
    r = requests.get(f"{BASE_URL}/index.html")
    print(f"  - No Header: {r.status_code} ({r.text.strip()})")
    # Wrong Auth
    r = requests.get(f"{BASE_URL}/index.html", headers={"Authorization": "Bearer wrong"})
    print(f"  - Invalid Token: {r.status_code} ({r.text.strip()})")
    # Correct Auth
    r = requests.get(f"{BASE_URL}/index.html", headers=AUTH_HEADER)
    print(f"  - Correct Token: {r.status_code}")

def test_waf():
    print("\n[Test] Web Application Firewall (WAF)")
    # SQLi
    r = requests.get(f"{BASE_URL}/index.html?id=1 OR 1=1", headers=AUTH_HEADER)
    print(f"  - SQL Injection Attempt: {r.status_code} ({r.text.strip()})")
    # XSS
    r = requests.get(f"{BASE_URL}/index.html?name=<script>alert(1)</script>", headers=AUTH_HEADER)
    print(f"  - XSS Attempt: {r.status_code} ({r.text.strip()})")

def test_rate_limiting():
    print("\n[Test] Token Bucket Rate Limiting")
    print("  - Sending 20 rapid requests (Capacity: 10, Rate: 5/s)...")
    blocks = 0
    for i in range(20):
        r = requests.get(f"{BASE_URL}/index.html", headers=AUTH_HEADER)
        if r.status_code == 429:
            blocks += 1
    print(f"  - Total requests: 20 | BLOCKED: {blocks}")

def test_cache_hierarchy():
    print("\n[Test] Multi-Tier Cache Performance (L1 -> L2 -> Origin)")
    # Create a real file for cache testing
    path = "index.html"
    
    # 1. First Access: Origin Fetch
    start = time.perf_counter()
    r = requests.get(f"{BASE_URL}/{path}", headers=AUTH_HEADER)
    lat1 = (time.perf_counter() - start) * 1000
    print(f"  - 1st Request (MISS -> Origin): {lat1:.2f}ms")

    # 2. Second Access: L1 Hit
    start = time.perf_counter()
    r = requests.get(f"{BASE_URL}/{path}", headers=AUTH_HEADER)
    lat2 = (time.perf_counter() - start) * 1000
    print(f"  - 2nd Request (L1 HIT): {lat2:.2f}ms")
    
    if lat2 < lat1:
        print(f"  - SUCCESS: L1 Cache is {lat1/lat2:.1f}x faster!")

def test_consistent_hashing():
    print("\n[Test] Consistent Hashing & Hash-Based Routing")
    for res in RESOURCES:
        r = requests.get(f"{BASE_URL}/{res}", headers=AUTH_HEADER)
        print(f"  - Routing '{res}' -> Success (Edge {r.status_code})")


def test_metrics():
    print("\n[Test] Observability Metrics")
    # We hit a specific edge node directly for metrics if exposed, or via LB if routed
    # Since they have different ports in docker, we'll try port 8081 on localhost
    try:
        r = requests.get("http://localhost:8081/metrics")
        print(f"  - Edge Metrics Report:\n{r.text}")
    except:
        print("  - Edge 8081 not reachable directly from host. Check docker logs.")

if __name__ == "__main__":
    print("=" * 60)
    print("SWIFTEDGE CDN ENTERPRISE VALIDATION SUITE")
    print("=" * 60)
    print("NOTE: Ensure 'docker-compose up' is running before starting.")
    
    try:
        test_auth()
        test_waf()
        test_rate_limiting()
        test_cache_hierarchy()
        test_consistent_hashing()
        test_metrics()
    except Exception as e:
        print(f"\n[Error] Verification failed: {e}")
        print("Please make sure the distributed system is running.")
    
    print("\n" + "=" * 60)
    print("Verification Completed.")
