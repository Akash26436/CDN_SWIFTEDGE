import socket
import threading
import sys
import os

# Allow importing from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from concurrent.futures import ThreadPoolExecutor
from cache.lru_cache import LRUCache
from cache.disk_cache import DiskCache
from security.rate_limiter import RateLimiter
from security.waf import WAF
from security.auth import AuthManager
from metrics.metrics import Metrics
import time
import requests
import argparse

class LockManager:
    def __init__(self):
        self.locks = {}
        self.master_lock = threading.Lock()

    def get_lock(self, key):
        with self.master_lock:
            if key not in self.locks:
                self.locks[key] = threading.Lock()
            return self.locks[key]

class EdgeServer:
    """
    Enterprise Edge Server with multi-tier caching, security, and metrics.
    """
    def __init__(self, port, origin_url="http://origin:8001"):
        self.port = port
        self.origin_url = origin_url
        
        # Components
        self.l1_cache = LRUCache(capacity=200)
        self.l2_cache = DiskCache(cache_dir=f"disk_cache_{port}", ttl=120)
        self.limiter = RateLimiter(rate=5, capacity=10)
        self.waf = WAF()
        self.auth = AuthManager()
        self.metrics = Metrics()
        self.lock_manager = LockManager()
        self.pool = ThreadPoolExecutor(max_workers=50)

    def handle_client(self, client, addr):
        start_time = time.perf_counter()
        self.metrics.record_request()
        
        try:
            raw_req = client.recv(4096).decode(errors='ignore')
            if not raw_req: return
            
            lines = raw_req.split('\r\n')
            first_line = lines[0].split(' ')
            if len(first_line) < 2: return
            
            method, path = first_line[0], first_line[1]
            headers = {}
            for line in lines[1:]:
                if ": " in line:
                    k, v = line.split(": ", 1)
                    headers[k] = v

            # 1. Metrics Endpoint
            if path == "/metrics":
                self._send_response(client, self.metrics.get_json(), "application/json")
                return

            # 2. Security: Rate Limiting
            if not self.limiter.consume():
                self.metrics.record_rate_limit()
                self._send_error(client, 429, "Too Many Requests")
                return

            # 3. Security: Auth
            success, err = self.auth.validate(headers.get("Authorization"))
            if not success:
                self._send_error(client, 401, err)
                return

            # 4. Security: WAF
            safe, reason = self.waf.is_safe(raw_req)
            if not safe:
                self._send_error(client, 403, f"Blocked by WAF: {reason}")
                return

            # 5. Multi-Tier Cache Lookup
            resource_key = path.strip("/") or "index.html"
            data = self._tiered_lookup(resource_key)
            
            # 6. Final Delivery
            self.metrics.record_latency((time.perf_counter() - start_time) * 1000)
            self._send_response(client, data)

        except Exception as e:
            print(f"[Edge {self.port}] Error: {e}")
        finally:
            client.close()

    def _tiered_lookup(self, key):
        # L1 (Memory)
        data = self.l1_cache.get(key)
        if data:
            self.metrics.record_hit()
            return data

        # Lock to prevent thundering herd
        lock = self.lock_manager.get_lock(key)
        with lock:
            # Re-check L1
            data = self.l1_cache.get(key)
            if data: return data
            
            # L2 (Disk)
            data = self.l2_cache.get(key)
            if data:
                self.metrics.record_hit()
                self.l1_cache.put(key, data)
                return data

            # MISS: Fetch from Origin
            self.metrics.record_miss()
            try:
                resp = requests.get(f"{self.origin_url}/{key}")
                data = resp.content
                self.l2_cache.put(key, data)
                self.l1_cache.put(key, data)
                return data
            except:
                return b"Error fetching from origin"

    def _send_response(self, client, data, content_type="text/html"):
        if isinstance(data, str): data = data.encode()
        header = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(data)}\r\nConnection: close\r\n\r\n"
        client.sendall(header.encode() + data)

    def _send_error(self, client, code, msg):
        resp = f"HTTP/1.1 {code} {msg}\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n{msg}"
        client.sendall(resp.encode())

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', self.port))
        s.listen(100)
        print(f"[Edge] Serving on port {self.port}...")
        while True:
            client, addr = s.accept()
            self.pool.submit(self.handle_client, client, addr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--origin", type=str, default="http://origin:8001")
    args = parser.parse_args()
    
    server = EdgeServer(args.port, args.origin)
    server.start()
