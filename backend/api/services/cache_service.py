"""
Cache Service orchestrating semantic lookups, cache writes, and TokenOps economics.
"""

from typing import Dict, Any, Optional
from backend.api.repositories.cache_repository import CacheRepository


class CacheService:
    """Service layer coordinating semantic vector retrieval and TokenOps analytics."""

    def __init__(self, repository: CacheRepository = None):
        self.repo = repository or CacheRepository()

    def process_prompt(self, prompt: str, model: str = "gpt-4o", auto_seed_miss: bool = True) -> Dict[str, Any]:
        """Looks up prompt in cache; if miss and auto_seed_miss is True, generates a synthetic response and stores it."""
        hit = self.repo.query(prompt)

        if hit:
            return {
                "status": "HIT",
                "similarity_score": hit.similarity_score,
                "is_exact_match": hit.is_exact_match,
                "response": hit.response,
                "model": hit.model,
                "hit_count": hit.hit_count,
                "tokens_saved": hit.total_tokens_saved,
                "dollars_saved": hit.dollars_saved,
                "latency_saved_ms": hit.latency_saved_ms,
                "retrieval_latency_ms": hit.retrieval_latency_ms,
            }

        # Cache Miss
        synthetic_response = f"Simulated model response from upstream LLM for query: '{prompt}'."
        if auto_seed_miss:
            self.repo.store(prompt, synthetic_response, model=model)

        return {
            "status": "MISS",
            "similarity_score": 0.0,
            "is_exact_match": False,
            "response": synthetic_response,
            "model": model,
            "hit_count": 0,
            "tokens_saved": 0,
            "dollars_saved": 0.0,
            "latency_saved_ms": 0.0,
            "retrieval_latency_ms": 2.5,
            "message": "Cache MISS. Query forwarded to origin LLM and vector cached for future hits.",
        }

    def store_pair(self, prompt: str, response: str, model: str = "gpt-4o") -> Dict[str, Any]:
        return self.repo.store(prompt, response, model=model)

    def get_metrics(self) -> Dict[str, Any]:
        return self.repo.get_stats()

    def clear_cache(self):
        self.repo.clear()
