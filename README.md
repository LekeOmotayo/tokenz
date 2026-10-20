# Leke Local Token Cache — Zero-Infra Semantic Caching Engine

A pure Python + SQLite semantic caching gateway designed for local LLM token optimization. Sits in front of any LLM client to intercept semantically identical or near-duplicate queries, returning cached responses with zero network overhead and zero external dependencies (no Redis, no vector DB, no Docker required).

## Features
- **Zero Infrastructure**: Uses pure Python standard library (`sqlite3`, `math`, `json`).
- **Normalized Vector Embeddings**: Character n-gram hashing and unit-norm cosine similarity.
- **Configurable Threshold**: Tunable similarity boundary (`similarity_threshold`) to trade recall vs precision.
- **Hit-Count Telemetry**: Persistent statistics on token savings and query frequencies.

## Quick Start
```bash
# Run demo
python main.py

# Run test suite
pytest test_cache.py -v
```
