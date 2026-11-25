#!/usr/bin/env python3
"""The resume sheet is rendered twice: by the front end (JS rbody in skill/app/index.html) and by
resume_model.py (Python, used for the print page and LaTeX). This checks both split every writing
version into the same lines — summary / bold lead-in / plain point — so the preview never disagrees
with the exported PDF.

    python3 tools/test_render_parity.py      # needs node; prints PASS or each mismatch, exit 1 on mismatch
"""
import glob, html, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skill/scripts"))
import resume_model  # noqa: E402

EDGE = [
    "围绕「话题互动量」目标，从三个方向提升表现。\n选题策划：每周输出 5 条选题建议。\n数据复盘：按周跟踪 5 项指标。",
    "只有一行，没有小标题。",
    "第一行\n第二行，也没有小标题",
    "- 带短横的要点：会去掉短横\n• 带圆点的要点\n· 带间隔号的要点",
    "GPA：3.8 / 4.0（专业前 10%）",
    "Skills: Python, SQL\nLanguages: English (IELTS 7.0)",
    "这一句冒号前面超过十六个字所以不算小标题吧对吧：后半句",
    "\n\n  前后有空行和空格  \n\n",
    "概述没有小标题\n小标题：正文\n又一行没有小标题",
    "冒号：\n空正文的冒号行",
    "A&B <tag> \"quote\"：特殊字符",
    "Time:10am 没有空格的英文冒号不算小标题",
    "网址：https://example.com/a:b",
    "行尾有短横 -\n行首全角空格\u3000开头：正文",
    "Windows 换行：第一行\r\n第二行：正文",
    "英文 Lead: with space\n中文小标题：正文",
]


def js_lines(texts):
    src = (ROOT / "skill/app/index.html").read_text(encoding="utf-8")
    esc = re.search(r"const esc=s=>.*?;\n", src).group(0)
    lead = re.search(r"const rlead=l=>\{.*?\};\n", src).group(0)
    body = re.search(r"function rbody\(text\)\{.*?\.join\(''\)\}\n", src, re.S).group(0)
    prog = esc + lead + body + r"""
const texts=JSON.parse(require('fs').readFileSync(0,'utf8'));
console.log(JSON.stringify(texts.map(t=>rbody(t))));"""
    out = subprocess.run(["node", "-e", prog], input=json.dumps(texts), capture_output=True, text=True, check=True).stdout
    parsed = []
    for h in json.loads(out):
        lines = []
        for cls, inner in re.findall(r'<p class="rp-(sum|pt)">(.*?)</p>', h):
            m = re.match(r"<b>(.*?)</b>(.*)", inner)
            lead, text = (m.group(1), m.group(2)) if m else ("", inner)
            lines.append(("summary" if cls == "sum" else "point", html.unescape(lead), html.unescape(text)))
        parsed.append(lines)
    return parsed


def main():
    if not shutil.which("node"):
        print("SKIPPED node not installed"); return
    texts = []
    for f in sorted(glob.glob(str(ROOT / "skill/examples/sample-vault/experiences/*.json"))):
        c = json.loads(Path(f).read_text(encoding="utf-8"))
        texts += [v["text"] for w in c.get("writings", []) for v in w.get("versions", [])]
        texts += [c.get("fact") or "", c.get("result") or ""]
    texts += EDGE
    js = js_lines(texts)
    bad = 0
    for t, j in zip(texts, js):
        py = [tuple(x) for x in resume_model.body_lines(t)]
        if py != j:
            bad += 1
            print("MISMATCH", json.dumps(t, ensure_ascii=False)[:80])
            print("  python:", py)
            print("  js:    ", j)
    print(f"{'PASS' if not bad else 'FAIL'} {len(texts) - bad}/{len(texts)} texts render the same in the front end and resume_model.py")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
