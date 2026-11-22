#!/usr/bin/env python3
"""Fill a LaTeX template from vault JSON, escaping special characters safely.
(Escaping by hand is the step small models get wrong, so it lives here.)

    python3 fill_tex.py letter <VAULT> <application-id> <out.tex>
    python3 fill_tex.py resume <VAULT> <out.tex> --from <简历id>      # a saved resume (resumes/<id>.json)
    python3 fill_tex.py resume <VAULT> <out.tex> [--writing 简历条目] [--prefer 英文] [--ids a,b,c]   # quick look: all cards

Then compile:  cd <dir of out.tex> && xelatex -interaction=nonstopmode -halt-on-error <out.tex>
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import resume_model  # noqa: E402  (shared with fill_html.py)

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


def line_tex(kind, lead, text):
    if kind == "summary":
        return f"\\summaryline{{{tex(text)}}}"
    return f"\\{'plainline' if kind == 'plain' else 'point'}{{{tex(lead)}}}{{{tex(text)}}}"


def entry_tex(e):
    out = []
    if e.get("parts"):  # education: 「学校 - 专业 学历」; \enspace keeps the gap xeCJK would drop between Chinese words
        school, major, degree = e["parts"]
        right = "\\enspace ".join(tex(x) for x in [major, degree] if x)
        left = " - ".join(x for x in [tex(school) if school else "", right] if x)
        out.append(f"\\entry{{{left}}}{{{tex(e.get('time'))}}}")
    elif e.get("heading") or e.get("time"):
        out.append(f"\\entry{{{tex(e.get('heading'))}}}{{{tex(e.get('time'))}}}")
    out += [line_tex(*l) for l in e.get("lines", [])]
    return "\n".join(out)


def resume(vault, wtype="简历条目", prefer=None, ids=None, resume_id=None):
    m = resume_model.build(vault, resume_id, wtype, prefer, ids)
    blocks = [(s["title"], "\n".join(entry_tex(e) for e in s["entries"])) for s in m["sections"]]
    if not blocks:
        blocks = [("经历", "\\point{}{还没有可用的简历条目}")]
    contact = "\\enspace|\\enspace\\allowbreak ".join(tex(x) for x in m["contact"])  # a wrapped line never starts with 「|」
    first_title, first_body = blocks[0]
    parts = [f"\\resumeheader{{{tex(m['name'])}}}{{{tex(m['headline'])}}}{{{contact}}}{{{m['photo']}}}{{{tex(first_title)}}}", first_body]
    for title, body in blocks[1:]:
        parts += [f"\\resumesection{{{tex(title)}}}", body]
    return fill("resume.tex", {"CONTENT": "\n\n".join(parts)})


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="kind", required=True)
    a1 = sub.add_parser("letter"); a1.add_argument("vault"); a1.add_argument("id"); a1.add_argument("out")
    a2 = sub.add_parser("resume"); a2.add_argument("vault"); a2.add_argument("out")
    a2.add_argument("--from", dest="resume_id", help="简历 id in resumes/ (recommended); without it: all cards")
    a2.add_argument("--writing", default="简历条目"); a2.add_argument("--prefer"); a2.add_argument("--ids")
    a = ap.parse_args()
    v = Path(a.vault).expanduser()
    if a.kind == "letter":
        src = letter(v, a.id)
    else:
        src = resume(v, a.writing, a.prefer, a.ids.split(",") if a.ids else None, a.resume_id)
    Path(a.out).write_text(src, encoding="utf-8")
    print(Path(a.out).resolve())
