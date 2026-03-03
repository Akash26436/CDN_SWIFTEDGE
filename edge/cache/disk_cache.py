import os
import time

CACHE_DIR = 'disk_cache'
TTL = 60

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def path_for(key):
    return os.path.join(CACHE_DIR, key.replace('/', '_'))

def get(key):
    path = path_for(key)
    if not os.path.exists(path):
        return None
    if time.time() - os.path.getmtime(path) > TTL:
        os.remove(path)
        return None
    with open(path, 'rb') as f:
        return f.read()

def put(key, data):
    with open(path_for(key), 'wb') as f:
        f.write(data)
