import socket
import threading
import time
import requests
import os
import random
import zlib
from queue import Queue

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

# --- SOLUTION ARCHITECTURE: CORE ENGINES ---

class PointOfPresence:
    """
    Represents a Global Edge Node (POP).
    Contains: Optimized Caching, WAF, and Rate Limiting.
    """
    def __init__(self, port, region, capacity=50):
        self.port = port
        self.region = region
        self.cache = OptimizedCacheEngine(port, capacity)
        self.security = EdgeSecurityLayer()
        self.is_active = True

    def handle_request(self, conn, addr):
        try:
            raw = conn.recv(4096)
            if not raw: return
            request_text = raw.decode(errors='ignore')
            
            # 1. Edge Security Layer (WAF + Auth + Rate Limiting)
            safe, reason = self.security.inspect(addr[0], request_text)

            if not safe:
                conn.sendall(f"HTTP/1.1 403 Forbidden\r\n\r\nCDN Security Alert: {reason}".encode())
                return

            # 2. Optimized Cache Lookup
            path = request_text.split(' ')[1].strip('/') or 'index.html'
            data, status, lat_int = self.cache.get(path)
            
            # 3. Upstream Origin Fetch (On Cache MISS)
            if status == "MISS":
                # Simulated Upstream Fetch
                resp = requests.get("http://127.0.0.1:8001/index.html")
                data = resp.content
                self.cache.store(path, data)
            
            # 4. Downstream Response delivery
            headers = {
                "Server": f"SwiftEdge-POP-{self.region}",
                "X-Cache": status,
                "X-Edge-Latency": f"{lat_int:.3f}ms",
                "Content-Type": "text/html"
            }
            res = "HTTP/1.1 200 OK\r\n"
            for k,v in headers.items(): res += f"{k}: {v}\r\n"
            conn.sendall(res.encode() + b"\r\n" + data)
        except Exception as e:
            print(f"[POP {self.region}] Runtime Error: {e}")
        finally:
            conn.close()

    def start_service(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', self.port))
        s.listen(10)
        while self.is_active:
            conn, addr = s.accept()
            threading.Thread(target=self.handle_request, args=(conn, addr)).start()

class OptimizedCacheEngine:
    def __init__(self, port, mem_cap):
        self.dir = f"v3_persistent_cache_{port}"
        self.mem = {} # Key -> (data, time, hits)
        self.capacity = mem_cap
        if not os.path.exists(self.dir): os.makedirs(self.dir)

    def get(self, key):
        start = time.perf_counter()
        if key in self.mem:
            data, _, hits = self.mem[key]
            self.mem[key] = (data, time.time(), hits + 1)
            return data, "L1_HIT", (time.perf_counter() - start) * 1000
        
        path = os.path.join(self.dir, key.replace('/', '_'))
        if os.path.exists(path):
            with open(path, 'rb') as f: data = zlib.decompress(f.read())
            self.store_l1(key, data)
            return data, "L2_HIT", (time.perf_counter() - start) * 1000
        
        return None, "MISS", (time.perf_counter() - start) * 1000

    def store_l1(self, key, data):
        if len(self.mem) >= self.capacity:
            victim = min(self.mem.keys(), key=lambda k: self.mem[k][2]) # LFU
            del self.mem[victim]
        self.mem[key] = (data, time.time(), 1)

    def store(self, key, data):
        self.store_l1(key, data)
        path = os.path.join(self.dir, key.replace('/', '_'))
        with open(path, 'wb') as f: f.write(zlib.compress(data))

class EdgeSecurityLayer:
    def __init__(self):
        self.limiter = RateLimiter(rate=2, capacity=5) # Realistic tight limit for demo

    def inspect(self, addr, txt):
        # 1. Zero-Trust Check
        if "X-Auth: secure123" not in txt: return False, "Missing Zero-Trust Token"
        
        # 2. DDoS / Rate Limit Check
        if not self.limiter.consume(): return False, "Rate Limit Exceeded (DDoS Protection)"
        
        # 3. WAF Check
        if "OR 1=1" in txt: return False, "WAF: SQL Injection Detected"
        
        return True, None


# --- ORCHESTRATOR: GLOBAL SIMULATION ---

class CDNSimulator:
    def __init__(self):
        self.pops = [
            PointOfPresence(8081, "US-East-1"),
            PointOfPresence(8082, "EU-West-1"),
            PointOfPresence(8083, "ASIA-Pacific-1")
        ]
        self.origin_url = "http://127.0.0.1:8001"

    def run(self):
        print("\n" + "="*70)
        print("SwiftEdge CDN v3: Real-World Solution Simulation")
        print("="*70)

        # 1. Boot Services
        threading.Thread(target=self._run_origin, daemon=True).start()
        for pop in self.pops:
            threading.Thread(target=pop.start_service, daemon=True).start()
        
        print(f"[System] Origin Server active at {self.origin_url}")
        print(f"[System] Global POP Cluster active (3 Regions)")
        time.sleep(2)

        # 2. Simulate Realistic User Interactions
        scenarios = [
            {"user": "New York Client", "pop": "US-East-1", "port": 8081, "type": "First Access (Cold)"},
            {"user": "New York Client", "pop": "US-East-1", "port": 8081, "type": "Repeat Access (Warm)"},
            {"user": "London Client", "pop": "EU-West-1", "port": 8082, "type": "Regional Access (Cold)"},
            {"user": "DDoS Attacker", "pop": "Any", "port": 8081, "type": "High-Frequency Burst", "burst": 8},
            {"user": "Attacker (No Token)", "pop": "Any", "port": 8081, "type": "Security Bypass Attempt", "token": None},

            {"user": "Hacker (SQLi)", "pop": "Any", "port": 8081, "type": "WAF Stress Test", "sqli": True}
        ]

        results = []
        for s in scenarios:
            print(f"\n[Scenario] {s['user']} | {s['type']}")
            iterations = s.get('burst', 1)
            
            for i in range(iterations):
                headers = {"X-Auth": "secure123"}
                if s.get('token') is None and 'token' in s: headers = {}
                
                url = f"http://127.0.0.1:{s['port']}/index.html"
                if s.get('sqli'): url += "?q=' OR 1=1 --"

                start = time.perf_counter()
                try:
                    r = requests.get(url, headers=headers, timeout=2)
                    lat = (time.perf_counter() - start) * 1000
                    status = f"HTTP {r.status_code}"
                    cache = r.headers.get("X-Cache", "N/A")
                    
                    msg = f"{s['user']:<20} | {status:<10} | Cache: {cache:<8} | Latency: {lat:>8.2f}ms"
                    if iterations > 1: msg += f" (Burst {i+1})"
                    results.append(msg)
                    
                    if r.status_code == 403 and "Rate Limit" in r.text:
                        print(f"  -> Request {i+1}: BLOCKED by Rate Limiter")
                        break # Optimization: stop scenario if blocked
                except Exception as e:
                    results.append(f"{s['user']:<20} | FAILED     | Error: {e}")


        # 3. Reporting
        print("\n" + "="*70)
        print("REAL-WORLD ARCHITECTURE PERFORMANCE REPORT")
        print("-" * 70)
        print(f"{'User Location':<20} | {'Status':<10} | {'Cache':<8} | {'E2E Latency'}")
        print("-" * 70)
        for res in results: print(res)
        print("="*70)

    def _run_origin(self):
        from http.server import HTTPServer, SimpleHTTPRequestHandler
        if not os.path.exists('origin'): os.makedirs('origin')
        with open('origin/index.html', 'w') as f: f.write("<html><body>Authoritative Origin Content</body></html>")
        HTTPServer(('127.0.0.1', 8001), SimpleHTTPRequestHandler).serve_forever()

if __name__ == "__main__":
    CDNSimulator().run()
