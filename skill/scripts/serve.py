#!/usr/bin/env python3
"""经历库 thin local server: a dumb pipe between the browser page and the vault folder.
All product logic lives in the front end and in the harness AI (see SKILL.md).

    python3 serve.py [--vault ~/经历库] [--port 8765]
    python3 serve.py --vault ~/经历库 --ensure     # AI uses this: prints "RUNNING <url>" or starts it
                                                  # detached in the background and prints "STARTED <url>"

  GET    /                 app/index.html (with the write token injected)
  GET    /vault/<path>     a vault file; a folder returns a JSON listing [{name,dir,size,mtime}]
  PUT    /vault/<path>.json   write JSON (experiences/, applications/, config.json only)
  DELETE /vault/<path>.json   move to .trash/
Only 127.0.0.1; Host is checked; writes need the X-Token header. Standard library only.
"""
import argparse, json, mimetypes, os, secrets, socket, subprocess, sys, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ap = argparse.ArgumentParser()
ap.add_argument("--vault", default=os.environ.get("JINGLIKU_VAULT", "~/经历库"))
ap.add_argument("--port", type=int, default=8765)
ap.add_argument("--app", default=str(Path(__file__).resolve().parent.parent / "app"))
ap.add_argument("--ensure", action="store_true", help="print the URL if running, else start detached")
A = ap.parse_args()
VAULT, APP = Path(A.vault).expanduser().resolve(), Path(A.app).resolve()
WRITABLE = ("experiences/", "applications/", "config.json")


def running_url():
    """The URL in .runtime.json, but only if a server there actually answers."""
    try:
        u = json.loads((VAULT / ".runtime.json").read_text())["url"]
        with urllib.request.urlopen(u + "vault/config.json", timeout=2) as r:
            return u if r.status == 200 else None
    except Exception:
        return None


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


def free_port(p):
    """Same port as last time if possible (SO_REUSEADDR lets us reclaim it right after a restart)."""
    while True:
        with socket.socket() as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", p)); return p
            except OSError:
                p += 1


TOKEN = stable_token() if VAULT.is_dir() else secrets.token_urlsafe(16)
PORT = free_port(A.port)
HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}


class H(BaseHTTPRequestHandler):
    def send(self, code, body=b"", ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

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
        path = urlsplit(self.path).path
        if path.startswith("/vault/"):
            p, _ = self.target()
            if p and p.is_dir():
                items = [{"name": c.name, "dir": c.is_dir(), "size": c.stat().st_size,
                          "mtime": c.stat().st_mtime} for c in sorted(p.iterdir())
                         if not c.name.startswith(".") and c.exists()]
                return self.send(200, json.dumps(items, ensure_ascii=False).encode())
            if p and p.is_file():
                return self.send(200, p.read_bytes(), mimetypes.guess_type(p.name)[0] or "application/octet-stream")
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
    (VAULT / ".runtime.json").write_text(json.dumps({"url": url, "pid": os.getpid()}))
    print(f"经历库 running at {url}  (vault: {VAULT})", flush=True)
    try:
        ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
    except KeyboardInterrupt:
        pass
