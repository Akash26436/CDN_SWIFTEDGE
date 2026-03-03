# SwiftEdge CDN: Enterprise Architecture 🚀

SwiftEdge CDN is a production-grade, distributed edge delivery platform built with modular enterprise patterns.

## 🏗️ Technical Architecture

### 1. 📂 Core Components
- **`cache/`**: Advanced L1/L2 caching logic.
  - `lru_cache.py`: **O(1) HashMap + Doubly Linked List** for constant-time eviction.
  - `disk_cache.py`: File-based storage with **TTL (Time-To-Live)** and persistence.
- **`security/`**: multi-layered defense.
  - `rate_limiter.py`: **Token Bucket** algorithm for DDoS protection.
  - `waf.py`: Layer 7 Web Application Firewall for pattern-based filtering.
  - `auth.py`: **Zero-Trust** Bearer token validation.
- **`metrics/`**: Observability system for real-time analytics.

### 2. ⚡ Edge Runtime
The **Edge Server** acts as the localized Point of Presence (POP).
- **Thread Pool**: Managed concurrency for high-load handling.
- **Per-Key Locking**: Prevents the **Thundering Herd** problem by synchronizing simultaneous origin fetches.

### 3. 🌐 Global Load Balancer
- **Consistent Hashing**: Implementation with virtual nodes to ensure stable routing and cache locality.

## 🚀 Deployment

### Option A: Local Enterprise Simulation
If you don't have Docker, run the core logic in a unified script (deprecated but kept for quick tests):
```bash
python run_cdn_advanced.py
```

### Option B: Distributed System (Docker - Recommended)
This launches the full cluster (Origin, LB, 3 Edge Nodes).
```bash
docker-compose up --build
```

## 🧪 Verification

Once the system is running, run the **Enterprise Validation Suite**:
```bash
python validate_enterprise.py
```

This suite validates:
- [x] Zero-Trust Token Authentication
- [x] WAF filtering (SQLi/XSS)
- [x] Token Bucket Throttling
- [x] O(1) LRU Hit performance
- [x] Consistent Hashing Routing

---
Built for performance, secured with intelligence.
