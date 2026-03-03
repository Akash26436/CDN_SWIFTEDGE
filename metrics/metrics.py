import threading
import json

class Metrics:
    """
    Thread-safe analytics for Edge server performance.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "rate_limit_triggers": 0,
            "latencies": []
        }

    def record_request(self):
        with self.lock:
            self.stats["total_requests"] += 1

    def record_hit(self):
        with self.lock:
            self.stats["cache_hits"] += 1

    def record_miss(self):
        with self.lock:
            self.stats["cache_misses"] += 1

    def record_rate_limit(self):
        with self.lock:
            self.stats["rate_limit_triggers"] += 1

    def record_latency(self, ms):
        with self.lock:
            self.stats["latencies"].append(ms)
            if len(self.stats["latencies"]) > 1000:
                self.stats["latencies"].pop(0)

    def get_report(self):
        with self.lock:
            total = self.stats["total_requests"]
            hits = self.stats["cache_hits"]
            ratio = (hits / total) if total > 0 else 0
            avg_lat = sum(self.stats["latencies"]) / len(self.stats["latencies"]) if self.stats["latencies"] else 0
            
            return {
                "total_requests": total,
                "cache_hits": hits,
                "cache_misses": self.stats["cache_misses"],
                "hit_ratio": f"{ratio:.2%}",
                "avg_latency_ms": f"{avg_lat:.2f}ms",
                "rate_limit_triggers": self.stats["rate_limit_triggers"]
            }

    def get_json(self):
        return json.dumps(self.get_report(), indent=2)
