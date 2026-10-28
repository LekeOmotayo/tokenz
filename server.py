"""
Leke Local Token Cache - Lightweight Embedded Demo Server
Serves the interactive web UI and provides REST API endpoints for semantic caching,
TokenOps telemetry, and SQLite entry inspection.
Standard library only (http.server) - zero external dependencies required.
"""

from __future__ import annotations

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# Ensure safe UTF-8 terminal encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from cache import LocalVectorCache, MODEL_PRICING

HERE = Path(__file__).parent.resolve()
DB_FILE = HERE / "semantic_cache.db"
cache = LocalVectorCache(db_path=str(DB_FILE), similarity_threshold=0.80)


class TokenCacheHTTPHandler(BaseHTTPRequestHandler):

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. API: Telemetry Stats
        if path == "/api/stats":
            stats_data = cache.stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(stats_data).encode("utf-8"))
            return

        # 2. API: List Cached Entries
        if path == "/api/entries":
            entries = cache.list_entries(limit=50)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(entries).encode("utf-8"))
            return

        # 3. Serve static files (/static/...)
        if path.startswith("/static/"):
            rel_path = path.lstrip("/")
            file_path = HERE / rel_path
            if file_path.exists() and file_path.is_file():
                content = file_path.read_bytes()
                mime = "text/plain"
                if path.endswith(".css"):
                    mime = "text/css; charset=utf-8"
                elif path.endswith(".js"):
                    mime = "application/javascript; charset=utf-8"
                elif path.endswith(".json"):
                    mime = "application/json; charset=utf-8"
                elif path.endswith(".html"):
                    mime = "text/html; charset=utf-8"

                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
                return

        # 4. Serve index.html
        if path in ("/", "/index.html"):
            index_path = HERE / "index.html"
            if index_path.exists():
                content = index_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
                return

        # 5. 404 Not Found
        self.send_response(404)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Resource not found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        # 1. API: Query Cache
        if path == "/api/query":
            prompt = payload.get("prompt", "").strip()
            threshold = payload.get("threshold")
            if threshold is not None:
                try:
                    cache.similarity_threshold = float(threshold)
                except ValueError:
                    pass

            if not prompt:
                self.send_response(400)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Empty prompt"}).encode("utf-8"))
                return

            res = cache.get_detailed(prompt)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()

            if res:
                out = {
                    "hit": True,
                    "result": res.to_dict(),
                    "stats": cache.stats(),
                }
            else:
                out = {
                    "hit": False,
                    "message": "Cache Miss: No cached response exceeds similarity threshold.",
                    "stats": cache.stats(),
                }
            self.wfile.write(json.dumps(out).encode("utf-8"))
            return

        # 2. API: Store New Entry
        if path == "/api/set":
            prompt = payload.get("prompt", "").strip()
            response = payload.get("response", "").strip()
            model = payload.get("model", "gpt-4o")

            if prompt and response:
                cache.set(prompt, response, model=model)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "stats": cache.stats()}).encode("utf-8"))
                return

        # 3. API: Seed standard entries
        if path == "/api/seed":
            from main import seed_sample_database
            seed_sample_database(cache)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "stats": cache.stats()}).encode("utf-8"))
            return

        # 4. API: Clear cache
        if path == "/api/clear":
            cache.clear()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "stats": cache.stats()}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        # Clean terminal logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {args[0]} {args[1]} -> {args[2]}\n")


def run_server(port: int = 8001, host: str = "127.0.0.1"):
    server_address = (host, port)
    httpd = HTTPServer(server_address, TokenCacheHTTPHandler)
    url = f"http://localhost:{port}"

    print("=" * 72)
    print("  \u26a1 LEKE LOCAL TOKEN CACHE — Interactive Web Demo Server")
    print("=" * 72)
    print(f"\n  \U0001f310 Server running at:     {url}")
    print(f"  \U0001f4dc Query REST API:        {url}/api/query")
    print(f"  \U0001f4ca Telemetry Stats:       {url}/api/stats")
    print(f"  \U0001f5c3\ufe0f SQLite Entries:        {url}/api/entries")
    print("\n  Press Ctrl+C to terminate the server.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\U0001f6d1 Shutting down server gracefully...")
        httpd.server_close()


if __name__ == "__main__":
    port = 8001
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port=port)
