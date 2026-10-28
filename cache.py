"""
Leke Local Token Cache - Enterprise Zero-Infrastructure Semantic Caching Engine
Combines deterministic vector embeddings, SQLite persistence, LRU/TTL lifecycle,
and TokenOps economics (tokens, dollars, and latency saved) with zero external dependencies.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# TokenOps Cost Estimation Reference (Per 1 Million Tokens)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00, "est_latency_ms": 1400.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "est_latency_ms": 750.0},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00, "est_latency_ms": 1600.0},
    "llama-3-70b": {"input": 0.90, "output": 0.90, "est_latency_ms": 900.0},
    "default": {"input": 1.00, "output": 3.00, "est_latency_ms": 1000.0},
}


@dataclass
class CacheHitResult:
    response: str
    similarity_score: float
    model: str
    hit_count: int
    prompt_tokens_saved: int
    completion_tokens_saved: int
    dollars_saved: float
    latency_saved_ms: float
    retrieval_latency_ms: float
    is_exact_match: bool

    @property
    def total_tokens_saved(self) -> int:
        return self.prompt_tokens_saved + self.completion_tokens_saved

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response,
            "similarity_score": round(self.similarity_score, 4),
            "model": self.model,
            "hit_count": self.hit_count,
            "prompt_tokens_saved": self.prompt_tokens_saved,
            "completion_tokens_saved": self.completion_tokens_saved,
            "total_tokens_saved": self.total_tokens_saved,
            "dollars_saved": round(self.dollars_saved, 6),
            "latency_saved_ms": round(self.latency_saved_ms, 2),
            "retrieval_latency_ms": round(self.retrieval_latency_ms, 3),
            "is_exact_match": self.is_exact_match,
        }


class LocalVectorCache:
    """
    Production-grade local semantic vector cache backed by SQLite.
    Features:
    - Deterministic N-Gram & Word Hashing (process-restart resilient)
    - Unit-normalized Cosine Similarity matching
    - Fast exact-match O(1) index bypass
    - Configurable similarity threshold (0.0 to 1.0)
    - LRU eviction & optional TTL expiration
    - Real-time TokenOps telemetry (tokens, dollars, latency)
    - Zero external dependencies (pure Python standard library)
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        similarity_threshold: float = 0.85,
        vector_dim: int = 128,
        max_entries: int = 5000,
        default_ttl_seconds: Optional[int] = None,
    ):
        self.db_path = db_path
        self.similarity_threshold = float(similarity_threshold)
        self.vector_dim = vector_dim
        self.max_entries = max_entries
        self.default_ttl_seconds = default_ttl_seconds

        # In-memory statistics counters for real-time tracking
        self._total_queries = 0
        self._total_hits = 0
        self._total_misses = 0

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        with self.conn:
            # Enable SQLite Write-Ahead Logging for concurrency if using file database
            if self.db_path != ":memory:":
                try:
                    self.conn.execute("PRAGMA journal_mode=WAL;")
                except sqlite3.OperationalError:
                    pass

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt TEXT UNIQUE NOT NULL,
                    prompt_normalized TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model TEXT NOT NULL DEFAULT 'default',
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    created_at REAL NOT NULL,
                    last_accessed_at REAL NOT NULL,
                    hit_count INTEGER DEFAULT 0,
                    ttl_seconds INTEGER
                )
            """)

            # Auto-migrate legacy schema if table already existed on disk
            cur = self.conn.cursor()
            cur.execute("PRAGMA table_info(semantic_cache)")
            existing_cols = {row[1] for row in cur.fetchall()}
            if existing_cols:
                if "prompt_normalized" not in existing_cols:
                    self.conn.execute("ALTER TABLE semantic_cache ADD COLUMN prompt_normalized TEXT DEFAULT ''")
                    self.conn.execute("UPDATE semantic_cache SET prompt_normalized = lower(trim(prompt))")
                if "prompt_tokens" not in existing_cols:
                    self.conn.execute("ALTER TABLE semantic_cache ADD COLUMN prompt_tokens INTEGER DEFAULT 0")
                if "completion_tokens" not in existing_cols:
                    self.conn.execute("ALTER TABLE semantic_cache ADD COLUMN completion_tokens INTEGER DEFAULT 0")
                if "last_accessed_at" not in existing_cols:
                    self.conn.execute("ALTER TABLE semantic_cache ADD COLUMN last_accessed_at REAL DEFAULT 0")
                    self.conn.execute("UPDATE semantic_cache SET last_accessed_at = created_at")
                if "ttl_seconds" not in existing_cols:
                    self.conn.execute("ALTER TABLE semantic_cache ADD COLUMN ttl_seconds INTEGER")

            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_prompt_norm ON semantic_cache(prompt_normalized)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_last_accessed ON semantic_cache(last_accessed_at)")

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Strips excessive punctuation, collapses whitespace, and lowercases text."""
        cleaned = text.lower().strip()
        cleaned = re.sub(r"[^\w\s]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimates token count (~4 characters per token proxy)."""
        if not text:
            return 0
        return max(1, math.ceil(len(text) / 4.0))

    def _compute_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic, normalized vector embedding using SHA-256 token hashing.
        Unlike Python's built-in hash() which randomizes per process, this produces
        100% identical vectors across all process restarts and platforms.
        """
        clean = self._normalize_text(text)
        vec = [0.0] * self.vector_dim
        if not clean:
            return vec

        # 1. Word unigrams (weight 1.0)
        words = clean.split()
        for w in words:
            h = int(hashlib.sha256(w.encode("utf-8")).hexdigest(), 16) % self.vector_dim
            vec[h] += 1.0

        # 2. Word bigrams (weight 1.2 for phrase context)
        for i in range(len(words) - 1):
            bigram = f"{words[i]}_{words[i+1]}"
            h = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest(), 16) % self.vector_dim
            vec[h] += 1.2

        # 3. Character trigrams (weight 0.4 for spelling variations)
        compact = clean.replace(" ", "")
        for i in range(len(compact) - 2):
            tri = compact[i:i+3]
            h = int(hashlib.sha256(tri.encode("utf-8")).hexdigest(), 16) % self.vector_dim
            vec[h] += 0.4

        # 4. Normalize to unit Euclidean norm for fast dot-product cosine similarity
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0.0:
            vec = [x / norm for x in vec]
        return vec

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Computes dot product between two unit-normalized vectors."""
        if len(vec1) != len(vec2) or not vec1:
            return 0.0
        return sum(a * b for a, b in zip(vec1, vec2))

    def get(self, prompt: str) -> Optional[Tuple[str, float]]:
        """
        Standard look-up returning (response, similarity_score) if hit, or None if miss.
        Preserves backward compatibility with existing tests.
        """
        detail = self.get_detailed(prompt)
        if detail:
            return detail.response, detail.similarity_score
        return None

    def get_detailed(self, prompt: str) -> Optional[CacheHitResult]:
        """
        Evaluates prompt against semantic cache with full TokenOps economics.
        Returns CacheHitResult with similarity score, tokens saved, dollars saved, and latency saved.
        """
        start_time = time.perf_counter()
        self._total_queries += 1
        now = time.time()
        norm_prompt = self._normalize_text(prompt)

        # 1. Fast Path: Exact normalized match via SQLite B-Tree index (O(1) look-up)
        cur = self.conn.cursor()
        cur.execute(
            """SELECT id, response, model, prompt_tokens, completion_tokens, hit_count, created_at, ttl_seconds
               FROM semantic_cache
               WHERE prompt_normalized = ?""",
            (norm_prompt,)
        )
        exact_row = cur.fetchone()

        if exact_row:
            row_id, resp, model, p_tokens, c_tokens, hits, created, ttl = exact_row
            # Check TTL
            if ttl is None or (now - created) <= ttl:
                hits += 1
                with self.conn:
                    self.conn.execute(
                        "UPDATE semantic_cache SET hit_count = hit_count + 1, last_accessed_at = ? WHERE id = ?",
                        (now, row_id)
                    )
                self._total_hits += 1
                return self._build_hit_result(
                    resp, 1.0, model, hits, p_tokens, c_tokens, start_time, is_exact=True
                )

        # 2. Semantic Vector Path: Cosine similarity scan across candidates
        query_vec = self._compute_embedding(prompt)
        cur.execute(
            """SELECT id, prompt, embedding, response, model, prompt_tokens, completion_tokens, hit_count, created_at, ttl_seconds
               FROM semantic_cache"""
        )
        rows = cur.fetchall()

        best_score = -1.0
        best_row = None

        for r in rows:
            row_id, p_text, emb_json, resp, model, p_tokens, c_tokens, hits, created, ttl = r
            # Check TTL expiration
            if ttl is not None and (now - created) > ttl:
                continue

            cached_vec = json.loads(emb_json)
            sim = self._cosine_similarity(query_vec, cached_vec)
            if sim > best_score:
                best_score = sim
                best_row = r

        if best_score >= self.similarity_threshold and best_row is not None:
            row_id, _, _, resp, model, p_tokens, c_tokens, hits, _, _ = best_row
            hits += 1
            with self.conn:
                self.conn.execute(
                    "UPDATE semantic_cache SET hit_count = hit_count + 1, last_accessed_at = ? WHERE id = ?",
                    (now, row_id)
                )
            self._total_hits += 1
            return self._build_hit_result(
                resp, best_score, model, hits, p_tokens, c_tokens, start_time, is_exact=False
            )

        self._total_misses += 1
        return None

    def _build_hit_result(
        self,
        response: str,
        score: float,
        model: str,
        hit_count: int,
        p_tokens: int,
        c_tokens: int,
        start_time: float,
        is_exact: bool,
    ) -> CacheHitResult:
        retrieval_ms = (time.perf_counter() - start_time) * 1000.0
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])

        # Calculate cost savings
        input_cost = (p_tokens / 1_000_000.0) * pricing["input"]
        output_cost = (c_tokens / 1_000_000.0) * pricing["output"]
        dollars_saved = input_cost + output_cost

        # Calculate latency savings (LLM baseline ms minus local retrieval ms)
        est_llm_latency = pricing["est_latency_ms"]
        latency_saved = max(0.0, est_llm_latency - retrieval_ms)

        return CacheHitResult(
            response=response,
            similarity_score=score,
            model=model,
            hit_count=hit_count,
            prompt_tokens_saved=p_tokens,
            completion_tokens_saved=c_tokens,
            dollars_saved=dollars_saved,
            latency_saved_ms=latency_saved,
            retrieval_latency_ms=retrieval_ms,
            is_exact_match=is_exact,
        )

    def set(
        self,
        prompt: str,
        response: str,
        model: str = "default",
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        ttl_seconds: Optional[int] = None,
    ):
        """Stores prompt, deterministic embedding, and response in SQLite cache."""
        now = time.time()
        norm_prompt = self._normalize_text(prompt)
        emb = self._compute_embedding(prompt)

        p_tokens = prompt_tokens if prompt_tokens is not None else self._estimate_tokens(prompt)
        c_tokens = completion_tokens if completion_tokens is not None else self._estimate_tokens(response)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds

        with self.conn:
            # Enforce max entries via LRU eviction
            self._evict_if_needed()

            self.conn.execute("""
                INSERT INTO semantic_cache (
                    prompt, prompt_normalized, embedding, response, model,
                    prompt_tokens, completion_tokens, created_at, last_accessed_at, hit_count, ttl_seconds
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                ON CONFLICT(prompt) DO UPDATE SET
                    prompt_normalized = excluded.prompt_normalized,
                    response = excluded.response,
                    embedding = excluded.embedding,
                    model = excluded.model,
                    prompt_tokens = excluded.prompt_tokens,
                    completion_tokens = excluded.completion_tokens,
                    last_accessed_at = excluded.last_accessed_at,
                    ttl_seconds = excluded.ttl_seconds
            """, (
                prompt, norm_prompt, json.dumps(emb), response, model,
                p_tokens, c_tokens, now, now, ttl
            ))

    def _evict_if_needed(self):
        """Evicts oldest accessed entries (LRU) when reaching max_entries."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM semantic_cache")
        count = cur.fetchone()[0]

        if count >= self.max_entries:
            # Remove oldest 10% of entries
            evict_count = max(1, math.ceil(self.max_entries * 0.1))
            self.conn.execute(
                """DELETE FROM semantic_cache WHERE id IN (
                    SELECT id FROM semantic_cache ORDER BY last_accessed_at ASC LIMIT ?
                )""",
                (evict_count,)
            )

    def list_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns list of cached entries for UI visualization."""
        cur = self.conn.cursor()
        cur.execute(
            """SELECT id, prompt, response, model, hit_count, prompt_tokens, completion_tokens, created_at
               FROM semantic_cache ORDER BY last_accessed_at DESC LIMIT ?""",
            (limit,)
        )
        entries = []
        for r in cur.fetchall():
            entries.append({
                "id": r[0],
                "prompt": r[1],
                "response": r[2],
                "model": r[3],
                "hit_count": r[4],
                "prompt_tokens": r[5],
                "completion_tokens": r[6],
                "created_at": r[7],
            })
        return entries

    def clear(self):
        """Flushes all entries from the cache."""
        with self.conn:
            self.conn.execute("DELETE FROM semantic_cache")
        self._total_queries = 0
        self._total_hits = 0
        self._total_misses = 0

    def stats(self) -> Dict[str, Any]:
        """Returns comprehensive telemetry including token savings and ROI metrics."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT 
                COUNT(*),
                COALESCE(SUM(hit_count), 0),
                COALESCE(SUM(hit_count * prompt_tokens), 0),
                COALESCE(SUM(hit_count * completion_tokens), 0)
            FROM semantic_cache
        """)
        count, db_hits, prompt_tokens_saved, comp_tokens_saved = cur.fetchone()

        total_queries = max(self._total_queries, db_hits)
        hit_rate = (db_hits / total_queries * 100.0) if total_queries > 0 else 0.0

        # Estimate dollar savings across saved tokens
        total_tokens = prompt_tokens_saved + comp_tokens_saved
        # Baseline blending rate ($2.50 per 1M tokens)
        est_dollars_saved = (total_tokens / 1_000_000.0) * 2.50

        # Estimated latency saved (~1.2s per hit)
        est_time_saved_sec = db_hits * 1.2

        return {
            "total_cached_items": count,
            "total_cache_hits": db_hits,
            "total_queries": total_queries,
            "hit_rate_pct": round(hit_rate, 2),
            "total_tokens_saved": total_tokens,
            "prompt_tokens_saved": prompt_tokens_saved,
            "completion_tokens_saved": comp_tokens_saved,
            "est_dollars_saved": round(est_dollars_saved, 4),
            "est_time_saved_sec": round(est_time_saved_sec, 2),
            "threshold": self.similarity_threshold,
            "vector_dim": self.vector_dim,
            "db_path": self.db_path,
        }

    def close(self):
        """Closes the underlying SQLite database connection."""
        if hasattr(self, "conn") and self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
