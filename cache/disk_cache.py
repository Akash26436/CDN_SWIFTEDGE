import os
import time

class DiskCache:
    """
    File-based L2 cache with TTL (Time-To-Live) support.
    """
    def __init__(self, cache_dir, ttl=60):
        self.cache_dir = cache_dir
        self.ttl = ttl
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def _get_path(self, key):
        safe_key = key.replace('/', '_').replace('\\', '_')
        return os.path.join(self.cache_dir, safe_key)

    def get(self, key):
        path = self._get_path(key)
        if not os.path.exists(path):
            return None
        
        # Check TTL
        if time.time() - os.path.getmtime(path) > self.ttl:
            os.remove(path)
            return None
            
        try:
            with open(path, 'rb') as f:
                return f.read()
        except:
            return None

    def put(self, key, data):
        path = self._get_path(key)
        try:
            with open(path, 'wb') as f:
                f.write(data)
        except Exception as e:
            print(f"[DiskCache] Write Error: {e}")
