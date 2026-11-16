# 07 导出 PDF

有两种 PDF：**申请记录**（自荐信、动机信，用 `letter` 模板）和**简历**（用 `resume` 模板）。

两条路：
- **快速版：** 右半屏打开某份申请记录，点「导出 PDF」按钮，浏览器会打印成 PDF。不需要你做任何事，适合急用。
- **排版版（本文件）：** 用 LaTeX 排版，效果更正式。需要电脑上装了 `xelatex` 和中文宏包 `ctex`。

**为什么用脚本填模板：** LaTeX 里 `& % $ # _ { } ~ ^ \` 这些字符有特殊含义，正文里出现就会编译失败。`fill_tex.py` 会自动处理它们，所以不要自己手写 `.tex` 正文。

---

## 第 1 步：检查 LaTeX 环境

```bash
which xelatex && kpsewhich ctex.sty && echo READY
```

- 输出里有 `READY`：继续第 2 步。
- 没有 `READY`：
  - 告诉用户：「排版版 PDF 需要安装 LaTeX（体积较大，几百 MB 到几 GB）。现在可以先用右半屏的『导出 PDF』按钮出一份简单版。要我帮你装 LaTeX 吗？」
  - 用户同意才装。macOS：`brew install --cask mactex-no-gui`（大）；或装 TinyTeX 后执行 `tlmgr install ctex`。其他系统请用户去 tug.org/texlive 下载。
  - 用户不同意：停在这里。

## 第 2 步：准备一个临时文件夹

```bash
mkdir -p /tmp/jingliku-pdf && echo READY
```

## 第 3 步：生成 .tex 文件

**申请记录**（`<申请记录id>` 是 `applications/` 里的文件名，不带 `.json`）：

```bash
python3 "<SKILL>/scripts/fill_tex.py" letter "<VAULT>" "<申请记录id>" /tmp/jingliku-pdf/out.tex
```

**简历：**

```bash
python3 "<SKILL>/scripts/fill_tex.py" resume "<VAULT>" /tmp/jingliku-pdf/out.tex
```

简历的可选参数（加在命令末尾）：
- `--prefer 英文`：每段经历优先用名字里含「英文」的版本（也可以写别的词，如 `偏数据`）。
- `--writing 英文简历条目`：用另一种写法类型（默认 `简历条目`）。
- `--ids xhs-2025,fair-2024`：只放这几段经历，并按这个顺序。

简历顶部的姓名、邮箱来自 `<VAULT>/config.json` 的 `profile`。如果 `name` 是空的，先问用户名字和联系方式，写进 `profile`（改完校验 JSON），再生成。

- 期望结果：命令打印出 `.tex` 文件的路径。
- 报错 `No such file`：id 写错了，用 `ls "<VAULT>/applications/"` 看看正确的名字。

## 第 4 步：编译

```bash
cd /tmp/jingliku-pdf && xelatex -interaction=nonstopmode -halt-on-error out.tex > /dev/null 2>&1 && echo PDF_OK || tail -30 out.log
```

- 输出 `PDF_OK`：成功，PDF 在 `/tmp/jingliku-pdf/out.pdf`。
- 否则会打印日志末尾，按 `recipes/09-踩坑与解决.md` 的「LaTeX」部分处理。

## 第 5 步：放到用户想要的位置

问用户存哪里；没说就放「下载」文件夹，文件名用文档标题：

```bash
cp /tmp/jingliku-pdf/out.pdf "$HOME/Downloads/<文档标题>.pdf" && echo SAVED
```

告诉用户：「PDF 已保存到 下载/<文档标题>.pdf。」

## 用户想改版式

- 只改这一次：在第 3 步和第 4 步之间，编辑 `/tmp/jingliku-pdf/out.tex`（字号、页边距在文件开头），再做第 4 步。
- 以后都这样：改 `<SKILL>/templates/latex/` 里的模板。模板里 `%%NAME%%` 这类占位符不要删。
