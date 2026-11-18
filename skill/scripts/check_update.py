#!/usr/bin/env python3
"""Check GitHub for a newer version of this skill. Never updates on its own.

    python3 check_update.py            # at most once per 20 hours; prints one status line first
    python3 check_update.py --force    # check now
    python3 check_update.py --apply    # after the user agreed: update (git installs only)

First line of output is one of:
  UP_TO_DATE <version>          nothing to do
  UPDATE_AVAILABLE <what>       followed by "- <change>" lines; ask the user before --apply
  SKIPPED <reason>              checked recently / offline / no access; carry on silently
  UPDATED                       done; then run serve.py --restart so the new code is used
  DIRTY                         local edits in the skill folder; don't overwrite, tell the user
  CANT_APPLY <how>              copy install: reinstall following adapters/<tool>/README.md
Two install kinds: a git checkout (or a symlink into one) is compared with git; a copied folder
compares its VERSION file with the one on GitHub. Standard library + git only.
"""
import os, subprocess, sys, time, urllib.request
from pathlib import Path

REPO = os.environ.get("JINGLIKU_REPO", "shiqishan319-glitch/folio")
BRANCH = os.environ.get("JINGLIKU_BRANCH", "main")
SKILL = Path(__file__).resolve().parent.parent  # resolve() follows a symlinked install
STAMP = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "jingliku" / "last-update-check"
FORCE, APPLY = "--force" in sys.argv, "--apply" in sys.argv


def git(*args, timeout=5):
    env = os.environ.copy()
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    env.setdefault("GCM_INTERACTIVE", "never")
    env.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes -o ConnectTimeout=3")
    r = subprocess.run(["git", "-C", str(SKILL), *args], capture_output=True, text=True, timeout=timeout, env=env)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def write_stamp(offset_seconds=0):
    try:
        STAMP.parent.mkdir(parents=True, exist_ok=True)
        STAMP.write_text(str(int(time.time() - offset_seconds)))
    except OSError:
        pass


def done(line, *more):
    print(line, *more, sep="\n")
    if not line.startswith("SKIPPED"):
        write_stamp()
    sys.exit(0)


def skip_network(reason):
    print(f"SKIPPED {reason}")
    # Cool down for 2 hours on network/timeout failure so offline sessions don't stall repeatedly
    write_stamp(offset_seconds=18 * 3600)
    sys.exit(0)


def ver(s):
    return tuple(int(x) for x in s.strip().split(".") if x.isdigit())


if not (FORCE or APPLY) and STAMP.exists():
    try:
        if time.time() - float(STAMP.read_text() or 0) < 20 * 3600:
            print("SKIPPED checked recently"); sys.exit(0)
    except (OSError, ValueError):
        pass

try:
    is_git = git("rev-parse", "--is-inside-work-tree")[1] == "true"
except (OSError, subprocess.TimeoutExpired):
    is_git = False

if is_git:
    up = git("rev-parse", "--abbrev-ref", "@{u}")[1] or f"origin/{BRANCH}"
    try:
        rc, _, err = git("-c", "http.lowSpeedLimit=1000", "-c", "http.lowSpeedTime=3", "fetch", "--quiet", timeout=5)
    except subprocess.TimeoutExpired:
        rc, err = 1, "timeout"
    if rc:
        skip_network("cannot reach GitHub: " + (err.splitlines() or ["?"])[0])
    n = int(git("rev-list", "--count", f"HEAD..{up}")[1] or 0)
    if n == 0:
        done(f"UP_TO_DATE {git('rev-parse', '--short', 'HEAD')[1]}")
    if not APPLY:
        log = git("log", "--format=- %s", f"HEAD..{up}")[1].splitlines()
        done(f"UPDATE_AVAILABLE {n} new commit(s)", *log[:8])
    # only edits to tracked files block the update; stray files (.DS_Store, caches) don't,
    # and git pull itself refuses if an untracked file would be overwritten
    dirty = git("status", "--porcelain", "--untracked-files=no", "--", ".")[1]
    if dirty:
        print("DIRTY"); print(dirty); sys.exit(0)
    try:
        rc, out, err = git("pull", "--ff-only", "--quiet", timeout=30)
    except subprocess.TimeoutExpired:
        rc, err = 1, "timeout"
    done("UPDATED" if rc == 0 else f"SKIPPED pull failed: {err.splitlines()[0] if err else '?'}")

# copied install: compare VERSION files
local = (SKILL / "VERSION").read_text().strip() if (SKILL / "VERSION").exists() else "0"
url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/skill/VERSION"
try:
    with urllib.request.urlopen(url, timeout=4) as r:
        remote = r.read().decode().strip()
except Exception as e:
    skip_network(f"cannot read the version on GitHub (offline, or the repo is private): {type(e).__name__}")
if ver(remote) <= ver(local):
    done(f"UP_TO_DATE {local}")
if APPLY:
    done(f"CANT_APPLY copied install ({local} -> {remote}): reinstall following adapters/<your tool>/README.md")
done(f"UPDATE_AVAILABLE {local} -> {remote}", f"- see https://github.com/{REPO}/commits/{BRANCH}")
