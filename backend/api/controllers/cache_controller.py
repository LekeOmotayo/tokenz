"""
HTTP Controller for Leke Local Token Cache endpoints.
"""

from typing import Dict, Any
from backend.api.services.cache_service import CacheService


class CacheController:
    """Handles REST HTTP endpoints for semantic caching."""

    def __init__(self, service: CacheService = None):
        self.service = service or CacheService()

    def handle_query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = payload.get("prompt", "").strip()
        model = payload.get("model", "gpt-4o")
        auto_seed = payload.get("auto_seed", True)

        if not prompt:
            return {"status": "error", "message": "Prompt cannot be empty"}

        return self.service.process_prompt(prompt, model=model, auto_seed_miss=auto_seed)

    def handle_store(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = payload.get("prompt", "").strip()
        response = payload.get("response", "").strip()
        model = payload.get("model", "gpt-4o")

        if not prompt or not response:
            return {"status": "error", "message": "Both prompt and response are required"}

        res = self.service.store_pair(prompt, response, model=model)
        return {"status": "success", "result": res}

    def handle_stats(self) -> Dict[str, Any]:
        return {
            "status": "success",
            "stats": self.service.get_metrics()
        }

    def handle_clear(self) -> Dict[str, Any]:
        self.service.clear_cache()
        return {"status": "success", "message": "Cache database and metrics wiped successfully"}
