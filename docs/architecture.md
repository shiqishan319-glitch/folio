# 经历库 Skill 架构（v0.2）

> 2026-11-16。目标：一个开箱即用、活在 AI 工具（harness）里的「超级 Skill」。左半屏是 AI 对话，右半屏是内置浏览器里的经历库前端，两边读写同一份本地数据。

## 核心哲学：AI 就是后端

后端操作不预先写成代码，而是写成知识交给宿主里的 AI：数据格式、目录约定、操作步骤都写进 `SKILL.md`，AI 现场读写文件、建快捷方式、排版 PDF。

- **代码尽量轻。** 唯一的代码是一根「细管子」`serve.py`（约 120 行，Python 标准库）。
- **管子不懂业务。** 它只做四件事：提供前端页面、读数据目录里的文件、列目录、写入或删除 JSON。
- **为什么还需要管子：** 用户在右半屏点按钮时 AI 不在场，而浏览器不允许网页直接写本地文件。

| 谁 | 负责什么 |
|---|---|
| 宿主 AI（照 SKILL.md） | 入库拆卡、去重、追问、检索召回、生成写法、回存、挂作品快捷方式、检查文件是否被移动、LaTeX 排版导出 PDF、环境检查 |
| 前端（单个 HTML） | 浏览、筛选、取用；轻量编辑（新增、删除、改名、编辑写法）通过管子写回；轮询目录发现 AI 的改动并自动刷新；浏览器打印导出 PDF |
| `serve.py`（管子） | 页面 + `/vault/` 文件读写，只监听 127.0.0.1，写入需要口令 |

## 目录结构

```
skill/                       ← Skill 包（装进 harness）
├── SKILL.md                 给 AI 的全部 know-how
├── references/
│   └── data-format.md       数据格式（AI 第一次写数据前必读）
├── app/index.html           前端（v10 精致 Bento）
├── scripts/serve.py         唯一的代码：细管子
├── templates/latex/         letter.tex（申请记录）、resume.tex（简历）
├── examples/sample-vault/   示例数据（Demo 里的虚构经历）
└── adapters/                各 harness 的安装与打开方式
    ├── claude-code/
    ├── antigravity/
    ├── dsh/
    ├── qoder/
    ├── workbuddy/
    ├── doubao/
    └── codex/               （待验证）

~/folio/                    ← 用户数据，和 skill 分开放，升级 skill 不会动到
├── config.json              经历类型、个人信息
├── experiences/<id>.json    一段经历一个文件
├── applications/<id>.json   申请记录（整篇文档，按段落关联经历）
├── assets/<id>/<文件>       作品的快捷方式（软链接），大文件不复制
└── .trash/                  删除的文件移到这里
```

## 关键决定

1. **数据用 JSON。** AI 写、前端读都最稳，不需要 YAML 解析库。正文字段里可以写 Markdown。
2. **作品只存快捷方式。** 在 `assets/<卡片id>/` 下建软链接指向原文件，同时记下原路径、大小和修改时间。原文件被移动后，AI 能发现并按文件名帮忙找回（PRD 需求 B5）。数据目录因此始终很小。
3. **删除不真删。** 一律移到 `.trash/`。
4. **安全。** 管子只监听 127.0.0.1，检查 `Host` 防 DNS rebinding；写入需要页面里注入的随机口令，并检查 `Origin`，防止浏览器里的其他网站改数据。
5. **PDF 两条路。** 前端「导出 PDF」按钮用浏览器打印，马上就能出；要高质量排版，让 AI 用 LaTeX 模板和 xelatex 生成（需要 ctex 宏包）。

## 各 harness 的打开方式

详见 [`skill/adapters/README.md`](../skill/adapters/README.md)：

| Harness | 安装 | 右半屏 | 状态 |
|---|---|---|---|
| Claude Code 桌面版 | 软链到 `~/.claude/skills/jingliku` | 内置浏览器打开 localhost | 已实测 |
| Claude Code CLI | 同上 | 无内置浏览器，用系统浏览器 | 可用 |
| Google Antigravity | 软链到 `~/.gemini/config/skills/jingliku` | 内置 `browser` subagent 打开 localhost | 已实测 |
| DeepSeek Harness (DSH) | 软链到 `~/.agents/skills/jingliku` | 右侧栏 Browser 标签页打开 localhost | 已实测 |
| Qoder 桌面版 | `pack.py` 打包成 `.skill` 安装到 `~/.qoder/skills/jingliku` | 内置浏览器（`browser-use`）打开 localhost | 已实测 |
| WorkBuddy（腾讯） | 复制到 `~/.workbuddy/skills/jingliku` | 内置预览面板打开 localhost | 已实测 |
| 豆包桌面版（Agent 模式） | 复制到 `.../workspace/.user_skills/jingliku` | 右侧工作区 browser 标签页打开 localhost | 已实测 |
| Codex | AGENTS.md 指向 SKILL.md | 待验证 | 待验证 |

## 下一步

- **已完成**：C1 前端接入本地真实数据（`/vault/` 读写 + 轮询自动刷新）、C2 图片缩略图展示、LaTeX PDF 导出（`fill_tex.py`）、GitHub 自动更新检查（`check_update.py`）、主流 AI 工具适配（`skill/adapters/`）。
- **待推进**：
  - 本地视频拖动进度条所需的 Range 请求支持（C3）。
  - 用真实素材走完一个周期的「入库 → 申请 → 回存」持续试用。

## 已删除的方案（v0.1）

v0.1 曾把后端写成四个 Python 脚本（数据层 `vault.py`、渲染 `render.py`、服务 `serve.py`、环境检查 `doctor.py`）。按「AI 就是后端」的思路，除管子外都改成了 SKILL.md 里的说明。
