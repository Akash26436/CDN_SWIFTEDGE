# SwiftEdge CDN v3 🚀

SwiftEdge CDN v3 is a high-performance, distributed Content Delivery Network (CDN) prototype. It transforms standard edge nodes into intelligent units capable of **Multi-tier Caching**, **Advanced Security**, and **Edge Computing**.

## 🌟 Key Features

### ⚡ Multi-Tier Edge Caching ("Top of everything")
- **LRU In-Memory Cache**: Lightning-fast retrieval for hot data directly from RAM.
- **TTL-Based Disk Cache**: Persistence layer ensuring high hit ratios even for large file sets.
- **Auto-Promotion**: Intelligent movement of data from Disk to Memory based on access patterns.

### 🛡️ Global Edge Security
- **Web Application Firewall (WAF)**: Real-time inspection and blocking of SQL Injection, XSS, and Path Traversal attacks.
- **DDoS Mitigation**: Token Bucket rate limiting handles massive traffic spikes at the edge.
- **Behavioral Bot Detection**: Identifies and neutralizes malicious crawlers before they reach your origin.
- **Zero-Trust Protection**: Mandatory `X-Auth` token validation for every single request.

### 🧠 Intelligent Traffic Routing
- **Latency-Based Steering**: The Load Balancer dynamically routes traffic to the "closest" healthy edge node (US, EU, or ASIA) based on real-time network Jitter.
- **Global Scale Simulation**: Real-world network conditions simulated for robust testing.

### 💻 Edge Compute Engine
- **Request Interceptors**: Modify request context, inject headers, and handle logic near the user.
- **Response Interceptors**: On-the-fly content modification (e.g., HTML minification) and dynamic header injection.

## 🛠️ Project Structure
```text
CDN-SWIFTEDGE/
├── edge/               # Edge Server Implementation
│   ├── core/           # Security, Compute Engine, Metrics, LockManager
│   ├── cache/          # LRU and Disk Caching algorithms
│   └── edge_server.py  # Integrated Edge Node logic
├── origin/             # Origin Server (Source of Truth)
├── load_balancer.py    # Intelligent Latency-Based Router
├── run_cdn_advanced.py # THE UNIFIED DEMO SUITE
├── Dockerfile          # Containerized Node definition
└── docker-compose.yml  # Cluster orchestration (Origin + 3 Edges + LB)
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- `pip install requests`

### Running the Advanced Demo
Experience the full power of SwiftEdge (Security, Caching, Routing) in one command:
```bash
python run_cdn_advanced.py
```

### Distributed Setup (Docker)
To run as a real distributed cluster:
```bash
docker-compose up --build
```

## 🧪 Verification
The `run_cdn_advanced.py` suite automatically validates:
- [x] **Zero-Trust**: 401 Unauthorized on missing tokens.
- [x] **WAF**: 403 Forbidden on malicious payloads.
- [x] **Rate Limiting**: Dropping traffic during simulated DDoS.
- [x] **Caching**: Verifying Memory vs Disk HITs.
- [x] **Routing**: Latency-based node selection.

---
Built with ❤️ for High-Performance Edge Computing.
