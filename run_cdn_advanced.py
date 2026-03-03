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

# --- COMPONENTS ---

class Node:
    def __init__(self, key, value):
        self.key = key; self.value = value; self.prev = None; self.next = None

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity; self.cache = {}; self.lock = threading.Lock()
        self.head = Node(0,0); self.tail = Node(0,0); self.head.next = self.tail; self.tail.prev = self.head
    def _remove(self, node): node.prev.next = node.next; node.next.prev = node.prev
    def _add(self, node): node.next = self.head.next; node.prev = self.head; self.head.next.prev = node; self.head.next = node
    def get(self, key):
        with self.lock:
            if key in self.cache: node = self.cache[key]; self._remove(node); self._add(node); return node.value
            return None
    def put(self, key, value):
        with self.lock:
            if key in self.cache: self._remove(self.cache[key])
            node = Node(key, value); self._add(node); self.cache[key] = node
            if len(self.cache) > self.capacity: lru = self.tail.prev; self._remove(lru); del self.cache[lru.key]

class DiskCache:
    def __init__(self, dir_name):
        self.dir = dir_name; self.ttl = 60
        if not os.path.exists(self.dir): os.makedirs(self.dir)
    def path_for(self, key): return os.path.join(self.dir, key.replace('/', '_'))
    def get(self, key):
        path = self.path_for(key)
        if not os.path.exists(path) or time.time() - os.path.getmtime(path) > self.ttl: return None
        with open(path, 'rb') as f: return f.read()
    def put(self, key, data):
        with open(self.path_for(key), 'wb') as f: f.write(data)

class Metrics:
    def __init__(self):
        self.lock = threading.Lock(); self.total = 0; self.hits = 0; self.misses = 0
    def request(self): 
        with self.lock: self.total += 1
    def hit(self): 
        with self.lock: self.hits += 1
    def miss(self): 
        with self.lock: self.misses += 1
    def report(self):
        with self.lock: 
            ratio = self.hits/self.total if self.total else 0
            return f"Total:{self.total} Hits:{self.hits} Misses:{self.misses} HitRatio:{ratio:.2f}"

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
        return data.replace(b"Origin", b"SWIFT-EDGE-CDN"), headers

# --- SERVERS ---

def run_origin(port):
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    httpd = HTTPServer(('127.0.0.1', port), SimpleHTTPRequestHandler)
    httpd.serve_forever()

class AdvancedEdge:
    def __init__(self, port, region):
        self.port = port; self.region = region
        self.sec = SecurityManager(); self.comp = EdgeCompute()
        self.mem_cache = LRUCache(50); self.disk_cache = DiskCache(f"unified_disk_cache_{port}")
        self.metrics = Metrics()
    
    def handle(self, client, addr):
        try:
            raw = client.recv(4096)
            if not raw: return
            txt = raw.decode(errors='ignore')
            lines = txt.split('\r\n')
            parts = lines[0].split(' ')
            if len(parts) < 2: return
            path = parts[1]
            key = path.strip('/') or 'index.html'

            # Security Check
            ok, reason = self.sec.check(addr[0], txt)
            if not ok:
                client.sendall(f"HTTP/1.1 403 Forbidden\r\n\r\nBlocked: {reason}".encode())
                return
            
            # Zero Trust Check
            if "X-Auth: secure123" not in txt:
                client.sendall(b"HTTP/1.1 401 Unauthorized\r\n\r\nMissing Token")
                return

            self.metrics.request()

            # 1. Check Memory Cache
            data = self.mem_cache.get(key)
            if data:
                print(f"[Edge {self.port}] Memory HIT: {key}")
                self.metrics.hit()
            else:
                # 2. Check Disk Cache
                data = self.disk_cache.get(key)
                if data:
                    print(f"[Edge {self.port}] Disk HIT: {key}")
                    self.metrics.hit()
                    self.mem_cache.put(key, data)
                else:
                    # 3. Fetch from Origin
                    print(f"[Edge {self.port}] MISS: {key} -> Fetching from Origin")
                    self.metrics.miss()
                    resp = requests.get("http://127.0.0.1:8001/index.html")
                    data = resp.content
                    self.disk_cache.put(key, data)
                    self.mem_cache.put(key, data)

            # Edge Compute (Response)
            data, headers = self.comp.process_resp(data, {"Content-Type": "text/html"})
            
            res = "HTTP/1.1 200 OK\r\n"
            for k,v in headers.items(): res += f"{k}: {v}\r\n"
            client.sendall(res.encode() + b"\r\n" + data)
        except Exception as e:
            print(f"[Edge {self.port}] Error: {e}")
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
    
    time.sleep(5)
    
    def safe_get(url, headers=None, params=None):
        for _ in range(3):
            try: return requests.get(url, headers=headers, params=params, timeout=5)
            except: time.sleep(1)
        return None

    print("\n--- Phase 1: Zero-Trust Verification ---")
    r = safe_get("http://127.0.0.1:8080/index.html")
    if r: print(f"No Token Result: {r.status_code} ({r.text})")

    
    print("\n--- Phase 2: Security & Edge Compute Verification ---")
    r = safe_get("http://127.0.0.1:8080/index.html", headers={"X-Auth": "secure123"})
    if r:
        print(f"With Token: {r.status_code}")
        print(f"Headers: {r.headers.get('X-Edge-Compute')}")
        print(f"Body: {r.text[:50]}")

    print("\n--- Phase 3: Cache Hit Verification ---")
    print("Requesting same file again to verify HIT (check logs above)...")
    r = safe_get("http://127.0.0.1:8080/index.html", headers={"X-Auth": "secure123"})
    
    print("\n--- Phase 4: WAF Attack Simulation ---")
    r = safe_get("http://127.0.0.1:8080/index.html?q=' OR 1=1 --", headers={"X-Auth": "secure123"})
    if r: print(f"Attack Result: {r.status_code} ({r.text})")

    print("\n--- Phase 5: DDoS / Rate Limit Simulation ---")
    for i in range(12):
        r = safe_get("http://127.0.0.1:8080/", headers={"X-Auth": "secure123"})
        if r and r.status_code == 403: 
            print(f"Request {i}: Blocked by Rate Limiter")
            break
    
    print("\nFull Advanced CDN Demo Complete. Check logs for Memory/Disk HIT/MISS details.")

