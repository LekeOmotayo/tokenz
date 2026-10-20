from cache import LocalVectorCache

def main():
    print("=" * 60)
    print(">> Leke Local Token Cache - Zero-Infra Semantic Caching Engine")
    print("=" * 60)

    cache = LocalVectorCache(db_path="semantic_cache.db", similarity_threshold=0.80)

    # Prime cache with queries
    print("\n[1] Seeding cache with responses...")
    cache.set(
        "What is the capital of France?",
        "The capital of France is Paris.",
        model="gpt-4o-mini"
    )
    cache.set(
        "How do I sort a list in Python?",
        "Use sorted(my_list) or my_list.sort().",
        model="gpt-4o-mini"
    )
    print("Cached 2 distinct prompts in SQLite.")

    # Exact query
    print("\n[2] Testing Exact Hit:")
    query1 = "What is the capital of France?"
    result = cache.get(query1)
    if result:
        resp, score = result
        print(f" Query:    '{query1}'")
        print(f" HIT! Score: {score:.4f} -> Response: '{resp}'")
    else:
        print(" MISS!")

    # Semantic variation query
    print("\n[3] Testing Semantic Similarity Hit:")
    query2 = "what is the capital of France"
    result = cache.get(query2)
    if result:
        resp, score = result
        print(f" Query:    '{query2}'")
        print(f" HIT! Score: {score:.4f} -> Response: '{resp}'")
    else:
        print(" MISS!")

    # Unrelated query
    print("\n[4] Testing Cache Miss (Below Threshold):")
    query3 = "What is the recipe for chocolate cake?"
    result = cache.get(query3)
    if result:
        resp, score = result
        print(f" HIT! Score: {score:.4f}")
    else:
        print(f" Query:    '{query3}' -> MISS (Fresh LLM invocation required)")

    print("\n[5] Cache Telemetry:")
    print(cache.stats())
    print("\nDone! Instant local execution verified.")

if __name__ == "__main__":
    main()
