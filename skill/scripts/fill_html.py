#!/usr/bin/env python3
"""Fill the zero-dependency print-ready HTML resume template from vault JSON.

    python3 fill_html.py resume <VAULT> <out.html> --from <简历id>      # a saved resume (resumes/<id>.json)
    python3 fill_html.py resume <VAULT> <out.html> [--writing 简历条目] [--prefer 英文] [--ids a,b,c]   # all cards

Open the generated HTML in any browser and press Cmd/Ctrl + P to save as PDF.
Same layout as templates/latex/resume.tex; both are built from resume_model.build().
"""
import argparse, base64, html, mimetypes, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import resume_model  # noqa: E402

TPL = Path(__file__).resolve().parent.parent / "templates" / "html"


def esc(s):
    return html.escape(str(s or ""), quote=True)


def photo_data_uri(path):
    if not path:
        return ""
    mime, _ = mimetypes.guess_type(path)
    if not mime or not mime.startswith("image/"):
        mime = "image/png"
    return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode('ascii')}"


def line_html(kind, lead, text):
    lead_html = f"<b>{esc(lead)}</b>" if lead else ""
    cls = "pt" if kind == "point" else "ln"
    return f'<p class="{cls}">{lead_html}{esc(text)}</p>'


def entry_html(e):
    head = ""
    if e.get("heading") or e.get("time"):
        head = f'<div class="entry-head"><span>{esc(e.get("heading"))}</span><span class="entry-time">{esc(e.get("time"))}</span></div>'
    return f'<div class="entry">{head}{"".join(line_html(*l) for l in e.get("lines", []))}</div>'


def resume(vault, wtype="简历条目", prefer=None, ids=None, resume_id=None):
    m = resume_model.build(vault, resume_id, wtype, prefer, ids)
    sections = m["sections"] or [{"title": "经历", "entries": [{"lines": [("point", "", "还没有可用的简历条目")]}]}]
    contact = '<span class="sep">|</span>'.join(esc(x) for x in m["contact"])
    photo = photo_data_uri(m["photo"])
    header = (f'<header class="header"><div class="header-main"><h1 class="name">{esc(m["name"])}</h1>'
              + (f'<div class="headline">{esc(m["headline"])}</div>' if m["headline"] else "")
              + f'<div class="contact">{contact}</div></div>'
              + (f'<img class="portrait" src="{photo}" alt="证件照">' if photo else "") + "</header>")
    body = "".join(f'<section><div class="sec-title">{esc(s["title"])}</div>{"".join(entry_html(e) for e in s["entries"])}</section>'
                   for s in sections)
    title = f'{m["name"]} - {m["title"] or "简历"}'
    tpl = (TPL / "resume.html").read_text(encoding="utf-8")
    return tpl.replace("%%TITLE%%", esc(title)).replace("%%CONTENT%%", header + body)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="kind", required=True)
    a2 = sub.add_parser("resume")
    a2.add_argument("vault")
    a2.add_argument("out")
    a2.add_argument("--from", dest="resume_id", help="简历 id in resumes/ (recommended); without it: all cards")
    a2.add_argument("--writing", default="简历条目")
    a2.add_argument("--prefer")
    a2.add_argument("--ids")
    a = ap.parse_args()
    src = resume(Path(a.vault).expanduser(), a.writing, a.prefer, a.ids.split(",") if a.ids else None, a.resume_id)
    Path(a.out).write_text(src, encoding="utf-8")
    print(Path(a.out).resolve())
