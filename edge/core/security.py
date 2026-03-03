import time
import re
import threading

class RateLimiter:
    def __init__(self, rate=10, capacity=20):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()

    def consume(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

class WAF:
    def __init__(self):
        self.rules = [
            (r"(?i)(OR|AND)\s+.*=.*", "SQL Injection Pattern"),
            (r"(?i)<script.*?>.*?</script.*?>", "XSS Pattern"),
            (r"(?i)\.\./\.\./", "Path Traversal Pattern")
        ]

    def inspect(self, request_text):
        for pattern, reason in self.rules:
            if re.search(pattern, request_text):
                return False, reason
        return True, None

class BotDetection:
    def __init__(self):
        self.known_bots = ["bad-bot", "malicious-crawler"]
        self.request_history = {} # simple history tracking

    def is_bot(self, ip, user_agent):
        if user_agent in self.known_bots:
            return True
        # Simple behavioral heuristic: too many requests in a short time (handled by RateLimiter mainly)
        return False

class SecurityManager:
    def __init__(self):
        self.rate_limiters = {} # ip -> limiter
        self.waf = WAF()
        self.bot_detection = BotDetection()

    def check_request(self, ip, user_agent, payload):
        # 1. Bot Detection
        if self.bot_detection.is_bot(ip, user_agent):
            return False, "Bot detected"
        
        # 2. Rate Limiting
        if ip not in self.rate_limiters:
            self.rate_limiters[ip] = RateLimiter()
        if not self.rate_limiters[ip].consume():
            return False, "Rate limit exceeded (DDoS protection)"
        
        # 3. WAF inspection
        is_safe, reason = self.waf.inspect(payload)
        if not is_safe:
            return False, f"WAF Block: {reason}"
            
        return True, "OK"
