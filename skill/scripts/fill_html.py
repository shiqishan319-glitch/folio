#!/usr/bin/env python3
"""Fill a zero-dependency print-ready HTML resume template from vault JSON.

    python3 fill_html.py resume <VAULT> <out.html> [--writing 简历条目] [--prefer 英文] [--ids a,b,c]

Open the generated HTML in any browser and press Cmd/Ctrl + P to save as PDF.
"""
import argparse, base64, html, json, mimetypes
from pathlib import Path

TPL = Path(__file__).resolve().parent.parent / "templates" / "html"


def esc(s):
    return html.escape(str(s or ""), quote=True)


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


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
                return f"<li><strong>{esc(prefix.strip() + sep.strip())}</strong>{esc(rest.strip())}</li>"
    return f"<li>{esc(line)}</li>"


def render_points(lines):
    items = [format_point(l) for l in lines if str(l).strip(" -•·")]
    return f'<ul class="points">{"".join(items)}</ul>' if items else ""


def photo_data_uri(vault, raw_photo):
    if not raw_photo:
        return ""
    cand = Path(raw_photo).expanduser()
    if not cand.is_absolute():
        cand = vault / cand
    if not cand.is_file():
        return ""
    mime, _ = mimetypes.guess_type(str(cand))
    if not mime or not mime.startswith("image/"):
        mime = "image/png"
    b64 = base64.b64encode(cand.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def resume(vault, wtype, prefer, ids):
    cfg = load(vault / "config.json") if (vault / "config.json").exists() else {}
    p = cfg.get("profile") or {}
    cards = [load(f) for f in sorted((vault / "experiences").glob("*.json"))]
    if ids:
        cards = [c for i in ids for c in cards if c.get("id") == i]
    else:
        cards.sort(key=lambda c: (c.get("year") or 0, str(c.get("time", ""))), reverse=True)

    sections = []

    edu_list = p.get("education") or []
    if edu_list:
        edu_html = []
        for ed in edu_list:
            left = " · ".join(x for x in [ed.get("school"), ed.get("major"), ed.get("degree")] if x)
            t = esc(ed.get("time"))
            pts = render_points(ed.get("details") or [])
            edu_html.append(
                f'<div class="entry">'
                f'<div class="entry-head"><span class="entry-title">{esc(left)}</span><span class="entry-time">{t}</span></div>'
                f'{pts}</div>'
            )
        sections.append(("教育背景", "".join(edu_html)))

    types = cfg.get("resume_types") or [t for t in cfg.get("types", ["实习", "项目", "志愿者", "获奖", "技能"]) if t != "思考"]
    for t in types:
        entries = []
        for c in cards:
            text = pick(c, wtype, prefer) or c.get("result") or c.get("fact") if c.get("type") == t else None
            if text:
                pts = render_points(str(text).splitlines())
                if t == "技能" and not c.get("org") and not c.get("role") and not c.get("time"):
                    entries.append(f'<div class="entry">{pts}</div>')
                else:
                    heading = " · ".join(x for x in [c.get("org") or c.get("title"), c.get("role")] if x)
                    entries.append(
                        f'<div class="entry">'
                        f'<div class="entry-head"><span class="entry-title">{esc(heading)}</span><span class="entry-time">{esc(c.get("time"))}</span></div>'
                        f'{pts}</div>'
                    )
        if entries:
            sections.append((t, "".join(entries)))

    skills_list = [str(s).strip() for s in (p.get("skills") or []) if str(s).strip()]
    if skills_list:
        sections.append(("技能与语言", f'<div class="entry">{render_points(skills_list)}</div>'))

    if not sections:
        sections = [("经历", render_points(["还没有可用的简历条目"]))]

    contact_parts = []
    if p.get("location"):
        contact_parts.append(esc(p["location"]))
    if p.get("phone"):
        contact_parts.append(f"电话：{esc(p['phone'])}")
    if p.get("email"):
        contact_parts.append(f"邮箱：{esc(p['email'])}")
    for lk in p.get("links") or []:
        if lk:
            contact_parts.append(esc(lk))
    contact = " &nbsp;|&nbsp; ".join(contact_parts)

    name = p.get("name") or "姓名"
    headline = p.get("headline") or ""
    headline_html = f'<span class="headline">{esc(headline)}</span>' if headline else ""
    photo_uri = photo_data_uri(vault, p.get("photo"))
    photo_html = f'<img class="portrait" src="{photo_uri}" alt="证件照">' if photo_uri else ""

    header_html = (
        f'<header class="header">'
        f'<div class="header-main">'
        f'<div class="name-row"><h1 class="name">{esc(name)}</h1>{headline_html}</div>'
        f'<div class="contact">{contact}</div>'
        f'</div>'
        f'{photo_html}'
        f'</header>'
    )

    sec_html = "".join(f'<section><div class="sec-bar">{esc(title)}</div>{body}</section>' for title, body in sections)

    tpl = (TPL / "resume.html").read_text(encoding="utf-8")
    return tpl.replace("%%TITLE%%", esc(f"{name} - 简历")).replace("%%CONTENT%%", header_html + sec_html)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="kind", required=True)
    a2 = sub.add_parser("resume")
    a2.add_argument("vault")
    a2.add_argument("out")
    a2.add_argument("--writing", default="简历条目")
    a2.add_argument("--prefer")
    a2.add_argument("--ids")
    a = ap.parse_args()
    src = resume(Path(a.vault).expanduser(), a.writing, a.prefer, a.ids.split(",") if a.ids else None)
    Path(a.out).write_text(src, encoding="utf-8")
    print(Path(a.out).resolve())
