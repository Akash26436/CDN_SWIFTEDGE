# SwiftEdge CDN v3: Enterprise-Grade Edition 🚀

SwiftEdge CDN v3 is a high-performance Content Delivery Network solution that integrates industry-standard algorithms and architectural patterns.

## ✅ Feature Checklist Alignment

### 🏗️ Core Architecture
- **✅ Dockerized Distributed System**: Full orchestration with `docker-compose`.
- **✅ Horizontal Scaling**: Multi-node edge deployment (`edge1`, `edge2`, `edge3`).
- **✅ Consistent Hashing**: Ring-based hash-routing in the Load Balancer for stable horizontal scaling and cache locality.
- **✅ Load Balancing**: Hash-based distribution ensures deterministic routing.

### ⚡ Edge Server Optimization
- **✅ O(1) Cache Architecture**: HashMap + Doubly Linked List implementation for constant-time lookups and deletions.
- **✅ Efficient Eviction**: Pure LRU (Least Recently Used) strategy for memory management.
- **✅ Controlled Concurrency**: Custom Thread Pool to manage high-volume requests without resource exhaustion.
- **✅ Locking Mechanism**: Per-key locking protects the origin from the "Thundering Herd" problem (cache stampede).

### 💾 Persistence & Observability
- **✅ Multi-Tier Storage**: Automatic promotion/demotion between Memory (L1) and Disk (L2).
- **✅ Disk TTL Cache**: Expiration-based invalidation ensures content freshness.
- **✅ Observability**: Real-time metrics available via the `/metrics` endpoint on every edge node.

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local scripts)

### Running the Distributed System
```bash
docker-compose up --build
```
The system will start:
- **Origin Server**: Port 8001
- **Edge Nodes**: Ports 8081 (Internal)
- **Global Load Balancer**: Port 8080 (External entry point)

### Running the Unified Simulation
For quick verification of all logic in a single terminal:
```bash
python run_cdn_advanced.py
```

## 🧪 Verification
- **Metrics**: Visit `http://localhost:8081/metrics` to see edge performance.
- **Routing**: Monitor Load Balancer logs to see Consistent Hashing in action.
- **Security**: Advanced demo includes DDoS and WAF simulation.

---
Built with ❤️ for Scalable Edge Infrastructure.
