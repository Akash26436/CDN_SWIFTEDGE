import socket
import threading
import time
import requests
import os
import hashlib
from queue import Queue

# --- COMPONENTS ---

class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.lock = threading.Lock()
        self.head = Node(0,0)
        self.tail = Node(0,0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add(self, node):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    def get(self, key):
        with self.lock:
            if key in self.cache:
                node = self.cache[key]
                self._remove(node)
                self._add(node)
                return node.value
            return None

    def put(self, key, value):
        with self.lock:
            if key in self.cache:
                self._remove(self.cache[key])
            node = Node(key, value)
            self._add(node)
            self.cache[key] = node
            if len(self.cache) > self.capacity:
                lru = self.tail.prev
                self._remove(lru)
                del self.cache[lru.key]

class DiskCache:
    def __init__(self, dir_name):
        self.dir = dir_name
        self.ttl = 60
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def path_for(self, key):
        return os.path.join(self.dir, key.replace('/', '_'))

    def get(self, key):
        path = self.path_for(key)
        if not os.path.exists(path):
            return None
        if time.time() - os.path.getmtime(path) > self.ttl:
            os.remove(path)
            return None
        with open(path, 'rb') as f:
            return f.read()

    def put(self, key, data):
        with open(self.path_for(key), 'wb') as f:
            f.write(data)

class ThreadPool:
    def __init__(self, size):
        self.tasks = Queue()
        for _ in range(size):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()

    def worker(self):
        while True:
            func, args = self.tasks.get()
            try:
                func(*args)
            finally:
                self.tasks.task_done()

    def submit(self, func, *args):
        self.tasks.put((func, args))

class Metrics:
    def __init__(self):
        self.lock = threading.Lock()
        self.total = 0
        self.hits = 0
        self.misses = 0

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

class LockManager:
    def __init__(self):
        self.locks = {}
        self.global_lock = threading.Lock()

    def acquire(self, key):
        with self.global_lock:
            if key not in self.locks:
                self.locks[key] = threading.Lock()
            lock = self.locks[key]
        lock.acquire()
        return lock

# --- SERVERS ---

def run_origin(port):
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    os.chdir('origin')
    httpd = HTTPServer(('localhost', port), SimpleHTTPRequestHandler)
    print(f"[Origin] Running on {port}")
    httpd.serve_forever()

class EdgeServer:
    def __init__(self, port, origin_url):
        self.port = port
        self.origin_url = origin_url
        self.memory_cache = LRUCache(100)
        self.disk_cache = DiskCache(f"disk_cache_{port}")
        self.metrics = Metrics()
        self.locks = LockManager()
        self.pool = ThreadPool(5)

    def handle(self, client):
        try:
            req = client.recv(4096).decode()
            if not req: return
            parts = req.split(' ')
            if len(parts) < 2: return
            path = parts[1]
            if path == '/metrics':
                client.sendall(b"HTTP/1.1 200 OK\r\n\r\n" + self.metrics.report().encode())
                return
            key = path.strip('/') or 'index.html'
            self.metrics.request()
            data = self.memory_cache.get(key)
            if data:
                self.metrics.hit()
            else:
                lock = self.locks.acquire(key)
                try:
                    data = self.memory_cache.get(key)
                    if not data:
                        data = self.disk_cache.get(key)
                        if not data:
                            self.metrics.miss()
                            resp = requests.get(f"{self.origin_url}/{key}")
                            data = resp.content
                            self.disk_cache.put(key, data)
                        self.memory_cache.put(key, data)
                finally:
                    lock.release()
            client.sendall(b"HTTP/1.1 200 OK\r\n\r\n" + data)
        except Exception as e:
            print(f"[Edge {self.port}] Error: {e}")
        finally:
            client.close()

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('localhost', self.port))
        server.listen(10)
        print(f"[Edge {self.port}] Running")
        while True:
            client, _ = server.accept()
            self.pool.submit(self.handle, client)

def run_load_balancer(port, edges):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', port))
    server.listen(100)
    print(f"[LB] Running on {port}")
    
    def get_node(key):
        h = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return edges[h % len(edges)]

    while True:
        client, _ = server.accept()
        try:
            req = client.recv(4096)
            if not req: continue
            parts = req.decode().split(' ')
            if len(parts) < 2: continue
            key = parts[1]
            e_host, e_port = get_node(key)
            edge = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            edge.connect((e_host, e_port))
            edge.sendall(req)
            resp = edge.recv(8192)
            client.sendall(resp)
            edge.close()
        except Exception as e:
            print(f"[LB] Error: {e}")
        finally:
            client.close()

if __name__ == '__main__':
    # Start Origin
    threading.Thread(target=run_origin, args=(8001,), daemon=True).start()
    
    # Start Edges
    edge_ports = [8081, 8082, 8083]
    for p in edge_ports:
        e = EdgeServer(p, "http://localhost:8001")
        threading.Thread(target=e.start, daemon=True).start()
    
    # Start LB
    threading.Thread(target=run_load_balancer, args=(8080, [('localhost', p) for p in edge_ports]), daemon=True).start()
    
    # Keep alive and test
    time.sleep(2)
    print("\n--- Testing CDN ---")
    for _ in range(5):
        try:
            r = requests.get("http://localhost:8080/index.html")
            print(f"Request: {r.status_code}")
        except Exception as e:
            print(f"Test Error: {e}")
    
    # Report Metrics from one edge
    try:
        r = requests.get("http://localhost:8081/metrics")
        print(f"Edge 8081 Metrics: {r.text}")
    except: pass
    
    print("\nAll components running. Press Ctrl+C to stop.")
    while True: time.sleep(1)
