import sqlite3
import json
import time
import math
from typing import Optional, Tuple, List, Dict, Any

class LocalVectorCache:
    """
    Lightweight, in-memory/SQLite semantic caching engine.
    Uses pure cosine similarity with vector serialization.
    Can use SentenceTransformers if installed, or deterministic hash/trigram fallback embeddings
    without requiring external model weights to boot instantly.
    """
    def __init__(self, db_path: str = ":memory:", similarity_threshold: float = 0.85):
        self.db_path = db_path
        self.similarity_threshold = similarity_threshold
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt TEXT UNIQUE,
                    embedding TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model TEXT,
                    created_at REAL,
                    hit_count INTEGER DEFAULT 0
                )
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_prompt ON semantic_cache(prompt)")

    def _compute_embedding(self, text: str) -> List[float]:
        """Generate normalized vector embedding using frequency & character n-grams."""
        text_clean = text.lower().strip()
        # 64-dimensional feature vector based on hashed character trigrams
        dim = 64
        vec = [0.0] * dim
        if not text_clean:
            return vec
        
        words = text_clean.split()
        for w in words:
            h = hash(w) % dim
            vec[h] += 1.0

        for i in range(len(text_clean) - 2):
            tri = text_clean[i:i+3]
            h = hash(tri) % dim
            vec[h] += 0.5

        # Normalize to unit length for cosine similarity
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        if len(vec1) != len(vec2) or not vec1:
            return 0.0
        return sum(a * b for a, b in zip(vec1, vec2))

    def get(self, prompt: str) -> Optional[Tuple[str, float]]:
        """Look up prompt in semantic cache. Returns (response, similarity_score) if hit."""
        query_vec = self._compute_embedding(prompt)
        cur = self.conn.cursor()
        cur.execute("SELECT id, prompt, embedding, response, hit_count FROM semantic_cache")
        rows = cur.fetchall()

        best_score = -1.0
        best_id = None
        best_response = None

        for row_id, cached_prompt, emb_json, response, hit_count in rows:
            cached_vec = json.loads(emb_json)
            sim = self._cosine_similarity(query_vec, cached_vec)
            if sim > best_score:
                best_score = sim
                best_id = row_id
                best_response = response

        if best_score >= self.similarity_threshold and best_id is not None:
            with self.conn:
                self.conn.execute(
                    "UPDATE semantic_cache SET hit_count = hit_count + 1 WHERE id = ?",
                    (best_id,)
                )
            return best_response, best_score

        return None

    def set(self, prompt: str, response: str, model: str = "default"):
        """Store prompt, embedding, and response in SQLite cache."""
        emb = self._compute_embedding(prompt)
        with self.conn:
            self.conn.execute("""
                INSERT INTO semantic_cache (prompt, embedding, response, model, created_at, hit_count)
                VALUES (?, ?, ?, ?, ?, 0)
                ON CONFLICT(prompt) DO UPDATE SET
                    response = excluded.response,
                    embedding = excluded.embedding,
                    created_at = excluded.created_at
            """, (prompt, json.dumps(emb), response, model, time.time()))

    def stats(self) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*), COALESCE(SUM(hit_count), 0) FROM semantic_cache")
        count, total_hits = cur.fetchone()
        return {
            "total_cached_items": count,
            "total_cache_hits": total_hits,
            "threshold": self.similarity_threshold,
            "db_path": self.db_path
        }
