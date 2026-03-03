import os
import time
import json
import threading
import zlib
from queue import Queue

class OptimizedCache:
    """
    Advanced Two-Tier Caching Engine
    L1: High-speed Memory (Thread-safe dict)
    L2: Compressed Disk Storage (Async write)
    """
    def __init__(self, port, mem_capacity=100, disk_dir="opt_cache"):
        self.port = port
        self.mem_capacity = mem_capacity
        self.disk_dir = f"{disk_dir}_{port}"
        self.mem_cache = {} # Key -> (data, last_access, weight)
        self.lock = threading.Lock()
        
        # Async IO Queue
        self.io_queue = Queue()
        
        if not os.path.exists(self.disk_dir):
            os.makedirs(self.disk_dir)

        # Start Async IO Worker
        threading.Thread(target=self._io_worker, daemon=True).start()

    def _io_worker(self):
        while True:
            key, data = self.io_queue.get()
            try:
                path = os.path.join(self.disk_dir, key.replace('/', '_'))
                compressed = zlib.compress(data)
                with open(path, 'wb') as f:
                    f.write(compressed)
            except Exception as e:
                print(f"[Cache {self.port}] IO Error: {e}")
            finally:
                self.io_queue.task_done()

    def get(self, key):
        start = time.perf_counter()
        
        # 1. Check L1 Memory
        with self.lock:
            if key in self.mem_cache:
                data, _, weight = self.mem_cache[key]
                self.mem_cache[key] = (data, time.time(), weight + 1)
                latency = (time.perf_counter() - start) * 1000
                return data, "L1_HIT", latency

        # 2. Check L2 Disk
        path = os.path.join(self.disk_dir, key.replace('/', '_'))
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    compressed = f.read()
                data = zlib.decompress(compressed)
                
                # Promote to L1
                self.put_l1(key, data)
                
                latency = (time.perf_counter() - start) * 1000
                return data, "L2_HIT", latency
            except:
                pass

        return None, "MISS", (time.perf_counter() - start) * 1000

    def put_l1(self, key, data):
        with self.lock:
            if len(self.mem_cache) >= self.mem_capacity:
                # Simple LRU-LFU Hybrid Eviction: Evict lowest (weight / access_recency)
                now = time.time()
                victim = min(self.mem_cache.keys(), 
                             key=lambda k: self.mem_cache[k][2] / (now - self.mem_cache[k][1] + 1))
                del self.mem_cache[victim]
            
            self.mem_cache[key] = (data, time.time(), 1)

    def put(self, key, data):
        """Tiered Put: Immediate L1 + Async L2"""
        self.put_l1(key, data)
        self.io_queue.put((key, data))
