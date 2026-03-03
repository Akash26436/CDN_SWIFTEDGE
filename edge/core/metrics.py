import threading

class Metrics:
    def __init__(self):
        self.lock = threading.Lock()
        self.total = 0
        self.hits = 0
        self.misses = 0

    def request(self):
        with self.lock:
            self.total += 1

    def hit(self):
        with self.lock:
            self.hits += 1

    def miss(self):
        with self.lock:
            self.misses += 1

    def report(self):
        with self.lock:
            ratio = self.hits/self.total if self.total else 0
            return f"Total:{self.total} Hits:{self.hits} Misses:{self.misses} HitRatio:{ratio:.2f}"
