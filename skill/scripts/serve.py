#!/usr/bin/env python3
"""经历库 thin local server: a dumb pipe between the browser page and the vault folder.
All product logic lives in the front end and in the harness AI (see SKILL.md).

    python3 serve.py [--vault ~/经历库] [--port 8765]
    python3 serve.py --vault ~/经历库 --ensure     # AI uses this: prints "RUNNING <url>" or starts it
                                                  # detached in the background and prints "STARTED <url>"
    python3 serve.py --vault ~/经历库 --restart    # after an update: stop the old server, start the new code

  Port: last used port (from .runtime.json), else 8765; if another app holds it, the next free one.

  GET    /                 app/index.html (with the write token injected)
  GET    /vault/<path>     a vault file; a folder returns a JSON listing [{name,dir,size,mtime}]
  PUT    /vault/<path>.json   write JSON (experiences/, applications/, config.json only)
  DELETE /vault/<path>.json   move to .trash/
Only 127.0.0.1; Host is checked; writes need the X-Token header. Standard library only.
"""
import argparse, json, mimetypes, os, secrets, signal, socket, subprocess, sys, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

ap = argparse.ArgumentParser()
ap.add_argument("--vault", default=os.environ.get("JINGLIKU_VAULT", "~/经历库"))
ap.add_argument("--port", type=int, default=None, help="preferred port (default: last used, else 8765)")
ap.add_argument("--app", default=str(Path(__file__).resolve().parent.parent / "app"))
ap.add_argument("--ensure", action="store_true", help="print the URL if running, else start detached")
ap.add_argument("--restart", action="store_true", help="stop the running server (e.g. after an update), then --ensure")
A = ap.parse_args()
VAULT, APP = Path(A.vault).expanduser().resolve(), Path(A.app).resolve()
WRITABLE = ("experiences/", "applications/", "config.json")
SIGNATURE = "X-Jingliku"  # every response carries it, so we never mistake another app for ours


def runtime():
    try:
        return json.loads((VAULT / ".runtime.json").read_text())
    except Exception:
        return {}


def running_url():
    """The URL in .runtime.json, but only if OUR server answers there."""
    try:
        u = runtime()["url"]
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(u + "vault/config.json", timeout=2) as r:
            return u if r.status == 200 and r.headers.get(SIGNATURE) else None
    except Exception:
        return None


# keep the URL stable: reuse last port unless the user asked for one
A.port = A.port or runtime().get("port") or 8765

def is_our_process(pid):
    """True if pid is a running serve.py (also catches older versions without the signature header)."""
    try:
        if os.name == "nt":
            return bool(running_url())
        out = subprocess.run(["ps", "-p", str(int(pid)), "-o", "command="], capture_output=True, text=True).stdout
        return "serve.py" in out
    except (OSError, ValueError):
        return False


if A.restart:
    pid = runtime().get("pid")
    if pid and is_our_process(pid):
        try:
            os.kill(int(pid), signal.SIGTERM)
        except OSError:
            pass
        for _ in range(25):  # wait until it is really gone
            time.sleep(0.2)
            if not is_our_process(pid):
                break
    A.ensure = True

if A.ensure:
    if not VAULT.is_dir():
        sys.exit(f"NO_VAULT {VAULT} (create it first: recipes/01-启动.md)")
    u = running_url()
    if u:
        print("RUNNING", u); sys.exit(0)
    # start a detached copy that survives the end of this command / tool call
    log = open(VAULT / ".serve.log", "ab")
    detach = {"start_new_session": True} if os.name != "nt" else {"creationflags": 0x00000008 | 0x00000200}
    subprocess.Popen([sys.executable, os.path.abspath(__file__), "--vault", str(VAULT), "--port", str(A.port),
                      "--app", str(APP)], stdout=log, stderr=log, stdin=subprocess.DEVNULL, close_fds=True, **detach)
    for _ in range(50):
        time.sleep(0.2)
        u = running_url()
        if u:
            print("STARTED", u); sys.exit(0)
    sys.exit(f"FAILED to start; read {VAULT / '.serve.log'}")


def stable_token():
    """Keep the write token across restarts, so a page that is already open keeps working."""
    f = VAULT / ".token"
    try:
        t = f.read_text().strip()
        if len(t) >= 16: return t
    except OSError:
        pass
    t = secrets.token_urlsafe(16)
    try:
        f.write_text(t); f.chmod(0o600)
    except OSError:
        pass
    return t


def port_free(p):
    """Free = nobody answers on it AND we can bind it.
    The connect test catches other apps listening on any interface (0.0.0.0 / ::), which a
    SO_REUSEADDR bind on macOS would wrongly allow; SO_REUSEADDR itself is still needed to
    reclaim our own port right after a restart (TIME_WAIT). Windows uses exclusive binding."""
    with socket.socket() as c:
        c.settimeout(0.3)
        if c.connect_ex(("127.0.0.1", p)) == 0:
            return False
    with socket.socket() as s:
        s.setsockopt(socket.SOL_SOCKET, getattr(socket, "SO_EXCLUSIVEADDRUSE", socket.SO_REUSEADDR), 1)
        try:
            s.bind(("127.0.0.1", p)); return True
        except OSError:
            return False


def free_port(p):
    for q in range(p, p + 50):
        if port_free(q):
            return q
    sys.exit(f"NO_FREE_PORT in {p}-{p + 49}")


TOKEN = stable_token() if VAULT.is_dir() else secrets.token_urlsafe(16)
PORT = free_port(A.port)
HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}


class H(BaseHTTPRequestHandler):
    def send(self, code, body=b"", ctype="application/json; charset=utf-8"):
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header(SIGNATURE, "1")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass  # the browser closed or reloaded mid-response; nothing to report

    def send_file(self, path, ctype):
        """Stream a local file with HTTP Range support so large videos seek without loading into RAM."""
        total = path.stat().st_size
        start, end, code = 0, total - 1, 200
        rng = self.headers.get("Range")
        if rng and rng.startswith("bytes=") and total > 0:
            spec = rng[6:].split(",", 1)[0].strip()
            if "-" in spec:
                s_part, e_part = spec.split("-", 1)
                if s_part == "" and e_part:
                    length = int(e_part)
                    start = max(0, total - length)
                elif s_part:
                    start = int(s_part)
                    end = int(e_part) if e_part else total - 1
                if start > end or start >= total:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{total}")
                    self.send_header(SIGNATURE, "1")
                    return self.end_headers()
                end = min(end, total - 1)
                code = 206
        length = (end - start + 1) if total > 0 else 0
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(length))
            if code == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
            self.send_header("Cache-Control", "no-store")
            self.send_header(SIGNATURE, "1")
            self.end_headers()
            if length == 0:
                return
            with path.open("rb") as f:
                f.seek(start)
                rem = length
                while rem > 0:
                    chunk = f.read(min(65536, rem))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    rem -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def target(self):
        """Map /vault/<rel> to a path inside the vault, or None."""
        rel = unquote(urlsplit(self.path).path)[len("/vault/"):]
        if any(p in ("..", "") for p in rel.split("/")[:-1]) or ".." in rel.split("/"):
            return None, rel
        return VAULT / rel, rel

    def guard(self, write=False):
        if self.headers.get("Host") not in HOSTS:
            return self.send(403, b'{"error":"bad host"}')
        if write and (self.headers.get("X-Token") != TOKEN
                      or self.headers.get("Origin") not in (None, *(f"http://{h}" for h in HOSTS))):
            return self.send(403, b'{"error":"bad token"}')
        return True

    def do_GET(self):
        if not self.guard(): return
        parts = urlsplit(self.path)
        path = parts.path
        if path == "/resume-print":
            qs = parse_qs(parts.query)
            writing = (qs.get("writing") or ["简历条目"])[0]
            prefer = (qs.get("prefer") or [None])[0]
            ids = qs["ids"][0].split(",") if qs.get("ids") and qs["ids"][0] else None
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import fill_html
            html_out = fill_html.resume(VAULT, writing, prefer, ids)
            return self.send(200, html_out.encode("utf-8"), "text/html; charset=utf-8")
        if path.startswith("/vault/"):
            p, _ = self.target()
            if p and p.is_dir():
                items = [{"name": c.name, "dir": c.is_dir(), "size": c.stat().st_size,
                          "mtime": c.stat().st_mtime} for c in sorted(p.iterdir())
                         if not c.name.startswith(".") and c.exists()]
                return self.send(200, json.dumps(items, ensure_ascii=False).encode())
            if p and p.is_file():
                return self.send_file(p, mimetypes.guess_type(p.name)[0] or "application/octet-stream")
            return self.send(404, b'{"error":"not found"}')
        f = (APP / (path.lstrip("/") or "index.html")).resolve()
        if APP not in f.parents or not f.is_file():
            return self.send(404, b"not found", "text/plain")
        body = f.read_bytes()
        if f.suffix == ".html":
            body = body.replace(b"</head>", f'<meta name="jingliku-token" content="{TOKEN}"></head>'.encode(), 1)
        self.send(200, body, mimetypes.guess_type(f.name)[0] or "application/octet-stream")

    def do_PUT(self):
        if not self.guard(write=True): return
        p, rel = self.target()
        if p and rel in ("assets/portrait.png", "assets/portrait.jpg", "assets/portrait.jpeg", "assets/portrait.webp"):
            size = int(self.headers.get("Content-Length") or 0)
            if size <= 0 or size > 10 * 1024 * 1024:
                return self.send(400, b'{"error":"invalid size"}')
            raw = self.rfile.read(size)
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_name(f".{p.name}.tmp")
            tmp.write_bytes(raw)
            os.replace(tmp, p)
            return self.send(200, json.dumps({"ok": True, "path": rel}).encode())
        if not p or not rel.endswith(".json") or not rel.startswith(WRITABLE):
            return self.send(403, b'{"error":"not writable"}')
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
        except ValueError:
            return self.send(400, b'{"error":"body must be JSON"}')
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(f".{p.name}.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, p)
        self.send(200, b'{"ok":true}')

    def do_DELETE(self):
        if not self.guard(write=True): return
        p, rel = self.target()
        if not p or not rel.startswith(WRITABLE[:2]) or not p.is_file():
            return self.send(404, b'{"error":"not found"}')
        (VAULT / ".trash").mkdir(exist_ok=True)
        os.replace(p, VAULT / ".trash" / f"{time.strftime('%Y%m%d-%H%M%S')}-{p.name}")
        self.send(200, b'{"ok":true}')

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    if not VAULT.is_dir():
        sys.exit(f"no vault at {VAULT} — create it first (see SKILL.md)")
    url = f"http://127.0.0.1:{PORT}/"
    (VAULT / ".runtime.json").write_text(json.dumps({"url": url, "port": PORT, "pid": os.getpid()}))
    print(f"经历库 running at {url}  (vault: {VAULT})", flush=True)
    try:
        ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
    except KeyboardInterrupt:
        pass
