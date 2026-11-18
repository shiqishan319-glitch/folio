#!/usr/bin/env python3
"""Manage multimodal portfolio works with tiered storage & semantic index.

Tiered storage policy (default --mode auto):
  - Tier 0: URLs (kind: link) -> 0 bytes in vault.
  - Tier 1: <= 5 MB images / PDFs / documents -> copy into assets/<card_id>/ (portable, never breaks).
  - Tier 2: > 5 MB files, videos, archives, folders -> symlink in assets/<card_id>/ (0 vault bloat)
            + lightweight `summary` text & `sha256` fingerprint in card JSON.

Subcommands:
  python3 works.py attach <VAULT> <card_id> <file_path> [--mode auto|copy|link] [--label ...] [--summary ...]
  python3 works.py relink <VAULT> [--card <id>] [--dry-run]
  python3 works.py audit  <VAULT>
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

COPY_LIMIT_BYTES = 5 * 1024 * 1024  # 5 MB

EXT_KIND = {
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".webp": "image", ".gif": "image", ".svg": "image",
    ".mp4": "video", ".mov": "video", ".webm": "video", ".mkv": "video", ".avi": "video",
    ".pdf": "pdf",
    ".ppt": "slides", ".pptx": "slides", ".key": "slides",
    ".doc": "document", ".docx": "document", ".md": "document", ".txt": "document", ".pages": "document",
    ".zip": "archive", ".tar": "archive", ".gz": "archive", ".7z": "archive", ".rar": "archive",
}


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def infer_kind(path: Path) -> str:
    if path.is_dir():
        return "folder"
    return EXT_KIND.get(path.suffix.lower(), "file")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict):
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def cmd_attach(args):
    vault = Path(args.vault).expanduser().resolve()
    card_path = vault / "experiences" / f"{args.card_id}.json"
    if not card_path.is_file():
        sys.exit(f"Card not found: {card_path}")

    src = Path(args.file_path).expanduser().resolve()
    if not src.exists():
        sys.exit(f"Source file not found: {src}")

    kind = args.kind or infer_kind(src)
    size = src.stat().st_size if src.is_file() else 0
    mtime = int(src.stat().st_mtime)

    mode = args.mode
    if mode == "auto":
        if src.is_dir() or kind in ("video", "archive", "folder") or size > COPY_LIMIT_BYTES:
            mode = "link"
        else:
            mode = "copy"

    dest_dir = vault / "assets" / args.card_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if dest.exists() or dest.is_symlink():
        dest.unlink()

    if mode == "copy":
        if src.is_dir():
            sys.exit("Cannot use --mode copy on a directory; use --mode link.")
        shutil.copy2(src, dest)
    else:
        os.symlink(src, dest)

    rel_asset = f"{args.card_id}/{src.name}"
    sha = file_sha256(src) if src.is_file() and size <= 200 * 1024 * 1024 else ""

    item = {
        "label": args.label or src.name,
        "kind": kind,
        "asset": rel_asset,
        "mode": mode,
        "original": str(src),
        "size": size,
        "mtime": mtime,
    }
    if sha:
        item["sha256"] = sha
    if args.summary:
        item["summary"] = args.summary.strip()

    card = load_json(card_path)
    works = card.get("works") or []
    idx = next((i for i, w in enumerate(works) if isinstance(w, dict) and w.get("asset") == rel_asset), None)
    if idx is not None:
        if not item.get("summary") and works[idx].get("summary"):
            item["summary"] = works[idx]["summary"]
        works[idx] = item
    else:
        works.append(item)
    card["works"] = works
    card["updated"] = now_iso()
    save_json(card_path, card)

    mb = size / (1024 * 1024)
    print(f"ATTACHED [{mode}] {rel_asset} ({mb:.2f} MB, kind={kind})")
    if mode == "link" and not item.get("summary"):
        print("TIP: Tier-2 linked file has no `summary` yet; add 1-2 sentences so search & AI can find it without opening.")


def find_candidates_spotlight(filename: str):
    hits = []
    if shutil.which("mdfind"):
        try:
            out = subprocess.check_output(
                ["mdfind", f'kMDItemFSName == "{filename}"'],
                text=True, timeout=8, stderr=subprocess.DEVNULL
            )
            for line in out.splitlines():
                p = Path(line.strip())
                if p.exists():
                    hits.append(p)
        except Exception:
            pass
    if not hits:
        for base in ("Desktop", "Downloads", "Documents", "Movies", "Pictures"):
            root = Path.home() / base
            if root.is_dir():
                for p in root.rglob(filename):
                    if p.exists():
                        hits.append(p)
    return hits


def cmd_relink(args):
    vault = Path(args.vault).expanduser().resolve()
    exp_dir = vault / "experiences"
    cards = [exp_dir / f"{args.card}.json"] if args.card else sorted(exp_dir.glob("*.json"))

    checked = broken = repaired = 0
    for cp in cards:
        if not cp.is_file():
            continue
        card = load_json(cp)
        changed = False
        for w in card.get("works") or []:
            if not isinstance(w, dict) or not w.get("asset"):
                continue
            if w.get("mode", "link") != "link":
                continue
            checked += 1
            asset_path = vault / "assets" / w["asset"]
            if asset_path.exists():
                continue
            broken += 1
            fname = Path(w.get("original") or w["asset"]).name
            candidates = [p for p in find_candidates_spotlight(fname) if (vault / "assets") not in p.parents]
            match = None
            want_sha = w.get("sha256")
            want_size = w.get("size")
            for cand in candidates:
                if not cand.is_file():
                    continue
                if want_sha:
                    if file_sha256(cand) == want_sha:
                        match = cand
                        break
                elif want_size is not None and cand.stat().st_size == want_size:
                    match = cand
                    break
            if not match and len(candidates) == 1:
                match = candidates[0]

            if match:
                print(f"MATCH {cp.stem}: {w['asset']} -> {match}")
                if not args.dry_run:
                    asset_path.parent.mkdir(parents=True, exist_ok=True)
                    if asset_path.is_symlink() or asset_path.exists():
                        asset_path.unlink()
                    os.symlink(match, asset_path)
                    w["original"] = str(match)
                    w["mtime"] = int(match.stat().st_mtime)
                    w["size"] = match.stat().st_size
                    changed = True
                repaired += 1
            else:
                print(f"MISSING {cp.stem}: {w['asset']} (original: {w.get('original', '?')})")
        if changed and not args.dry_run:
            card["updated"] = now_iso()
            save_json(cp, card)

    print(f"Checked {checked} linked works: {broken} broken, {repaired} {'would repair' if args.dry_run else 'repaired'}.")


def cmd_audit(args):
    vault = Path(args.vault).expanduser().resolve()
    exp_dir = vault / "experiences"
    stats = {"total": 0, "copy": 0, "copy_bytes": 0, "link": 0, "link_bytes": 0, "url": 0, "broken": 0, "no_summary": []}
    for cp in sorted(exp_dir.glob("*.json")):
        card = load_json(cp)
        for w in card.get("works") or []:
            stats["total"] += 1
            if not isinstance(w, dict):
                continue
            if w.get("kind") == "link" and w.get("url"):
                stats["url"] += 1
                continue
            asset = w.get("asset")
            if not asset:
                continue
            ap = vault / "assets" / asset
            mode = w.get("mode", "link")
            sz = w.get("size") or (ap.stat().st_size if ap.exists() else 0)
            if mode == "copy":
                stats["copy"] += 1
                stats["copy_bytes"] += sz
            else:
                stats["link"] += 1
                stats["link_bytes"] += sz
                if not ap.exists():
                    stats["broken"] += 1
            if (mode == "link" or sz > COPY_LIMIT_BYTES) and not w.get("summary"):
                stats["no_summary"].append(f"{cp.stem}:{asset}")

    print(f"Works total: {stats['total']} | url={stats['url']} | copy={stats['copy']} ({stats['copy_bytes']/1048576:.2f} MB in vault) | link={stats['link']} ({stats['link_bytes']/1048576:.2f} MB external) | broken={stats['broken']}")
    if stats["no_summary"]:
        print("Missing summary on heavy/linked works:", ", ".join(stats["no_summary"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a1 = sub.add_parser("attach", help="Attach a local file with tiered copy/link policy")
    a1.add_argument("vault")
    a1.add_argument("card_id")
    a1.add_argument("file_path")
    a1.add_argument("--mode", choices=["auto", "copy", "link"], default="auto")
    a1.add_argument("--label")
    a1.add_argument("--summary")
    a1.add_argument("--kind")
    a1.set_defaults(func=cmd_attach)

    a2 = sub.add_parser("relink", help="Find and repair broken work symlinks")
    a2.add_argument("vault")
    a2.add_argument("--card")
    a2.add_argument("--dry-run", action="store_true")
    a2.set_defaults(func=cmd_relink)

    a3 = sub.add_parser("audit", help="Audit vault works storage & semantic summaries")
    a3.add_argument("vault")
    a3.set_defaults(func=cmd_audit)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
