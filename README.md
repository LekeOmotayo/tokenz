# ⚡ Leke Local Token Cache — Zero-Infrastructure Semantic Caching Engine

> **A high-performance Python + SQLite semantic caching gateway** designed for local LLM token optimization and cost reduction. Intercepts semantically identical or near-duplicate queries, returning cached responses in **sub-millisecond latency** with **zero external dependencies** (no Redis, no Docker, no cloud vector DB required).

---

## 🏗️ Architecture Overview

```
                      ┌──────────────────────────────────────────────┐
                      │             Incoming LLM Prompt              │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │           Exact Normalized Lookup            │
                      │       (O(1) SQLite B-Tree Index Check)       │
                      └──────────────┬───────────────────────────────┘
                                     │
                     ┌───────────────┴───────────────┐
                     │ HIT                           │ MISS
                     ▼                               ▼
       ┌───────────────────────────┐   ┌───────────────────────────┐
       │   Return Cached Response  │   │  Deterministic Embedding  │
       │   (0.05ms, 100% Savings)  │   │   (128-dim SHA-256 Trigrams)
       └───────────────────────────┘   └─────────────┬─────────────┘
                                                     │
                                                     ▼
                                       ┌───────────────────────────┐
                                       │     Cosine Similarity     │
                                       │    Scan Across SQLite     │
                                       └─────────────┬─────────────┘
                                                     │
                                     ┌───────────────┴───────────────┐
                                     │ Sim >= Threshold              │ Sim < Threshold
                                     ▼                               ▼
                       ┌───────────────────────────┐   ┌───────────────────────────┐
                       │  CACHE HIT (Semantic Sim) │   │        CACHE MISS         │
                       │   Update LRU Hit Counter  │   │  Forward to Upstream LLM  │
                       │   Return Cached Response  │   │  Store Response in SQLite │
                       └───────────────────────────┘   └───────────────────────────┘
```

---

## 🚀 Key Engineering Highlights

- **Deterministic N-Gram Vector Engine**: Uses SHA-256 token hashing (`int(hashlib.sha256(w).hexdigest(), 16) % dim`) to produce 100% stable, platform-independent embeddings resilient to Python process restarts.
- **Unit Euclidean Normalization**: Normalizes vectors to length 1.0, simplifying cosine similarity to an ultra-fast dot product: $S = \sum a_i b_i$.
- **TokenOps ROI Economics**: Automatically computes prompt & completion tokens saved, estimated dollar savings across model tiers (GPT-4o, Claude 3.5 Sonnet, Llama-3), and latency saved.
- **LRU Eviction & TTL Support**: Auto-evicts oldest accessed entries when reaching `max_entries` capacity, keeping SQLite lightweight and bounded.
- **Dual-Path Fast B-Tree Index**: O(1) exact-match bypass before running full vector scans.

---

## ⚡ Quick Start & Commands

Built strictly on Python's **Standard Library**. No `pip install` required!

### 1. Interactive Web Dashboard
```bash
py main.py --serve
# Or specify custom port
py main.py --serve --port 8001
```
Open **`http://localhost:8001`** in any browser.

### 2. Run CLI Demonstration
```bash
py main.py
```

### 3. Run Latency Benchmark
```bash
py main.py --benchmark
# Tests 100 lookups against baseline LLM latency (typically >3,000x faster)
```

### 4. Query Cache from Terminal
```bash
py main.py --query "What is the capital of France?"
```

### 5. Run Unit Test Suite
```bash
py test_cache.py
# 9 tests running in <0.02s with 100% pass rate
```

---

## 📂 Project Structure

```
leke-local-token-cache/
├── cache.py               # Deterministic embedding engine, SQLite persistence, LRU/TTL
├── main.py                # CLI runner, benchmark harness, and server starter
├── server.py              # Embedded HTTP server & REST API (/api/query, /api/stats, /api/entries)
├── index.html             # Component-based dark-mode web dashboard
├── test_cache.py          # Unit test suite (9 tests)
├── SENIOR_DEMO_SCRIPT.md  # Presentation script & interview defense talking points
├── README.md              # Architectural documentation
└── static/
    ├── css/styles.css     # Design system tokens and card styling
    └── js/
        ├── api.js         # API client with offline simulation fallback
        ├── app.js         # Main application controller
        └── components/
            ├── QueryPanel.js    # Prompt input & threshold slider
            ├── MetricsPanel.js  # Live status, score gauge & latency comparison
            ├── StatsBar.js      # Cumulative tokens/dollars saved
            └── EntriesTable.js  # SQLite database table inspector
```
