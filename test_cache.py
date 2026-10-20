import pytest
from cache import LocalVectorCache

def test_cache_miss_on_empty():
    cache = LocalVectorCache()
    assert cache.get("hello world") is None

def test_cache_exact_hit():
    cache = LocalVectorCache()
    cache.set("How to reverse a string?", "Use [::-1] slice.", model="gpt-4o")
    res = cache.get("How to reverse a string?")
    assert res is not None
    response, score = res
    assert response == "Use [::-1] slice."
    assert score >= 0.99

def test_cache_similarity_threshold():
    cache = LocalVectorCache(similarity_threshold=0.85)
    cache.set("What is the capital of France?", "Paris", model="gpt-4o")
    
    # Slight variation passes threshold
    hit = cache.get("what is the capital of France?")
    assert hit is not None
    assert hit[0] == "Paris"

    # Completely different query misses
    miss = cache.get("How to cook rice?")
    assert miss is None

def test_hit_count_increment():
    cache = LocalVectorCache()
    cache.set("Test query", "Test response")
    assert cache.stats()["total_cache_hits"] == 0
    cache.get("Test query")
    cache.get("Test query")
    assert cache.stats()["total_cache_hits"] == 2
