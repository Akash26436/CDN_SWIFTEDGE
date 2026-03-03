import socket
import hashlib
import bisect

class ConsistentHashRing:
    """
    Consistent Hashing with virtual nodes for stable distribution.
    """
    def __init__(self, nodes=None, replicas=50):
        self.replicas = replicas
        self.ring = []
        self.nodes = {} # Hash -> node_name
        if nodes:
            for node in nodes:
                self.add_node(node)

    def add_node(self, node):
        for i in range(self.replicas):
            h = self._hash(f"{node}:{i}")
            bisect.insort(self.ring, h)
            self.nodes[h] = node

    def _hash(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def get_node(self, key):
        if not self.ring: return None
        h = self._hash(key)
        idx = bisect.bisect_right(self.ring, h)
        if idx == len(self.ring): idx = 0
        return self.nodes[self.ring[idx]]

class LoadBalancer:
    def __init__(self, port=8080, nodes=None):
        self.port = port
        self.ring = ConsistentHashRing(nodes)
        print(f"[LB] Consistent Hashing Ring initialized with {len(nodes)} nodes.")

    def handle_request(self, client):
        try:
            req = client.recv(4096)
            if not req: return
            
            raw = req.decode(errors='ignore')
            lines = raw.split('\r\n')
            if not lines: return
            
            first_line = lines[0].split(' ')
            if len(first_line) < 2: return
            
            path = first_line[1]
            target_node = self.ring.get_node(path)
            
            if not target_node:
                client.sendall(b"HTTP/1.1 503 Service Unavailable\r\n\r\nNo edge nodes available")
                return

            print(f"[LB] Route: {path} -> {target_node}")
            host, port = target_node.split(':')
            
            # Forward to Edge
            edge = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            edge.connect((host, int(port)))
            edge.sendall(req)
            
            # Stream response back to client
            while True:
                data = edge.recv(8192)
                if not data: break
                client.sendall(data)
            edge.close()

        except Exception as e:
            print(f"[LB] Forward Error: {e}")
        finally:
            client.close()

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', self.port))
        s.listen(100)
        print(f"[LB] Listening on port {self.port}...")
        while True:
            client, addr = s.accept()
            threading.Thread(target=self.handle_request, args=(client,), daemon=True).start()

if __name__ == "__main__":
    import threading
    # In docker, these are the service names from docker-compose
    LB = LoadBalancer(nodes=["edge1:8081", "edge2:8081", "edge3:8081"])
    LB.start()
