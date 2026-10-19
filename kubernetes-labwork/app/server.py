import os, time, json
from http.server import BaseHTTPRequestHandler, HTTPServer

START   = time.time()
VERSION = os.environ.get("APP_VERSION", "02230129-1.0.0")
PINNED  = os.environ.get("FEATURE_PINNED", "false").lower() == "true"
POD     = os.environ.get("HOSTNAME", "unknown")

NOTICES = [
    {"id": 1, "text": "Welcome to the Campus Notice Board", "category": "general"},
    {"id": 2, "text": "Exam timetable published",           "category": "exams", "pinned": True},
    {"id": 3, "text": "Library closed on Sunday",           "category": "facilities"},
]

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            if time.time() - START < 5:
                self.send_response(503); self.end_headers(); self.wfile.write(b"warming up"); return
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok"); return
        if self.path == "/version":
            self._json({"version": VERSION, "pod": POD}); return
        if self.path == "/notices":
            data = list(NOTICES)
            if PINNED:
                data.sort(key=lambda x: (not x.get("pinned", False), x["id"]))
            self._json({"notices": data, "pinnedFirst": PINNED}); return
        self.send_response(404); self.end_headers()

    def _json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):     # keep stdout clean for the probe noise
        pass

HTTPServer(("", 8080), H).serve_forever()