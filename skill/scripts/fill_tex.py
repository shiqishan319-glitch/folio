#!/usr/bin/env python3
"""Fill a LaTeX template from vault JSON, escaping special characters safely.
(Escaping by hand is the step small models get wrong, so it lives here.)

    python3 fill_tex.py letter <VAULT> <application-id> <out.tex>
    python3 fill_tex.py resume <VAULT> <out.tex> [--writing 简历条目] [--prefer 英文] [--ids a,b,c]

Then compile:  cd <dir of out.tex> && xelatex -interaction=nonstopmode -halt-on-error <out.tex>
"""
import argparse, json, re
from pathlib import Path

TPL = Path(__file__).resolve().parent.parent / "templates" / "latex"
ESC = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
       "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def tex(s):
    return re.sub(r"[\\&%$#_{}~^]", lambda m: ESC[m.group()], str(s or ""))


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def fill(name, values):
    out = (TPL / name).read_text(encoding="utf-8")
    for k, v in values.items():
        out = out.replace(f"%%{k}%%", v)
    return out


def letter(vault, did):
    d = load(vault / "applications" / f"{did}.json")
    name = (load(vault / "config.json").get("profile") or {}).get("name") if (vault / "config.json").exists() else ""
    meta = " · ".join(tex(d.get(k)) for k in ("kind", "target", "date") if d.get(k))
    body = "\n\n".join(tex(p.get("text")) for p in d.get("paras", []) if str(p.get("text") or "").strip())
    return fill("letter.tex", {"TITLE": tex(d.get("title")), "META": meta, "BODY": body or "~", "SIGNATURE": tex(name) or "~"})


def pick(card, wtype, prefer):
    for w in card.get("writings", []):
        if w.get("type") == wtype and w.get("versions"):
            for v in w["versions"]:
                if prefer and prefer in v.get("name", ""):
                    return v.get("text")
            return w["versions"][0].get("text")


def resume(vault, wtype, prefer, ids):
    cfg = load(vault / "config.json") if (vault / "config.json").exists() else {}
    cards = [load(f) for f in sorted((vault / "experiences").glob("*.json"))]
    if ids:
        cards = [c for i in ids for c in cards if c.get("id") == i]
    else:
        cards.sort(key=lambda c: (c.get("year") or 0, str(c.get("time", ""))), reverse=True)
    types = cfg.get("resume_types") or [t for t in cfg.get("types", ["实习", "项目", "志愿者", "获奖"]) if t != "思考"]
    sections = []
    for t in types:
        entries = []
        for c in cards:
            text = pick(c, wtype, prefer) or c.get("result") or c.get("fact") if c.get("type") == t else None
            if text:
                items = "\n".join(f"\\item {tex(l.strip(' -•·'))}" for l in str(text).splitlines() if l.strip(" -•·"))
                entries.append(f"\\entry{{{tex(c.get('org') or c.get('title'))}}}{{{tex(c.get('role'))}}}{{{tex(c.get('time'))}}}{{{items}}}")
        if entries:
            sections.append(f"\\section*{{{tex(t)}}}\n" + "\n".join(entries))
    p = cfg.get("profile") or {}
    contact = " \\quad ".join(tex(x) for x in [p.get("email"), p.get("phone"), *(p.get("links") or [])] if x)
    head = f"{{\\color{{muted}}{tex(p['headline'])}}}\\par\\vspace{{0.2em}}\n" if p.get("headline") else ""
    return fill("resume.tex", {"NAME": tex(p.get("name") or "姓名"), "HEADLINE": head, "CONTACT": contact or "~",
                               "SECTIONS": "\n\n".join(sections) or "（还没有可用的简历条目）"})


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="kind", required=True)
    a1 = sub.add_parser("letter"); a1.add_argument("vault"); a1.add_argument("id"); a1.add_argument("out")
    a2 = sub.add_parser("resume"); a2.add_argument("vault"); a2.add_argument("out")
    a2.add_argument("--writing", default="简历条目"); a2.add_argument("--prefer"); a2.add_argument("--ids")
    a = ap.parse_args()
    v = Path(a.vault).expanduser()
    src = letter(v, a.id) if a.kind == "letter" else resume(v, a.writing, a.prefer, a.ids.split(",") if a.ids else None)
    Path(a.out).write_text(src, encoding="utf-8")
    print(Path(a.out).resolve())
