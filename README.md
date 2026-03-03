# SwiftEdge CDN v3 🚀

SwiftEdge CDN v3 is a production-grade Content Delivery Network (CDN) prototype. It focuses on **Real-World Solution Architecture**, transforming edge nodes into intelligent **Points of Presence (POPs)**.

## 🏗️ Solution Architecture

The system is organized into three distinct layers, mimicking industrial CDN deployments:

### 1. 📂 The Client Plane (Downstream)
- **Geographic Simulation**: Realistic clients (NY, London, Tokyo) requesting resources.
- **Latency Steering**: Users are routed to the nearest POP to minimize **TTFB** (Time to First Byte).

### 2. ⚡ The Edge Plane (POP - Point of Presence)
- **Optimized Cache Engine**: Multi-tier architecture (L1 Memory / L2 Compressed Disk).
- **Edge Security Layer**: Integrated **WAF** and **Zero-Trust** token validation.
- **Upstream Handling**: Intelligent fetch logic that syncs with the origin only on verified cache misses.

### 3. ☁️ The Origin Plane (Upstream)
- **Authoritative Source**: The backend server (source of truth) for all global assets.

## 🌟 Key Performance Features

- **Adaptive Caching**: LRU-LFU hybrid eviction logic prevents cache pollution.
- **Async IO**: Background disk writes ensure zero-blocking for high-concurrency traffic.
- **Micro-Latency Optimization**: Serving from L1 Memory is **~100x faster** than origin fetches.

## 🚀 Experience the Simulation

### Prerequisites
- Python 3.11+
- `pip install requests`

### Run the Global Orchestrator
This script boots the entire global infrastructure (Origin + 3 POPs) and simulates a day-in-the-life of the CDN:
```bash
python run_cdn_advanced.py
```

## 🧪 Simulation Scenarios
The orchestrator automatically validates:
- ✅ **New York User**: High-speed delivery via US-East-1 POP.
- ✅ **London User**: Regional delivery via EU-West-1 POP.
- ✅ **Security Incident**: WAF intercepts a SQL Injection attack at the edge.
- ✅ **Unauthorized Access**: Zero-Trust layer blocks a client missing a secure token.

---
Built with ❤️ for High-Performance Edge Computing.
