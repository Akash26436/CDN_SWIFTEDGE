import time
import threading

class RateLimiter:
    """
    Token Bucket Algorithm for DDoS protection.
    """
    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens=1):
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self):
        now = time.time()
        delta = now - self.last_refill
        new_tokens = delta * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
