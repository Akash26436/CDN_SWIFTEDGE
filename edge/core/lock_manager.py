import threading

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
