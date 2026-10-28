"""
Leke Local Token Cache - Enterprise CLI & TokenOps Benchmark Runner
Demonstrates zero-infrastructure semantic caching, cost & latency economics,
and launches the interactive web dashboard.
"""

from __future__ import annotations

import argparse
import json
import sys
import time

# Ensure safe UTF-8 terminal encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from cache import LocalVectorCache, MODEL_PRICING


COLOR_RESET = "\033[0m"
COLOR_CYAN = "\033[96m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"


def print_banner():
    print(f"{COLOR_CYAN}{COLOR_BOLD}=" * 72)
    print("  \u26a1 LEKE LOCAL TOKEN CACHE — Zero-Infrastructure Semantic Caching Engine")
    print("     Pure Python + SQLite Semantic Gate for LLM Token Optimization")
    print(f"{COLOR_CYAN}=" * 72 + f"{COLOR_RESET}\n")


def seed_sample_database(cache: LocalVectorCache):
    samples = [
        (
            "What is the capital of France?",
            "The capital of France is Paris, located along the Seine River.",
            "gpt-4o",
            7, 14
        ),
        (
            "How do I sort a dictionary by value in Python?",
            "You can use sorted(my_dict.items(), key=lambda item: item[1]).",
            "gpt-4o",
            12, 16
        ),
        (
            "What is the difference between TCP and UDP?",
            "TCP is connection-oriented and guarantees ordered delivery via handshakes, whereas UDP is connectionless and prioritizes low latency without delivery guarantees.",
            "claude-3-5-sonnet",
            10, 32
        ),
        (
            "How do I create a virtual environment in Python?",
            "Run 'python -m venv .venv' and activate it using 'source .venv/bin/activate' or '.\\.venv\\Scripts\\activate' on Windows.",
            "gpt-4o-mini",
            11, 24
        ),
    ]

    for p, r, m, pt, ct in samples:
        cache.set(p, r, model=m, prompt_tokens=pt, completion_tokens=ct)


def run_demo():
    print_banner()
    cache = LocalVectorCache(db_path="semantic_cache.db", similarity_threshold=0.80)

    print(f"{COLOR_BOLD}[1] Seeding persistent SQLite semantic cache...{COLOR_RESET}")
    seed_sample_database(cache)
    stats = cache.stats()
    print(f"    ✔ Successfully initialized {stats['total_cached_items']} entries in SQLite.\n")

    # 1. Exact Hit
    print(f"{COLOR_BOLD}[2] Testing Exact Match Query (O(1) B-Tree Fast Path):{COLOR_RESET}")
    q1 = "What is the capital of France?"
    res1 = cache.get_detailed(q1)
    if res1:
        print(f"    Query:      '{COLOR_CYAN}{q1}{COLOR_RESET}'")
        print(f"    Verdict:    {COLOR_GREEN}{COLOR_BOLD}CACHE HIT (100% Token Savings){COLOR_RESET}")
        print(f"    Similarity: {res1.similarity_score:.4f} [Exact Match: {res1.is_exact_match}]")
        print(f"    Latency:    {COLOR_YELLOW}{res1.retrieval_latency_ms:.3f} ms{COLOR_RESET} (vs ~1,400ms LLM baseline)")
        print(f"    Tokens:     {res1.total_tokens_saved} tokens saved | ${res1.dollars_saved:.6f} saved")
        print(f"    Response:   {COLOR_DIM}{res1.response}{COLOR_RESET}\n")

    # 2. Semantic Variation Hit
    print(f"{COLOR_BOLD}[3] Testing Semantic Variation (Cosine Similarity on SHA-256 Trigrams):{COLOR_RESET}")
    q2 = "what is the capital of france"
    res2 = cache.get_detailed(q2)
    if res2:
        print(f"    Query:      '{COLOR_CYAN}{q2}{COLOR_RESET}'")
        print(f"    Verdict:    {COLOR_GREEN}{COLOR_BOLD}CACHE HIT (Cosine Sim >= {cache.similarity_threshold}){COLOR_RESET}")
        print(f"    Similarity: {COLOR_GREEN}{res2.similarity_score:.4f}{COLOR_RESET}")
        print(f"    Latency:    {COLOR_YELLOW}{res2.retrieval_latency_ms:.3f} ms{COLOR_RESET}")
        print(f"    Response:   {COLOR_DIM}{res2.response}{COLOR_RESET}\n")

    # 3. Cache Miss (Below threshold)
    print(f"{COLOR_BOLD}[4] Testing Unrelated Query (Cache Miss):{COLOR_RESET}")
    q3 = "What is the recipe for authentic Neapolitan pizza?"
    res3 = cache.get_detailed(q3)
    if not res3:
        print(f"    Query:      '{COLOR_CYAN}{q3}{COLOR_RESET}'")
        print(f"    Verdict:    {COLOR_RED}{COLOR_BOLD}CACHE MISS{COLOR_RESET} (Forwarding to upstream LLM provider)")
        print(f"    Action:     LLM computes response -> Stored in SQLite for future queries.\n")

    # 4. Telemetry Summary
    final_stats = cache.stats()
    print(f"{COLOR_BOLD}[5] Real-Time TokenOps Telemetry & ROI Summary:{COLOR_RESET}")
    print(f"    Total Queries Evaluated:   {final_stats['total_queries']}")
    print(f"    Total Cache Hits:          {COLOR_GREEN}{final_stats['total_cache_hits']}{COLOR_RESET}")
    print(f"    Hit Rate:                  {COLOR_CYAN}{final_stats['hit_rate_pct']}%{COLOR_RESET}")
    print(f"    Cumulative Tokens Saved:   {COLOR_YELLOW}{final_stats['total_tokens_saved']} tokens{COLOR_RESET}")
    print(f"    Cumulative Dollars Saved:  {COLOR_GREEN}${final_stats['est_dollars_saved']:.4f}{COLOR_RESET}")
    print(f"    Cumulative Latency Saved:  {COLOR_CYAN}{final_stats['est_time_saved_sec']:.2f} seconds{COLOR_RESET}\n")

    print(f"{COLOR_BOLD}Next steps:{COLOR_RESET}")
    print("  • Launch visual dashboard:   py main.py --serve")
    print("  • Run latency benchmark:     py main.py --benchmark")
    print("  • Query CLI cache:           py main.py --query \"your prompt here\"")


def run_benchmark(n_queries: int = 100):
    print_banner()
    cache = LocalVectorCache(db_path=":memory:", similarity_threshold=0.80)
    seed_sample_database(cache)

    print(f"Running benchmark with {n_queries} repeated semantic queries against in-memory SQLite...\n")
    test_queries = [
        "what is the capital of France?",
        "how to sort a dict by value in python",
        "difference between tcp and udp protocols",
        "how do i create virtualenv in python"
    ]

    start = time.perf_counter()
    hits = 0
    for i in range(n_queries):
        q = test_queries[i % len(test_queries)]
        hit = cache.get(q)
        if hit:
            hits += 1
    total_time = (time.perf_counter() - start) * 1000.0
    avg_latency = total_time / n_queries

    # Simulated LLM comparison (assuming 1,200ms per un-cached API call)
    sim_llm_time_ms = n_queries * 1200.0

    print(f"Benchmark Results ({n_queries} lookups):")
    print(f"  • Total Cache Hits:        {COLOR_GREEN}{hits}/{n_queries} ({hits/n_queries*100:.1f}%){COLOR_RESET}")
    print(f"  • Total Retrieval Time:    {COLOR_YELLOW}{total_time:.2f} ms{COLOR_RESET}")
    print(f"  • Avg Latency per Query:   {COLOR_CYAN}{avg_latency:.3f} ms{COLOR_RESET}")
    print(f"  • Baseline LLM Time:       {COLOR_RED}{sim_llm_time_ms:,.0f} ms{COLOR_RESET}")
    print(f"  • Latency Speedup:         {COLOR_GREEN}{sim_llm_time_ms / total_time:,.0f}x faster{COLOR_RESET}\n")


def start_server(port: int = 8001):
    from server import run_server
    run_server(port=port)


def main():
    parser = argparse.ArgumentParser(
        description="Leke Local Token Cache — Zero-Infra Semantic Caching Engine"
    )
    parser.add_argument("--query", "-q", type=str, help="Evaluate a single prompt against cache")
    parser.add_argument("--benchmark", "-b", action="store_true", help="Run latency and throughput benchmark")
    parser.add_argument("--stats", "-s", action="store_true", help="Print persistent cache statistics and ROI")
    parser.add_argument("--seed", action="store_true", help="Seed persistent database with standard knowledge base")
    parser.add_argument("--clear", action="store_true", help="Clear all records from persistent cache")
    parser.add_argument("--serve", action="store_true", help="Launch interactive web demo dashboard on http://localhost:8001")
    parser.add_argument("--port", type=int, default=8001, help="Port for web dashboard (default: 8001)")

    args = parser.parse_args()

    if args.serve:
        start_server(port=args.port)
        sys.exit(0)

    if args.benchmark:
        run_benchmark()
        sys.exit(0)

    cache = LocalVectorCache(db_path="semantic_cache.db", similarity_threshold=0.80)

    if args.clear:
        cache.clear()
        print("✔ Persistent SQLite cache cleared successfully.")
        sys.exit(0)

    if args.seed:
        seed_sample_database(cache)
        print("✔ Persistent SQLite cache seeded successfully.")
        sys.exit(0)

    if args.stats:
        print_banner()
        print(json.dumps(cache.stats(), indent=2))
        sys.exit(0)

    if args.query:
        print_banner()
        res = cache.get_detailed(args.query)
        if res:
            print(f"{COLOR_GREEN}{COLOR_BOLD}✔ CACHE HIT{COLOR_RESET} (Score: {res.similarity_score:.4f}, Latency: {res.retrieval_latency_ms:.3f}ms)")
            print(f"Model: {res.model} | Saved: {res.total_tokens_saved} tokens (${res.dollars_saved:.6f})")
            print(f"\nResponse:\n{res.response}")
        else:
            print(f"{COLOR_RED}{COLOR_BOLD}✖ CACHE MISS{COLOR_RESET} (No matching response found above threshold {cache.similarity_threshold})")
        sys.exit(0)

    # Default action: run the complete demo
    run_demo()


if __name__ == "__main__":
    main()
