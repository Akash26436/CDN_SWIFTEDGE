# SwiftEdge CDN v3 🚀

SwiftEdge CDN v3 is a high-performance, distributed Content Delivery Network (CDN) prototype built with Python. It features edge servers with tiered caching, intelligent traffic routing, and robust security layers.

## 🌟 Key Features

### 🛡️ Edge Security & Protection
- **Web Application Firewall (WAF)**: Protects against common web attacks like SQL Injection and XSS.
- **DDoS Mitigation**: Token Bucket rate limiting to prevent traffic surges.
- **Bot Detection**: Pattern-based identification of malicious crawlers.
- **Zero-Trust Security**: Mandatory token-based authentication at the edge.

### 🧠 Intelligent Traffic Management
- **Latency-Based Routing**: Dynamically routes users to the optimal edge node based on simulated global network conditions.
- **Simulated Global Regions**: US, EU, and ASIA regions with realistic performance jitter.

### ⚡ Performance & Compute
- **Tiered Caching**: LRU In-Memory cache for hot data + TTL-based Disk cache for persistence.
- **Edge Compute Engine**: Run custom logic (interceptors) near the user to modify requests and responses.
- **Custom Thread Pool**: High-concurrency handling for edge requests.

## 🛠️ Project Structure
```text
CDN-SWIFTEDGE/
├── edge/               # Edge Server Implementation
│   ├── core/           # Security, Compute, Metrics, Locking
│   ├── cache/          # LRU and Disk Caching logic
│   └── edge_server.py  # Main Edge Server logic
├── origin/             # Origin Server content
├── load_balancer.py    # Intelligent Routing Load Balancer
├── run_cdn_advanced.py # Unified Demo Script (Single-process)
├── Dockerfile          # Containerization for Edge nodes
└── docker-compose.yml  # Distributed cluster orchestration
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- `pip install requests`

### Running the Advanced Demo
To see all features (Security, Routing, Zero-Trust) in action, run the unified simulation:
```bash
python run_cdn_advanced.py
```

### Distributed Setup (Docker)
If you have Docker Desktop running:
```bash
docker-compose up --build
```
This will spin up a 3-node edge cluster with a dedicated load balancer.

## 🧪 Verification
The `run_cdn_advanced.py` script automatically verifies:
- ✅ Zero-Trust authentication blocks.
- ✅ WAF intercepting malicious payloads.
- ✅ Rate limiting triggering under load.
- ✅ Intelligent routing selecting the best region.

---
Built with ❤️ for High-Performance Edge Computing.
