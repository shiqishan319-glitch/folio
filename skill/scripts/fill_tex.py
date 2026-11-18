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


def format_point(line):
    line = line.strip(" -•·")
    for sep in ("：", ": "):
        if sep in line:
            prefix, rest = line.split(sep, 1)
            if 1 <= len(prefix.strip()) <= 16 and rest.strip():
                return f"\\point{{{tex(prefix.strip() + sep.strip())}}}{{{tex(rest.strip())}}}"
    return f"\\point{{}}{{{tex(line)}}}"


def resume(vault, wtype, prefer, ids):
    cfg = load(vault / "config.json") if (vault / "config.json").exists() else {}
    p = cfg.get("profile") or {}
    cards = [load(f) for f in sorted((vault / "experiences").glob("*.json"))]
    if ids:
        cards = [c for i in ids for c in cards if c.get("id") == i]
    else:
        cards.sort(key=lambda c: (c.get("year") or 0, str(c.get("time", ""))), reverse=True)

    sec_blocks = []

    # Optional education section at the top
    edu_list = p.get("education") or []
    if edu_list:
        edu_lines = []
        for ed in edu_list:
            left = " · ".join(x for x in [ed.get("school"), ed.get("major"), ed.get("degree")] if x)
            edu_lines.append(f"\\entry{{{tex(left)}}}{{{tex(ed.get('time'))}}}")
            for det in ed.get("details") or []:
                if str(det).strip():
                    edu_lines.append(format_point(str(det)))
        sec_blocks.append(("教育背景", "\n".join(edu_lines)))

    types = cfg.get("resume_types") or [t for t in cfg.get("types", ["实习", "项目", "志愿者", "获奖", "技能"]) if t != "思考"]
    for t in types:
        entries = []
        for c in cards:
            text = pick(c, wtype, prefer) or c.get("result") or c.get("fact") if c.get("type") == t else None
            if text:
                pts = "\n".join(format_point(l) for l in str(text).splitlines() if l.strip(" -•·"))
                if t == "技能" and not c.get("org") and not c.get("role") and not c.get("time"):
                    entries.append(pts)
                else:
                    heading = " · ".join(x for x in [c.get("org") or c.get("title"), c.get("role")] if x)
                    entries.append(f"\\entry{{{tex(heading)}}}{{{tex(c.get('time'))}}}\n{pts}")
        if entries:
            sec_blocks.append((t, "\n".join(entries)))

    # Contact line: 城市 · 电话 · 邮箱 · 链接
    contact_parts = []
    if p.get("location"):
        contact_parts.append(tex(p["location"]))
    if p.get("phone"):
        contact_parts.append(f"电话：{tex(p['phone'])}")
    if p.get("email"):
        contact_parts.append(f"邮箱：{tex(p['email'])}")
    for lk in p.get("links") or []:
        if lk:
            contact_parts.append(tex(lk))
    contact = " \\quad|\\quad ".join(contact_parts)

    # Optional skills / languages section at the bottom
    skills_list = [str(s).strip() for s in (p.get("skills") or []) if str(s).strip()]
    if skills_list:
        sec_blocks.append(("技能与语言", "\n".join(format_point(s) for s in skills_list)))

    photo_path = ""
    if p.get("photo"):
        cand = Path(p["photo"]).expanduser()
        if not cand.is_absolute():
            cand = vault / cand
        if cand.is_file():
            photo_path = str(cand.resolve())

    if not sec_blocks:
        sec_blocks = [("经历", "\\point{}{还没有可用的简历条目}")]

    first_title, first_body = sec_blocks[0]
    body_parts = [
        f"\\resumeheader{{{tex(p.get('name') or '姓名')}}}{{{tex(p.get('headline'))}}}{{{contact}}}{{{photo_path}}}{{{tex(first_title)}}}",
        first_body,
    ]
    for sec_title, sec_body in sec_blocks[1:]:
        body_parts.append(f"\\resumesection{{{tex(sec_title)}}}")
        body_parts.append(sec_body)

    return fill("resume.tex", {"CONTENT": "\n\n".join(body_parts)})


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
