import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ASSET_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
               ".svg": "image/svg+xml", ".webp": "image/webp", ".ico": "image/x-icon"}

def make_handler(board):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                with open(PAGE_PATH, "rb") as f:
                    self._send(200, f.read(), "text/html")
            elif self.path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
            elif self.path.startswith("/assets/"):
                name = os.path.basename(self.path[len("/assets/"):].split("?")[0])
                ext = os.path.splitext(name)[1].lower()
                path = os.path.join(ASSET_DIR, name)
                if ext in ASSET_TYPES and os.path.isfile(path):
                    with open(path, "rb") as f:
                        self._send(200, f.read(), ASSET_TYPES[ext])
                else:
                    self._send(404, "not found", "text/plain")
            elif self.path == "/api/board":
                self._send(200, json.dumps(board.snapshot()))
            else:
                self._send(404, "not found", "text/plain")

        def do_POST(self):
            try:
                n = int(self.headers.get("Content-Length", 0))
                req = json.loads(self.rfile.read(n) or b"{}")
                if self.path == "/api/update":
                    board.update(req["id"], req["field"], str(req["value"]))
                    self._send(200, "{}")
                elif self.path == "/api/deliver":
                    self._send(200, json.dumps({"failed": board.deliver(req["id"])}))
                else:
                    self._send(404, "not found", "text/plain")
            except Exception as e:
                self._send(400, str(e), "text/plain")

    return Handler


def serve(board, host, port):
    ThreadingHTTPServer((host, port), make_handler(board)).serve_forever()
