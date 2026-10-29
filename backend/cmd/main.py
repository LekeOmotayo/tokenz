"""
CLI and Web Server entrypoint for Leke Local Token Cache.
Usage:
  python -m backend.cmd.main --serve        # Launch web dashboard on port 8098
  python -m backend.cmd.main --query "..."  # Query cache via CLI
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.server import start_server
from backend.core.cache import LocalVectorCache


def main():
    parser = argparse.ArgumentParser(description="Leke Local Token Cache & Semantic LLM Accelerator")
    parser.add_argument("--serve", "-s", action="store_true", help="Launch interactive web console on port 8098")
    parser.add_argument("--port", "-p", type=int, default=8098, help="Port for web server (default: 8098)")
    parser.add_argument("--query", "-q", type=str, help="Query string to check against semantic cache")
    parser.add_argument("--stats", action="store_true", help="Display cumulative TokenOps metrics")

    args = parser.parse_args()

    if args.serve or (not args.query and not args.stats):
        start_server(args.port)
        return

    cache = LocalVectorCache()

    if args.stats:
        stats = cache.get_stats()
        print("\n📊 Cumulative TokenOps Economics:")
        print(json.dumps(stats, indent=2))
        return

    if args.query:
        hit = cache.get_with_result(args.query)
        if hit:
            print(f"\n⚡ Cache HIT ({hit.similarity_score:.4f} similarity):")
            print(f"   Model:        {hit.model}")
            print(f"   Tokens Saved: {hit.total_tokens_saved}")
            print(f"   Cost Saved:   ${hit.dollars_saved:.6f}")
            print(f"   Response:     {hit.response}")
        else:
            print(f"\n❌ Cache MISS for: '{args.query}'")


if __name__ == "__main__":
    main()
