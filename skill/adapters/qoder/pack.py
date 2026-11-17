#!/usr/bin/env python3
"""把本 skill 打包成 Qoder 可安装的 .skill（ZIP）文件。

用法：
    python3 skill/adapters/qoder/pack.py            # 输出到系统临时目录
    python3 skill/adapters/qoder/pack.py -o x.skill # 指定输出路径

只依赖标准库。会跳过 .DS_Store、._* 和 __MACOSX，并用 UTF-8 存储中文文件名。
"""

import argparse
import os
import re
import sys
import tempfile
import zipfile

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAME_RULE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def die(message):
    print(f"错误：{message}", file=sys.stderr)
    sys.exit(1)


def read_frontmatter():
    skill_md = os.path.join(SKILL_DIR, "SKILL.md")
    if not os.path.isfile(skill_md):
        die(f"找不到 {skill_md}")
    with open(skill_md, encoding="utf-8") as f:
        text = f.read()
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not match:
        die("SKILL.md 开头没有用 --- 包起来的 frontmatter")
    return match.group(1)


def validate(frontmatter):
    name_match = re.search(r"^name:\s*(\S+)\s*$", frontmatter, re.M)
    if not name_match:
        die("frontmatter 缺少 name")
    name = name_match.group(1)
    if not NAME_RULE.match(name):
        die(f"name「{name}」只能用小写字母、数字和连字符，且不能以连字符开头")

    desc_match = re.search(r"^description:\s*(.*)$", frontmatter, re.M)
    if not desc_match:
        die("frontmatter 缺少 description")
    desc = desc_match.group(1).strip()
    if desc[:1] not in ("'", '"') and ": " in desc:
        die(
            "description 含英文冒号加空格（例如 vault: logging），这不是合法 YAML，"
            "Qoder 会报 EXTENSION_SKILL_FRONTMATTER_INVALID。\n"
            "        改法：给整段 description 加双引号。"
        )

    try:
        import yaml  # 可选：装了 PyYAML 就做一次完整解析
    except ImportError:
        pass
    else:
        try:
            yaml.safe_load(frontmatter)
        except yaml.YAMLError as exc:
            die(f"frontmatter 不是合法 YAML：{exc}")
    return name


def build(name, out_path):
    count = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, dirs, files in os.walk(SKILL_DIR):
            dirs[:] = sorted(d for d in dirs if d != "__MACOSX")
            rel = os.path.relpath(root, SKILL_DIR)
            base = name if rel == "." else name + "/" + rel.replace(os.sep, "/")
            archive.write(root, base + "/")
            for filename in sorted(files):
                if filename == ".DS_Store" or filename.startswith("._"):
                    continue
                archive.write(os.path.join(root, filename), base + "/" + filename)
                count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="打包成本地 Skill 压缩包（.skill）")
    parser.add_argument("-o", "--output", help="输出路径，默认是系统临时目录下的 <name>.skill")
    args = parser.parse_args()

    name = validate(read_frontmatter())
    out_path = args.output or os.path.join(tempfile.gettempdir(), name + ".skill")
    count = build(name, out_path)

    print(f"已生成：{out_path}（{count} 个文件）")
    print("下一步：在 Qoder 的本地 Skill 安装入口选择这个文件，")
    print(f"或者对 Agent 说「安装这个本地 skill：{out_path}」。")


if __name__ == "__main__":
    main()
