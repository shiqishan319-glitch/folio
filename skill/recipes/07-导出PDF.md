# 07 导出 PDF

有两种 PDF：**申请记录**（自荐信、动机信，用 `letter` 模板）和**简历**（用 `resume` 模板）。

两条路：
- **排版版（默认，推荐）：** 用 LaTeX（`xelatex` + `ctex`）排版，效果最正式稳定。AI 收到导出请求时**默认先走这条路**。
- **网页打印版（零依赖兜底 / 右半屏快捷按钮）：** 当电脑未安装 LaTeX 时作为降级方案；右半屏也提供了「打印版简历」和申请记录「导出 PDF」快捷按钮，直接调用浏览器打印成 PDF。

**为什么用脚本填模板：** 脚本会自动处理特殊字符转义（如 LaTeX 里的 `& % $ # _ { } ~ ^ \`）、证件照内嵌和字段排版，不要自己手写模板正文。

---

## 第 1 步：检查 LaTeX 环境

```bash
which xelatex && kpsewhich ctex.sty && echo READY
```

- 输出里有 `READY`：继续第 2 步（走 LaTeX 导出）。
- 没有 `READY`：
  - 告诉用户：「电脑上还没装 LaTeX（体积几百 MB 到几 GB）。我可以先帮你生成**零依赖网页打印版简历**（浏览器 `Cmd/Ctrl + P` 即可存为 A4 PDF），或者现在安装 LaTeX。你想先用打印版，还是装 LaTeX？」
  - 用户选打印版：跳到文末「备选：零依赖网页打印版简历」。
  - 用户同意装 LaTeX 才装。macOS：`brew install --cask mactex-no-gui`（大）；或装 TinyTeX 后执行 `tlmgr install ctex`。其他系统请用户去 tug.org/texlive 下载。

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

简历顶部的姓名、联系方式、教育背景和技能来自 `<VAULT>/config.json` 的 `profile`：
- 如果 `profile.name` 或 `profile.education` 是空的：可以先问用户姓名、所在城市/到岗时间（`location`）、联系方式（邮箱/电话）及教育背景（学校、专业、学历、时间、GPA/主修课程），写进 `<VAULT>/config.json` 并校验（见 `recipes/06-修改删除.md`）；也可以提醒用户直接在右半屏左侧栏点「个人信息」自己填好保存。用户不需要放教育背景就留空 `[]`。
- 如果用户提供了**证件照**（`photo`）：证件照体积很小且随时要用于导出简历，**鼓励直接复制一份放进 `<VAULT>/assets/portrait.<扩展名>`**，并在 `config.json` 里写相对路径 `"photo": "assets/portrait.<扩展名>"`，避免原图被清理后失效。
- 如果用户需要展示**技能与语言**、**所在城市 / 到岗时间**且希望按不同岗位/语言切换版本：鼓励建一张 `type: "技能"` 的经历卡片（如 `skills.json`、`availability.json`），把不同侧重的版本放进 `writings` 的「简历条目」里，导出时就能用 `--prefer 英文` / `--prefer 数据` 自动选版，不需要在 `config.json` 里写死。
- 如果用户只在 `config.json` 的 `profile.skills` 里写了纯列表，脚本也会作为兜底在简历底部渲染「技能与语言」板块。

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

---

## 备选：零依赖网页打印版简历（无 LaTeX 时兜底）

```bash
python3 "<SKILL>/scripts/fill_html.py" resume "<VAULT>" "$HOME/Downloads/简历-打印版.html"
```

可选参数与 `fill_tex.py` 一致（`--prefer`、`--writing`、`--ids`）。生成后在系统浏览器打开该 `.html` 文件，点击右上角「打印 / 存为 PDF」（或 `Cmd/Ctrl + P`），勾选「背景图形」即可保存为 A4 PDF。用户也可以直接在右半屏左侧栏点「打印版简历」快捷打开。
