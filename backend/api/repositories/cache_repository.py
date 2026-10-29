"""
Cache Repository for Leke Local Token Cache.
Manages vector persistence and SQLite storage lifecycle.
"""

from typing import Dict, Any, Optional, Tuple, List
from backend.core.cache import LocalVectorCache, CacheHitResult, MODEL_PRICING


class CacheRepository:
    """Manages the underlying LocalVectorCache instance."""

    def __init__(self, db_path: str = "semantic_cache.db", similarity_threshold: float = 0.85):
        self.cache = LocalVectorCache(db_path=db_path, similarity_threshold=similarity_threshold)

    def query(self, prompt: str) -> Optional[CacheHitResult]:
        """Queries for exact or semantic vector hit."""
        return self.cache.get_with_result(prompt)

    def store(self, prompt: str, response: str, model: str = "gpt-4o") -> Dict[str, Any]:
        """Stores a prompt-response vector pair."""
        return self.cache.set(prompt, response, model=model)

    def get_stats(self) -> Dict[str, Any]:
        """Returns cumulative cache metrics and TokenOps savings."""
        return self.cache.get_stats()

    def clear(self):
        """Clears all cached vectors and resets metrics."""
        self.cache.clear()

    def get_pricing(self) -> Dict[str, Dict[str, float]]:
        """Returns LLM model token pricing references."""
        return MODEL_PRICING

    def close(self):
        self.cache.close()
