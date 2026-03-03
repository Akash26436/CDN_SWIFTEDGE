class AuthManager:
    """
    Zero-trust Bearer Token Authentication.
    """
    def __init__(self, secret_token="swift-edge-master-key-2026"):
        self.secret_token = secret_token

    def validate(self, auth_header):
        if not auth_header:
            return False, "Missing Authorization Header"
        
        # Expecting 'Bearer <token>'
        if not auth_header.startswith("Bearer "):
            return False, "Invalid Authorization Format"
        
        token = auth_header.split(" ")[1]
        if token != self.secret_token:
            return False, "Unauthorized Token"
            
        return True, None
