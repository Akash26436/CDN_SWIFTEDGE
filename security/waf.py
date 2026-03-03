import re

class WAF:
    """
    Web Application Firewall for filtering malicious patterns.
    """
    def __init__(self):
        self.patterns = [
            re.compile(r"OR\s+1=1", re.IGNORECASE), # SQLi
            re.compile(r"<script.*?>", re.IGNORECASE), # XSS
            re.compile(r"UNION\s+SELECT", re.IGNORECASE), # SQLi
            re.compile(r"javascript:", re.IGNORECASE) # XSS
        ]

    def is_safe(self, text):
        for pattern in self.patterns:
            if pattern.search(text):
                return False, f"Matched pattern: {pattern.pattern}"
        return True, None
