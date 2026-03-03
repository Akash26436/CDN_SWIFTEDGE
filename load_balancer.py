import socket
import hashlib
import bisect

class ConsistentHash:
    def __init__(self, nodes=None, replicas=3):
        self.replicas = replicas
        self.ring = []
        self.nodes = {}
        if nodes:
            for node in nodes:
                self.add_node(node)

    def add_node(self, node):
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            bisect.insort(self.ring, key)
            self.nodes[key] = node

    def _hash(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def get_node(self, key):
        if not self.ring: return None
        h = self._hash(key)
        idx = bisect.bisect_right(self.ring, h)
        if idx == len(self.ring): idx = 0
        return self.nodes[self.ring[idx]]

# Configuration for Edge Nodes
NODES = ['edge1:8081', 'edge2:8081', 'edge3:8081']
CH = ConsistentHash(NODES)

def handle(client):
    try:
        req = client.recv(4096)
        if not req:
            client.close()
            return
        
        request_text = req.decode(errors='ignore')
        parts = request_text.split(' ')
        if len(parts) < 2:
            client.close()
            return
            
        path = parts[1]
        node = CH.get_node(path)
        host, port = node.split(':')
        port = int(port)

        print(f"[LB] Hash-Routing path '{path}' to {node}")

        edge = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        edge.connect((host, port))
        edge.sendall(req)
        
        # Stream response back
        while True:
            resp = edge.recv(8192)
            if not resp: break
            client.sendall(resp)
        edge.close()
    except Exception as e:
        print(f"Error in load balancer: {e}")
    finally:
        client.close()


def start():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 8080))
    server.listen(100)
    print('Load balancer on 8080')
    while True:
        client, _ = server.accept()
        handle(client)

if __name__ == '__main__':
    start()
