#!/usr/bin/env python3
"""Resume model shared by fill_tex.py (LaTeX) and fill_html.py (print page), plus two helpers for the AI.

    python3 resume_model.py check <VAULT> [<简历id>]        # every reference still points at a card version?
    python3 resume_model.py sync  <VAULT> <简历id> [--sent]  # refresh the text snapshots; --sent also freezes it

check prints one line per resume: "OK <id>" or "BROKEN <id>: <card>/<version> (<why>)".
sync prints "SYNCED <id>" (draft: snapshots now equal the card versions) or "SENT <id> <date>".

A resume (resumes/<id>.json) lists which version of which card goes where; the text itself lives on the
card. Each item also keeps a snapshot "text": a draft shows the card's current version, a sent resume
(status 已投递) shows its snapshots, so what was sent never changes.
Standard library only.
"""
import argparse, datetime, json, os, re, sys
from pathlib import Path

WT = "简历条目"
SECTION_TITLES = {"实习": "实习经历", "项目": "项目经历", "志愿者": "志愿经历", "获奖": "荣誉奖项", "技能": "技能与语言"}
SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def cards_by_id(vault):
    out = {}
    for f in sorted((vault / "experiences").glob("*.json")):
        try:
            c = load(f)
        except (OSError, ValueError):
            continue
        out[c.get("id") or f.stem] = c
    return out


def versions(card, wtype=WT):
    for w in card.get("writings", []):
        if w.get("type") == wtype:
            return w.get("versions") or []
    return []


def version_text(card, name, wtype=WT):
    for v in versions(card, wtype):
        if v.get("name") == name:
            return v.get("text")
    return None


def pick(card, wtype, prefer):
    vs = versions(card, wtype)
    for v in vs:
        if prefer and prefer in v.get("name", ""):
            return v.get("text")
    return vs[0].get("text") if vs else None


# ---------- one writing version -> lines ----------
def split_lead(line):
    """「产品功能优化：……」 -> ("产品功能优化：", "……"); no short lead-in -> None."""
    for sep in ("：", ": "):
        if sep in line:
            prefix, rest = line.split(sep, 1)
            if 1 <= len(prefix.strip()) <= 16 and rest.strip():
                return prefix.strip() + sep.strip(), rest.strip()
    return None


def body_lines(text):
    """-> [("summary", "", text) | ("point", lead, text)]. When the other lines start with a lead-in,
    an opening line without one is the entry's summary (rendered without a bullet)."""
    lines = [l.strip(" -•·") for l in str(text or "").splitlines() if l.strip(" -•·")]
    any_lead = any(split_lead(l) for l in lines)
    out = []
    for i, l in enumerate(lines):
        lead = split_lead(l)
        if i == 0 and len(lines) > 1 and any_lead and not lead:
            out.append(("summary", "", l))
        else:
            out.append(("point",) + (lead or ("", l)))
    return out


def plain_lines(items):
    out = []
    for d in items or []:
        d = str(d).strip()
        if d:
            out.append(("plain",) + (split_lead(d) or ("", d)))
    return out


def card_entry(c, text):
    entry = {"heading": "", "time": "", "lines": body_lines(text)}
    if not (c.get("type") == "技能" and not c.get("org") and not c.get("role") and not c.get("time")):
        entry["heading"] = " - ".join(x for x in [c.get("org") or c.get("title"), c.get("role")] if x)
        entry["time"] = c.get("time") or ""
    return entry


def education_section(profile, title="教育经历"):
    entries = []
    for ed in profile.get("education") or []:
        major = " ".join(x for x in [ed.get("major"), ed.get("degree")] if x)
        entries.append({"heading": " - ".join(x for x in [ed.get("school"), major] if x),
                        "time": ed.get("time") or "", "lines": plain_lines(ed.get("details")),
                        "parts": [ed.get("school") or "", ed.get("major") or "", ed.get("degree") or ""]})
    return {"title": title, "entries": entries} if entries else None


def photo_path(vault, raw):
    if not raw:
        return ""
    cand = Path(raw).expanduser()
    if not cand.is_absolute():
        cand = vault / cand
    return str(cand.resolve()) if cand.is_file() else ""


def build(vault, resume_id=None, wtype=WT, prefer=None, ids=None):
    """-> {name, headline, contact:[...], photo, title, sections:[{title, entries:[{heading, time, lines}]}]}.
    With resume_id: follow resumes/<id>.json. Without: every card of the resume types (the old behaviour)."""
    vault = Path(vault)
    cfg = load(vault / "config.json") if (vault / "config.json").exists() else {}
    p = cfg.get("profile") or {}
    cards = cards_by_id(vault)
    model = {"name": p.get("name") or "姓名", "headline": p.get("headline") or "",
             "contact": [x for x in [p.get("location"), p.get("phone") and f"电话：{p['phone']}",
                                     p.get("email") and f"邮箱：{p['email']}", *(p.get("links") or [])] if x],
             "photo": photo_path(vault, p.get("photo")), "title": "", "sections": []}

    if resume_id:
        if not SAFE_ID.match(resume_id):
            raise ValueError(f"bad resume id: {resume_id}")
        r = load(vault / "resumes" / f"{resume_id}.json")
        model["title"] = r.get("title") or ""
        header = r.get("header") or {}
        if "headline" in header:
            model["headline"] = header.get("headline") or ""
        if header.get("photo") is False:
            model["photo"] = ""
        sent = r.get("status") == "已投递"
        for s in r.get("sections") or []:
            if s.get("from") == "education":
                sec = education_section(p, s.get("title") or "教育经历")
                if sec:
                    model["sections"].append(sec)
                continue
            entries = []
            for it in s.get("items") or []:
                c = cards.get(it.get("card"))
                if not c:
                    continue  # check() reports it; never invent a heading for a missing card
                live = version_text(c, it.get("version"), it.get("writing") or WT)
                text = it.get("text") if sent or live is None else live
                if text:
                    entries.append(card_entry(c, text))
            if entries:
                model["sections"].append({"title": s.get("title") or "", "entries": entries})
        return model

    chosen = list(cards.values())
    if ids:
        chosen = [cards[i] for i in ids if i in cards]
    else:
        chosen.sort(key=lambda c: (c.get("year") or 0, str(c.get("time", ""))), reverse=True)
    sec = education_section(p)
    if sec:
        model["sections"].append(sec)
    types = cfg.get("resume_types") or [t for t in cfg.get("types", ["实习", "项目", "志愿者", "获奖", "技能"]) if t != "思考"]
    for t in types:
        entries = []
        for c in chosen:
            if c.get("type") != t:
                continue
            text = pick(c, wtype, prefer) or c.get("result") or c.get("fact")
            if text:
                entries.append(card_entry(c, text))
        if entries:
            model["sections"].append({"title": SECTION_TITLES.get(t, t), "entries": entries})
    skills = plain_lines(p.get("skills"))
    if skills:
        model["sections"].append({"title": "技能与语言", "entries": [{"heading": "", "time": "",
                                  "lines": [("point", lead, text) for _, lead, text in skills]}]})
    return model


# ---------- helpers for the AI ----------
def problems(vault, r):
    cards, out = cards_by_id(vault), []
    for s in r.get("sections") or []:
        for it in s.get("items") or []:
            cid, ver = it.get("card"), it.get("version")
            c = cards.get(cid)
            if not c:
                out.append(f"{cid}/{ver} (no such card)")
            elif version_text(c, ver, it.get("writing") or WT) is None:
                out.append(f"{cid}/{ver} (no such version; snapshot kept)")
    return out


def cmd_check(vault, rid):
    files = [vault / "resumes" / f"{rid}.json"] if rid else sorted((vault / "resumes").glob("*.json"))
    bad = 0
    for f in files:
        try:
            r = load(f)
        except (OSError, ValueError) as e:
            print(f"BROKEN {f.stem}: cannot read ({type(e).__name__})"); bad += 1; continue
        ps = problems(vault, r)
        for x in ps:
            print(f"BROKEN {f.stem}: {x}")
        if not ps:
            print(f"OK {f.stem}")
        bad += bool(ps)
    if not files:
        print("OK (no resumes yet)")
    return 1 if bad else 0


def cmd_sync(vault, rid, sent):
    f = vault / "resumes" / f"{rid}.json"
    r, cards = load(f), cards_by_id(vault)
    if r.get("status") == "已投递":
        print(f"SKIPPED {rid}: already sent, its text is frozen (copy it to a new draft to change it)"); return 0
    for s in r.get("sections") or []:
        for it in s.get("items") or []:
            c = cards.get(it.get("card"))
            live = version_text(c, it.get("version"), it.get("writing") or WT) if c else None
            if live is not None:
                it["text"] = live
    now = datetime.datetime.now().astimezone()
    if sent:
        r["status"], r["sent"] = "已投递", now.strftime("%Y-%m-%d")
    r["updated"] = now.isoformat(timespec="seconds")
    tmp = f.with_name(f".{f.name}.tmp")
    tmp.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, f)
    ps = problems(vault, r)
    print(f"SENT {rid} {r['sent']}" if sent else f"SYNCED {rid}")
    for x in ps:
        print(f"BROKEN {rid}: {x}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("check"); a.add_argument("vault"); a.add_argument("id", nargs="?")
    b = sub.add_parser("sync"); b.add_argument("vault"); b.add_argument("id"); b.add_argument("--sent", action="store_true")
    args = ap.parse_args()
    v = Path(args.vault).expanduser()
    if getattr(args, "id", None) and not SAFE_ID.match(args.id):
        sys.exit(f"bad resume id: {args.id}")
    sys.exit(cmd_check(v, args.id) if args.cmd == "check" else cmd_sync(v, args.id, args.sent))
