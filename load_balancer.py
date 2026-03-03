import socket
import hashlib

import random

# Simulated "Global Regions" with latencies (ms)
# In reality, this would be based on real-time health checks or geodns
EDGE_REGISTRY = [
    {'id': 'edge1', 'host': 'edge1', 'port': 8081, 'region': 'US-East', 'latency': 10},
    {'id': 'edge2', 'host': 'edge2', 'port': 8081, 'region': 'EU-West', 'latency': 50},
    {'id': 'edge3', 'host': 'edge3', 'port': 8081, 'region': 'ASIA-South', 'latency': 120}
]

def get_node(key):
    """
    Intelligent Routing: Selects node based on lowest simulated latency.
    For demonstration, we periodically 'jitter' these latencies to simulate network shifts.
    """
    # Simulate network jitter:
    for node in EDGE_REGISTRY:
        node['current_latency'] = node['latency'] + random.randint(-5, 5)

    # Pick the best node (lowest current latency)
    best_node = min(EDGE_REGISTRY, key=lambda x: x['current_latency'])
    print(f"[LB] Intelligent Routing: Selected {best_node['id']} ({best_node['region']}) with {best_node['current_latency']}ms latency")
    return best_node['host'], best_node['port']


def handle(client):
    try:
        req = client.recv(4096)
        if not req:
            client.close()
            return
        
        parts = req.decode().split(' ')
        if len(parts) < 2:
            client.close()
            return
            
        key = parts[1]
        host, port = get_node(key)

        edge = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        edge.connect((host, port))
        edge.sendall(req)
        
        # Simple response forwarding (might need loop for large responses)
        resp = edge.recv(8192)
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
