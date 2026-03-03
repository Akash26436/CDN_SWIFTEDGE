import socket
import threading
import time
import requests
import os
import hashlib
import random
from queue import Queue

# NOTE: This script bundles all logic to ensure it can run in a single-process 
# threaded environment since multi-process/docker had issues in the current terminal.

# --- CORE UTILS ---

class RateLimiter:
    def __init__(self, rate=10, capacity=20):
        self.rate = rate; self.capacity = capacity; self.tokens = capacity
        self.last_update = time.time(); self.lock = threading.Lock()
    def consume(self):
        with self.lock:
            now = time.time(); elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            if self.tokens >= 1: self.tokens -= 1; return True
            return False

class WAF:
    def __init__(self):
        self.rules = [(r"(?i)(OR|AND)\s+.*=.*", "SQLi"), (r"(?i)<script", "XSS")]
    def inspect(self, text):
        import re
        for p, r in self.rules:
            if re.search(p, text): return False, r
        return True, None

class SecurityManager:
    def __init__(self):
        self.limiters = {}; self.waf = WAF()
    def check(self, ip, payload):
        if ip not in self.limiters: self.limiters[ip] = RateLimiter(5, 10)
        if not self.limiters[ip].consume(): return False, "Rate Limit"
        safe, reason = self.waf.inspect(payload)
        if not safe: return False, f"WAF:{reason}"
        return True, "OK"

class EdgeCompute:
    def process_resp(self, data, headers):
        headers["X-Edge-Compute"] = "Active"
        return data.replace(b"CDN", b"SWIFT-CDN"), headers

# --- SERVERS ---

def run_origin(port):
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    httpd = HTTPServer(('127.0.0.1', port), SimpleHTTPRequestHandler)
    httpd.serve_forever()

class AdvancedEdge:
    def __init__(self, port, region):
        self.port = port; self.region = region; self.sec = SecurityManager(); self.comp = EdgeCompute()
    def handle(self, client, addr):
        try:
            raw = client.recv(4096)
            if not raw: return
            txt = raw.decode(errors='ignore')
            
            # Security
            ok, reason = self.sec.check(addr[0], txt)
            if not ok:
                client.sendall(f"HTTP/1.1 403 Forbidden\r\n\r\nBlocked: {reason}".encode())
                return
            
            # Zero Trust
            if "X-Auth: secure123" not in txt:
                client.sendall(b"HTTP/1.1 401 Unauthorized\r\n\r\nMissing Token")
                return

            # Proxy to Origin (simulated)
            resp = requests.get("http://127.0.0.1:8001/index.html")
            data, headers = self.comp.process_resp(resp.content, {"Content-Type": "text/html"})
            
            res = "HTTP/1.1 200 OK\r\n"
            for k,v in headers.items(): res += f"{k}: {v}\r\n"
            client.sendall(res.encode() + b"\r\n" + data)
        finally: client.close()
    
    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', self.port))
        s.listen(5)
        while True:
            c, a = s.accept()
            threading.Thread(target=self.handle, args=(c,a)).start()

def run_lb(port, edges):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', port))
    s.listen(10)
    print(f"[LB] Ready on {port}")
    while True:
        c, a = s.accept()
        raw = c.recv(4096)
        # Latency-based selective routing
        best = min(edges, key=lambda x: x['lat'] + random.randint(-2,2))
        print(f"[LB] Routing to {best['port']} ({best['reg']}) - Latency: {best['lat']}ms")
        e = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        e.connect(('127.0.0.1', best['port']))
        e.sendall(raw)
        c.sendall(e.recv(8192))
        e.close(); c.close()

if __name__ == '__main__':
    if not os.path.exists('origin'): os.makedirs('origin')
    with open('origin/index.html', 'w') as f: f.write("<h1>CDN Origin Content</h1>")
    
    threading.Thread(target=run_origin, args=(8001,), daemon=True).start()
    
    configs = [{'p': 8081, 'r': 'US'}, {'p': 8082, 'r': 'EU'}, {'p': 8083, 'r': 'ASIA'}]
    for c in configs:
        e = AdvancedEdge(c['p'], c['r'])
        threading.Thread(target=e.start, daemon=True).start()
    
    edges = [{'port': 8081, 'reg': 'US', 'lat': 10}, {'port': 8082, 'reg': 'EU', 'lat': 50}, {'port': 8083, 'reg': 'ASIA', 'lat': 150}]
    threading.Thread(target=run_load_balancer if False else run_lb, args=(8080, edges), daemon=True).start()
    
    time.sleep(2)
    print("\n--- Phase 1: Zero-Trust Verification ---")
    r = requests.get("http://127.0.0.1:8080/index.html")
    print(f"No Token: {r.status_code} ({r.text})")
    
    print("\n--- Phase 2: Security & Edge Compute Verification ---")
    r = requests.get("http://127.0.0.1:8080/index.html", headers={"X-Auth": "secure123"})
    print(f"With Token: {r.status_code}")
    print(f"Headers: {r.headers.get('X-Edge-Compute')}")
    print(f"Body: {r.text[:50]}")

    print("\n--- Phase 3: WAF Attack Simulation ---")
    r = requests.get("http://127.0.0.1:8080/index.html?q=' OR 1=1 --", headers={"X-Auth": "secure123"})
    print(f"Attack Result: {r.status_code} ({r.text})")

    print("\n--- Phase 4: DDoS / Rate Limit Simulation ---")
    for i in range(10):
        r = requests.get("http://127.0.0.1:8080/", headers={"X-Auth": "secure123"})
        if r.status_code == 403: print(f"Request {i}: Blocked by Rate Limiter")
    
    print("\nFull Advanced CDN Demo Complete.")
