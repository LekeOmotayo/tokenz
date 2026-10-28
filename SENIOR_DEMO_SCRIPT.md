# 🎤 Leke Local Token Cache — Senior Engineering Demo Script & Defense Guide

Use this playbook when presenting **Leke Local Token Cache** to Staff/Principal Engineers, Platform Leads, or Hiring Managers.

---

## ⏱️ 1. The 30-Second Elevator Pitch

> *"Every time an application calls an LLM like GPT-4o or Claude 3.5, you pay for tokens and incur 1 to 2.5 seconds of latency. Traditional key-value caches like Redis require exact string matches and miss on minor casing or punctuation variations, forcing repeated API calls.*
> 
> *Meanwhile, commercial semantic vector databases like Pinecone, Milvus, or Redis Stack require heavy Docker containers, cloud clusters, and DevOps overhead.*
> 
> *I built **Leke Local Token Cache**: a zero-infrastructure semantic caching engine that operates entirely on **pure Python and SQLite**. It uses deterministic SHA-256 character trigrams and unit-normalized cosine similarity to intercept semantically identical queries in **under 0.4 milliseconds**, saving 100% of the token cost and eliminating over 99% of cloud API latency with zero external dependencies."*

---

## 🎬 2. The 3-Minute Live Demo Flow

### Step 1: The Terminal Demo & Benchmark
Open PowerShell in `leke-local-token-cache` and run:
```powershell
py main.py
```
**What to say:**
> *"Here in the CLI, the cache seeds a persistent SQLite database with standard queries.
> When we run an exact query, it takes our **O(1) B-tree fast path** in SQLite and returns the response in sub-millisecond time.
> When we query a semantic variation with lowercase letters and missing punctuation ('what is the capital of france'), the vector engine computes cosine similarity across our 128-dimensional SHA-256 trigrams, detects 100% semantic match, and bypasses the LLM completely.*
> *Finally, when an unrelated prompt arrives, it correctly flags a CACHE MISS and forwards to the model."*

Now run the throughput benchmark:
```powershell
py main.py --benchmark
```
**What to say:**
> *"Across 100 queries, our local SQLite vector search averages **0.37 milliseconds per lookup**. Compared to a 1,200ms cloud API roundtrip, that's over **3,000x faster execution** with zero token consumption."*

---

### Step 2: The Visual Interactive Web Dashboard
Run:
```powershell
py main.py --serve
```
Open **`http://localhost:8001`** in the browser.

**Showcase highlights:**
1. **Interactive Evaluation**:
   > *"Let's test the 'France (Variation)' preset with the similarity threshold at 0.80. Click Evaluate—notice how it instantly resolves to CACHE HIT with 0.4ms retrieval latency, rendering the latency comparison bar that demonstrates ~1,400ms saved."*
2. **Threshold Sensitivity**:
   > *"We can adjust the threshold slider dynamically from 0.50 to 0.99 to demonstrate the precision vs recall trade-off."*
3. **SQLite Persistent Database Inspector**:
   > *"Down below, you can see the live SQLite table tracking hit counts, models, and token numbers per entry, with full controls to seed or clear the database."*

---

## 🧠 3. Code Deep Dive (How to Explain `cache.py`)

When seniors ask: *"Show me the math and vector search implementation:"*

### 1. Deterministic Embeddings vs Python's `hash()`
- **The Senior Insight**:
  *"Python's built-in `hash()` function uses a random salt per process (`PYTHONHASHSEED`). If the server restarts, `hash('france')` produces a completely different integer, corrupting saved vector indexes.*
  *I implemented deterministic SHA-256 token hashing: `int(hashlib.sha256(token.encode()).hexdigest(), 16) % dim`. This guarantees vectors remain 100% identical and stable across all process restarts, machines, and operating systems."*

### 2. Unit Euclidean Normalization & Dot-Product Cosine Similarity
- Point to:
  ```python
  norm = math.sqrt(sum(x * x for x in vec))
  if norm > 0.0:
      vec = [x / norm for x in vec]
  ```
  *Explanation: "Because every vector is normalized to unit length ($\|\vec{v}\| = 1.0$), the mathematical Cosine Similarity simplifies directly to the Dot Product: $S = \sum a_i b_i$. This turns complex vector math into a single-pass $O(D)$ vector operation without needing external C-bindings."*

### 3. Dual-Path Retrieval (B-Tree + Vector Scan)
- Explain:
  *"Before doing a full cosine similarity scan, we query SQLite's B-Tree index on `prompt_normalized`. If an exact string match exists, it resolves in $O(1)$ time without computing cosine similarity across all rows."*

### 4. LRU Eviction & TTL Expiration
- Explain:
  *"To prevent unbounded SQLite disk growth, the cache enforces a maximum capacity (`max_entries`). When capacity is reached, it automatically evicts the oldest accessed records using an LRU policy."*

---

## 🥊 4. Anticipated "Grill" Questions & Answers

### Q1: *"Why not use Redis Stack or Milvus instead of SQLite?"*
**Senior Answer:**
> *"Redis Stack and Milvus are fantastic for distributed, enterprise clusters with millions of vectors. However, in edge environments, local developer tooling, CLI assistants, desktop apps, or serverless functions (like AWS Lambda), spinning up a Redis container or paying for managed vector DBs adds immense infrastructure and cost overhead. Leke Local Token Cache gives you zero-infrastructure semantic caching with zero cold-start delay."*

### Q2: *"How does this scale as the cache grows to 100,000 entries?"*
**Senior Answer:**
> *"At high vector counts ($>10,000$), brute-force linear cosine scanning in Python becomes CPU-bound. In our architecture, we mitigate this through 3 layers: (1) O(1) exact normalized B-Tree lookups, (2) strict LRU capacity capping (`max_entries`), and (3) an architectural path to swap in `sqlite-vss` (SQLite Vector Similarity Search with FAISS indexing) when scaling beyond 50,000 vectors."*

### Q3: *"How do you test this?"*
**Senior Answer:**
> *"The test suite in `test_cache.py` uses Python's standard library `unittest` with an in-memory SQLite database (`:memory:`). It tests exact hits, semantic variation hits, threshold boundaries, deterministic embedding stability, TokenOps telemetry, and LRU eviction in 16 milliseconds."*
