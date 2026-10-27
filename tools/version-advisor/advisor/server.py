"""Small dependency-free web server for the bilingual version advisor.

Only the Python standard library is used, so the live preview works anywhere
without installing packages.  All browser calls are same-origin relative URLs.
"""

from __future__ import annotations

import json
import mimetypes
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import VERSION, WEB_DIR
from .catalog import load_catalog, sync_catalog
from .devices import DeviceDetectionError, load_devices, profile_from_payload, search_devices
from .recommend import analyze

MAX_BODY = 64 * 1024
ALLOWED_FILES = {"index.html", "app.js", "styles.css", "favicon.svg"}

STATE = {
    "catalog": None,
    "devices": [],
    "online": True,
    "lastRefresh": None,
    "refreshError": None,
    "refreshing": False,
    "refreshHours": 6,
}
LOCK = threading.Lock()


def refresh_catalog() -> dict:
    """Run a catalog sync once and update the shared state."""
    with LOCK:
        if STATE["refreshing"]:
            return {"started": False, "reason": "a refresh is already running", "error": STATE["refreshError"]}
        STATE["refreshing"] = True
    try:
        result = sync_catalog(online=STATE["online"], write=True, timeout=20)
        with LOCK:
            STATE["catalog"] = result["catalog"]
            STATE["lastRefresh"] = result.get("checkedAt") or result["catalog"]["upstream"].get("checkedAt")
            STATE["refreshError"] = result["error"]
        return {
            "started": True,
            "changed": result["changed"],
            "notModified": result["notModified"],
            "added": [item["version"] for item in result["added"]],
            "error": result["error"],
            "checkedAt": STATE["lastRefresh"],
        }
    except Exception as error:  # keep the server alive on any unexpected failure
        with LOCK:
            STATE["refreshError"] = str(error)
        return {"started": True, "changed": False, "error": str(error)}
    finally:
        with LOCK:
            STATE["refreshing"] = False


def _refresh_loop(interval_seconds: float) -> None:
    stop = threading.Event()
    while not stop.wait(interval_seconds):
        try:
            refresh_catalog()
        except Exception as error:
            print(f"[advisor] background refresh failed: {error}", file=sys.stderr)


def state_payload() -> dict:
    with LOCK:
        catalog = STATE["catalog"]
        return {
            "server": {
                "version": VERSION,
                "online": STATE["online"],
                "refreshHours": STATE["refreshHours"],
                "lastRefresh": STATE["lastRefresh"],
                "refreshError": STATE["refreshError"],
                "refreshing": STATE["refreshing"],
            },
            "catalog": catalog,
            "devices": STATE["devices"],
        }


class Handler(BaseHTTPRequestHandler):
    server_version = f"YouTubeVersionAdvisor/{VERSION}"

    def log_message(self, fmt: str, *args) -> None:  # quieter logs
        sys.stderr.write("[advisor] " + (fmt % args) + "\n")

    def _headers(self, content_type: str = "application/json; charset=utf-8", length: int | None = None) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        if length is not None:
            self.send_header("Content-Length", str(length))

    def _send(self, status: int, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self._headers(content_type, len(payload))
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: int, data) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _static(self, name: str) -> None:
        path = Path(WEB_DIR) / name
        if name not in ALLOWED_FILES or not path.is_file():
            self._json(404, {"error": "not found"})
            return
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or name.endswith(".js"):
            content_type += "; charset=utf-8"
        self._send(200, path.read_bytes(), content_type)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urllib.parse.urlsplit(self.path).path
        if path in ("/", "/index.html"):
            self._static("index.html")
            return
        if path.startswith("/") and path[1:] in ALLOWED_FILES:
            self._static(path[1:])
            return
        if path in ("/api/state", "/api/catalog"):
            self._json(200, state_payload())
            return
        if path == "/api/health":
            self._json(200, {"ok": True, **state_payload()["server"]})
            return
        if path == "/api/devices":
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get("q", [""])[0]
            self._json(200, {"devices": search_devices(query, limit=20, devices=STATE["devices"])})
            return
        self._json(404, {"error": "not found", "path": path})

    def _body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        if length > MAX_BODY:
            raise ValueError("request body too large")
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8")) if raw else {}

    def do_POST(self) -> None:  # noqa: N802
        path = urllib.parse.urlsplit(self.path).path
        try:
            payload = self._body()
        except (ValueError, json.JSONDecodeError) as error:
            self._json(400, {"error": f"invalid JSON body: {error}"})
            return

        if path == "/api/refresh":
            self._json(200, {**refresh_catalog(), "state": state_payload()["server"], "catalog": STATE["catalog"]})
            return
        if path == "/api/detect":
            try:
                profile = profile_from_payload(payload, STATE["devices"])
            except DeviceDetectionError as error:
                self._json(422, {"error": str(error)})
                return
            self._json(200, {"device": profile, "matches": search_devices(payload.get("model") or "", 6, STATE["devices"])})
            return
        if path == "/api/devices":
            self._json(200, {"devices": search_devices(payload.get("query", ""), 12, STATE["devices"])})
            return
        if path == "/api/recommend":
            channel = payload.get("channel", "local")
            if channel not in ("local", "upstream"):
                self._json(400, {"error": "channel must be 'local' or 'upstream'"})
                return
            try:
                profile = profile_from_payload(payload, STATE["devices"])
                result = analyze(profile, STATE["catalog"], channel)
            except DeviceDetectionError as error:
                self._json(422, {"error": str(error)})
                return
            self._json(200, result)
            return
        self._json(404, {"error": "not found", "path": path})


def serve(
    host: str = "0.0.0.0",
    port: int = 8000,
    refresh_hours: float = 6,
    startup_refresh: bool = True,
    online: bool = True,
) -> int:
    STATE["catalog"] = load_catalog()
    STATE["devices"] = load_devices()
    STATE["online"] = online
    STATE["refreshHours"] = refresh_hours
    STATE["lastRefresh"] = STATE["catalog"]["upstream"].get("checkedAt")

    if startup_refresh and online:
        threading.Thread(target=refresh_catalog, name="startup-refresh", daemon=True).start()
    if refresh_hours and refresh_hours > 0:
        threading.Thread(
            target=_refresh_loop,
            args=(refresh_hours * 3600,),
            name="catalog-refresh",
            daemon=True,
        ).start()

    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.daemon_threads = True
    print(f"YouTube version advisor running on http://{host}:{port} (catalog auto-refresh: {refresh_hours}h)")
    try:
        httpd.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        httpd.server_close()
    return 0
