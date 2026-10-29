"""
Comprehensive Unit Tests for Leke Local Token Cache
Tests deterministic vector embeddings, similarity thresholds, TokenOps ROI calculations,
LRU eviction, and exact match shortcuts using pure Python standard library.
"""

import unittest
from backend.core.cache import LocalVectorCache


class TestLocalVectorCache(unittest.TestCase):

    def setUp(self):
        # Use in-memory SQLite database for isolated test execution
        self.cache = LocalVectorCache(db_path=":memory:", similarity_threshold=0.80)

    def tearDown(self):
        self.cache.close()

    def test_cache_miss_on_empty(self):
        res = self.cache.get("hello world")
        self.assertIsNone(res)

    def test_cache_exact_hit(self):
        prompt = "How to reverse a string in Python?"
        response = "Use [::-1] slice."
        self.cache.set(prompt, response, model="gpt-4o")

        hit = self.cache.get(prompt)
        self.assertIsNotNone(hit)
        resp, score = hit
        self.assertEqual(resp, response)
        self.assertAlmostEqual(score, 1.0, places=2)

    def test_cache_semantic_variation_hit(self):
        # Seed cache with standard query
        self.cache.set("What is the capital of France?", "The capital is Paris.", model="gpt-4o")

        # Slight case/punctuation variations should match with high similarity
        hit = self.cache.get("what is the capital of France")
        self.assertIsNotNone(hit)
        self.assertEqual(hit[0], "The capital is Paris.")
        self.assertGreaterEqual(hit[1], 0.80)

    def test_cache_miss_on_unrelated_query(self):
        self.cache.set("What is the capital of France?", "Paris", model="gpt-4o")

        # Completely different topic should miss
        miss = self.cache.get("How to bake chocolate cookies?")
        self.assertIsNone(miss)

    def test_deterministic_embedding_stability(self):
        """Ensures identical vectors are produced across independent invocations."""
        text = "Semantic vector search with cosine similarity"
        vec1 = self.cache._compute_embedding(text)
        vec2 = self.cache._compute_embedding(text)
        self.assertEqual(vec1, vec2)
        # Verify unit Euclidean length (||v|| = 1.0)
        norm = sum(x * x for x in vec1)
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_tokenops_economics_telemetry(self):
        prompt = "Explain quantum computing in one sentence"
        resp = "Quantum computing uses superposition and entanglement to perform complex computations."
        self.cache.set(prompt, resp, model="gpt-4o", prompt_tokens=8, completion_tokens=15)

        detail = self.cache.get_detailed(prompt)
        self.assertIsNotNone(detail)
        self.assertEqual(detail.prompt_tokens_saved, 8)
        self.assertEqual(detail.completion_tokens_saved, 15)
        self.assertEqual(detail.total_tokens_saved, 23)
        self.assertGreater(detail.dollars_saved, 0.0)
        self.assertGreater(detail.latency_saved_ms, 500.0)
        self.assertTrue(detail.is_exact_match)

    def test_hit_count_increment(self):
        self.cache.set("Query A", "Response A")
        self.assertEqual(self.cache.stats()["total_cache_hits"], 0)

        self.cache.get("Query A")
        self.cache.get("Query A")
        self.assertEqual(self.cache.stats()["total_cache_hits"], 2)

    def test_lru_eviction(self):
        # Create cache with max capacity of 3 items
        small_cache = LocalVectorCache(db_path=":memory:", max_entries=3)
        small_cache.set("q1", "r1")
        small_cache.set("q2", "r2")
        small_cache.set("q3", "r3")

        # Adding a 4th triggers eviction of oldest entries
        small_cache.set("q4", "r4")
        entries = small_cache.list_entries()
        self.assertLessEqual(len(entries), 3)

    def test_clear_cache(self):
        self.cache.set("Key 1", "Val 1")
        self.cache.set("Key 2", "Val 2")
        self.assertEqual(self.cache.stats()["total_cached_items"], 2)

        self.cache.clear()
        self.assertEqual(self.cache.stats()["total_cached_items"], 0)
        self.assertEqual(self.cache.stats()["total_cache_hits"], 0)


if __name__ == "__main__":
    unittest.main()

