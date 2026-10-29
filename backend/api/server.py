"""
REST and Static File Server for Leke Local Token Cache.
Zero external pip dependencies.
"""

from __future__ import annotations

import json
import mimetypes
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from backend.api.controllers.cache_controller import CacheController
from backend.api.services.cache_service import CacheService
from backend.api.repositories.cache_repository import CacheRepository


class CacheRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler for Token Cache endpoints and frontend UI."""

    controller = CacheController(CacheService(CacheRepository()))
    frontend_dir: Path = Path(__file__).parent.parent.parent / "frontend"

    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._set_cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/stats":
            self._send_json(200, self.controller.handle_stats())
            return
        elif path == "/api/health":
            self._send_json(200, {"status": "healthy", "service": "leke-local-token-cache"})
            return

        # Serve static assets
        rel_path = path.lstrip("/")
        if not rel_path or rel_path == "index.html":
            target = self.frontend_dir / "index.html"
        else:
            target = self.frontend_dir / rel_path

        if target.is_file():
            mime_type, _ = mimetypes.guess_type(str(target))
            mime_type = mime_type or "application/octet-stream"
            content = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self._set_cors()
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length > 0 else b"{}"

        try:
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except Exception as e:
            self._send_json(400, {"status": "error", "message": f"Invalid JSON: {e}"})
            return

        if path == "/api/query":
            res = self.controller.handle_query(payload)
            self._send_json(200, res)
        elif path == "/api/store":
            res = self.controller.handle_store(payload)
            self._send_json(200, res)
        elif path == "/api/clear":
            res = self.controller.handle_clear()
            self._send_json(200, res)
        else:
            self._send_json(404, {"status": "error", "message": "Endpoint not found"})


def start_server(port: int = 8098):
    server = HTTPServer(("0.0.0.0", port), CacheRequestHandler)
    print(f"\n🚀 Leke Local Token Cache Console running at http://localhost:{port}")
    print(f"   Frontend assets served from: {CacheRequestHandler.frontend_dir}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping cache server...")
        server.server_close()
