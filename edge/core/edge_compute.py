import json

class EdgeCompute:
    """
    Simulates an Edge Compute engine where custom 'functions' can be registered
    to run logic on requests and responses.
    """
    def __init__(self):
        self.request_interceptors = []
        self.response_interceptors = []

    def register_request_interceptor(self, func):
        self.request_interceptors.append(func)

    def register_response_interceptor(self, func):
        self.response_interceptors.append(func)

    def process_request(self, key, headers):
        """Logic near user: modify request context"""
        context = {"key": key, "headers": headers, "action": "proxy"}
        for interceptor in self.request_interceptors:
            context = interceptor(context)
        return context

    def process_response(self, data, headers):
        """Logic near user: modify response content/headers"""
        for interceptor in self.response_interceptors:
            data, headers = interceptor(data, headers)
        return data, headers

# Example Edge Functions
def inject_server_latency_header(context):
    context["headers"]["X-Edge-Processed"] = "true"
    return context

def minify_html_interceptor(data, headers):
    if headers.get("Content-Type") == "text/html":
        # Simple simulation: just remove some spaces
        data = data.replace(b"    ", b"")
    headers["X-Powered-By"] = "SwiftEdge-Compute"
    return data, headers
