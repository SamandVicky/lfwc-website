import http.server
import os
import urllib.parse

SITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
PORT = 8080

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"{self.path} -> {args[0] if args else ''}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        # Try exact file first, then a directory's index.html — no fallback
        # to the homepage, so unmatched paths correctly 404 (matches the
        # production Vercel routing, which has no catch-all fallback either).
        candidates = [
            os.path.join(SITE_DIR, path.lstrip("/")),
            os.path.join(SITE_DIR, path.lstrip("/"), "index.html"),
        ]

        for candidate in candidates:
            if os.path.isfile(candidate):
                self._serve_file(candidate)
                return

        # 404
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not found")

    def _serve_file(self, fpath):
        ext = os.path.splitext(fpath)[1].lower()
        mime = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css",
            ".js": "application/javascript",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".ico": "image/x-icon",
            ".svg": "image/svg+xml",
            ".woff": "font/woff",
            ".woff2": "font/woff2",
        }.get(ext, "application/octet-stream")

        with open(fpath, "rb") as f:
            data = f.read()

        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", len(data))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

if __name__ == "__main__":
    os.chdir(SITE_DIR)
    httpd = http.server.HTTPServer(("", PORT), Handler)
    print(f"Serving {SITE_DIR} at http://localhost:{PORT}")
    httpd.serve_forever()
