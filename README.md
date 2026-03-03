# SwiftEdge CDN v3: Enterprise-Grade Solution 🚀

SwiftEdge CDN v3 is a state-of-the-art, distributed Content Delivery Network designed for maximum performance, security, and scalability. It implements industry-standard algorithms and architectural patterns used by global CDNs.

## 🌟 Key Features

### ⚡ Performance & Caching
- **✅ O(1) Memory Cache**: High-performance **HashMap + Doubly Linked List** implementation (LRU) for constant-time lookups.
- **✅ Multi-Tier Storage**: Seamless data promotion between **Memory (L1)** and **Compressed Disk (L2)**.
- **✅ Optimized Eviction**: Pure **LRU (Least Recently Used)** strategy prevents cache exhaustion.
- **✅ Disk TTL**: Automatic expiration-based invalidation for content freshness.

### 🏗️ Scalability & Reliability
- **✅ Consistent Hashing**: Ring-based hash-routing ensures stable horizontal scaling and deterministic cache locality.
- **✅ Thundering Herd Protection**: **Per-key locking** prevents multiple simultaneous origin fetches for the same asset.
- **✅ Thread Pool Architecture**: Controlled concurrency for high-throughput edge processing.
- **✅ Intelligent Load Balancing**: Global orchestrator with geographic and hash-based steering.

### 🛡️ Edge Security
- **✅ Zero-Trust Authentication**: Integrated mandatory token-based security for all API/Edge requests.
- **✅ Edge WAF**: Built-in SQL Injection and XSS filtering at the Point of Presence (POP).
- **✅ DDoS Protection**: **Token Bucket Rate Limiting** to intercept high-frequency malicious bursts.

### 📊 Observability
- **✅ /metrics Endpoint**: Real-time observability on every POP to track Hit Ratios, Latency, and Throughput.

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+

### Option 1: Distributed Deployment (Docker)
```bash
docker-compose up --build
```
- **Load Balancer**: `http://localhost:8080`
- **Edge Metrics**: `http://localhost:8081/metrics`

### Option 2: Unified Simulation (Local)
Run the full "Day-in-the-Life" orchestrator to see all features (Caching, Security, Routing) in a single report:
```bash
python run_cdn_advanced.py
```

## 📂 Project Structure
- `/edge`: Edge Server logic and Core Engines (Security, Metrics, Pool).
- `/cache`: O(1) LRU and Disk Persistence implementations.
- `load_balancer.py`: Consistent Hashing ring and request steering.
- `run_cdn_advanced.py`: High-performance simulation suite.

---
Built for speed, secured at the edge. 🚀✨
