import socket
import argparse
import requests
import os
import sys

# Add the project root to sys.path to allow relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security import SecurityManager
from core.edge_compute import EdgeCompute, inject_server_latency_header, minify_html_interceptor
from core.metrics import Metrics
from core.lock_manager import LockManager
from core.thread_pool import ThreadPool
from cache.lru_cache import LRUCache
import cache.disk_cache as disk

metrics = Metrics()
locks = LockManager()
pool = ThreadPool(20) # Controlled concurrency
security = SecurityManager()
compute = EdgeCompute()
memory_cache = LRUCache(100) # O(1) LRU


def get_optimized_cache(port):
    return OptimizedCache(port)


# Register Edge Functions
compute.register_request_interceptor(inject_server_latency_header)
compute.register_response_interceptor(minify_html_interceptor)

ORIGIN = 'http://origin:8001'
ZERO_TRUST_TOKEN = "secure-edge-token-2026"

def handle(client, addr):
    ip = addr[0]
    try:
        raw_request = client.recv(4096)
        if not raw_request:
            client.close()
            return
            
        request_text = raw_request.decode(errors='ignore')
        lines = request_text.split('\r\n')
        if not lines: return
        
        parts = lines[0].split(' ')
        if len(parts) < 2: return
        path = parts[1]
        
        # 1. Edge Security (WAF, Rate Limiting, Bot Detection)
        user_agent = "Unknown"
        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                k, v = line.split(': ', 1)
                headers[k] = v
                if k.lower() == 'user-agent': user_agent = v

        is_allowed, reason = security.check_request(ip, user_agent, request_text)
        if not is_allowed:
            client.sendall(f"HTTP/1.1 403 Forbidden\r\n\r\nSecurity Block: {reason}".encode())
            return

        # 2. Zero-trust / API Protection
        if "X-Edge-Auth" not in headers or headers["X-Edge-Auth"] != ZERO_TRUST_TOKEN:
             client.sendall(b"HTTP/1.1 401 Unauthorized\r\n\r\nZero-trust: Missing or invalid token")
             return

        if path == '/metrics':
            client.sendall(b"HTTP/1.1 200 OK\r\n\r\n" + metrics.report().encode())
            client.close()
            return
            
        key = path.strip('/') or 'index.html'

        # 3. Edge Compute (Request Processing)
        context = compute.process_request(key, headers)
        key = context["key"]

        metrics.request()

        data = memory_cache.get(key)
        if data:
            metrics.hit()
            status = "HIT_MEM"
        else:
            lock = locks.acquire(key)
            try:
                data = memory_cache.get(key)
                if data:
                    metrics.hit()
                    status = "HIT_MEM"
                else:
                    data = disk.get(key)
                    if data:
                        metrics.hit()
                        status = "HIT_DISK"
                        memory_cache.put(key, data)
                    else:
                        metrics.miss()
                        status = "MISS"
                        response = requests.get(f"{ORIGIN}/{key}")
                        data = response.content
                        disk.put(key, data)
                        memory_cache.put(key, data)
            finally:
                lock.release()


        # 4. Edge Compute (Response Processing)
        resp_headers = {"Content-Type": "text/html" if key.endswith(".html") else "application/octet-stream"}
        data, resp_headers = compute.process_response(data, resp_headers)

        header_str = "HTTP/1.1 200 OK\r\n"
        for k, v in resp_headers.items():
            header_str += f"{k}: {v}\r\n"
        header_str += "\r\n"

        client.sendall(header_str.encode() + data)
    except Exception as e:
        print(f"Error handling request from {ip}: {e}")
    finally:
        client.close()


def start(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', port))
    server.listen(100)
    print(f"Edge running {port}")
    while True:
        client, addr = server.accept()
        pool.submit(handle, client, addr)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8081)
    args = parser.parse_args()
    start(args.port)
