#!/usr/bin/env python3
"""Fill the zero-dependency print-ready HTML resume template from vault JSON.

    python3 fill_html.py resume <VAULT> <out.html> --from <简历id>      # a saved resume (resumes/<id>.json)
    python3 fill_html.py resume <VAULT> <out.html> [--writing 简历条目] [--prefer 英文] [--ids a,b,c]   # all cards
    python3 fill_html.py site   <VAULT> <out.html> [--from <简历id>] [--phone]   # a one-file personal page (no phone unless --phone)

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


def site(vault, resume_id=None, phone=False, wtype="简历条目", prefer=None):
    """A one-file personal page from the same model as the resume: header, sections, entries. Public by intent,
    so the phone number is left out unless asked for."""
    m = resume_model.build(vault, resume_id, wtype, prefer, None)
    contact = [x for x in m["contact"] if phone or not x.startswith("电话：")]
    def chip(x):
        if x.startswith("邮箱："):
            mail = x[3:]
            return f'<li><a href="mailto:{esc(mail)}">{esc(mail)}</a></li>'
        if x.startswith(("http://", "https://")) or ("." in x and "/" in x and " " not in x):
            url = x if x.startswith("http") else "https://" + x
            return f'<li><a href="{esc(url)}" target="_blank" rel="noopener">{esc(x)}</a></li>'
        return f"<li>{esc(x)}</li>"
    def line(kind, lead, text):
        cls = {"summary": ' class="summary"', "plain": ' class="plain"'}.get(kind, "")
        return f'<li{cls}>{f"<b>{esc(lead)}</b>" if lead else ""}{esc(text)}</li>'
    def entry(e):
        head = ""
        if e.get("heading") or e.get("time"):
            head = (f'<div class="entry-head"><h3>{esc(e.get("heading"))}</h3>'
                    + (f'<span class="time">{esc(e.get("time"))}</span>' if e.get("time") else "") + "</div>")
        return f'<article class="entry">{head}<ul class="lines">{"".join(line(*l) for l in e.get("lines", []))}</ul></article>'
    photo = photo_data_uri(m["photo"])
    hero = ('<header class="hero"><div>'
            f'<h1>{esc(m["name"])}</h1>' + (f'<p class="headline">{esc(m["headline"])}</p>' if m["headline"] else "")
            + (f'<ul class="contact">{"".join(chip(x) for x in contact)}</ul>' if contact else "") + "</div>"
            + (f'<img src="{photo}" alt="{esc(m["name"])}">' if photo else "") + "</header>")
    body = "".join(f'<section><h2>{esc(s["title"])}</h2>{"".join(entry(e) for e in s["entries"])}</section>' for s in m["sections"])
    tpl = (TPL / "site.html").read_text(encoding="utf-8")
    return (tpl.replace("%%TITLE%%", esc(m["name"])).replace("%%DESC%%", esc(m["headline"] or m["name"]))
               .replace("%%CONTENT%%", hero + body).replace("%%FOOTER%%", "由经历库生成"))


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
    a3 = sub.add_parser("site", help="one-file personal page")
    a3.add_argument("vault")
    a3.add_argument("out")
    a3.add_argument("--from", dest="resume_id", help="use this resume's sections and versions (recommended)")
    a3.add_argument("--phone", action="store_true", help="also show the phone number (it is public)")
    a3.add_argument("--writing", default="简历条目")
    a3.add_argument("--prefer")
    a = ap.parse_args()
    if a.kind == "site":
        src = site(Path(a.vault).expanduser(), a.resume_id, a.phone, a.writing, a.prefer)
    else:
        src = resume(Path(a.vault).expanduser(), a.writing, a.prefer, a.ids.split(",") if a.ids else None, a.resume_id)
    Path(a.out).write_text(src, encoding="utf-8")
    print(Path(a.out).resolve())
