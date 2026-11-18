# 经历库

一个住在本地、由 AI 维护的个人经历数据库。每段经历只存一份；申请时按场景检索，生成对应的写法；生成结果存回库里，下次直接复用。

> 当前版本：**`v0.3.4`**（v10 精致 Bento 前端 + 零依赖 HTML 打印版简历 + 多模态作品集分层存储与语义索引 + 个人信息/教育背景置底卡片 + 简历/申请信 LaTeX PDF 导出 + 已适配 7 款主流 AI 工具）。

## 为什么做

申请很频繁（志愿者、评奖评优、网申、面试），每次都要把经历重新归纳一遍。卡住的不是「想不起有哪些经历」，而是三件事：

1. 素材散在备忘录、Word、相册、网盘、聊天记录里；
2. 录入时没人追问，事后补不回数字、难点和思考；
3. 同一段经历有很多种写法，版本散落在各个面试文件里。

经历库把组织单位从「一次申请」换成「一段经历」：一段经历一张卡片，各种写法挂在卡片下。

## 产品形态

```
  左半屏：AI 对话（Claude Code / Antigravity / DSH / 豆包 …）   右半屏：经历库前端
  ┌──────────────────────────────┐   ┌──────────────────────────────┐
  │ Skill：入库、追问、检索、生成、回存 │   │ 浏览、筛选、多版本对比、轻量编辑  │
  └──────────────┬───────────────┘   └──────────────┬───────────────┘
                 └──────────── 同一份本地数据 ────────────┘
```

- **AI 做重活，前端做轻活**：批量入库、追问、检索、生成、LaTeX PDF 排版由 Skill 完成；右半屏前端负责浏览、对比、取用和轻量编辑。
- **数据和产品都在本地**：所有数据存在 `~/经历库/`，不收集用户数据。换 AI 工具只需挂载 Skill，数据不用搬家。
- **只在电脑上维护**：专注桌面端与常用 AI 工具协同。
- **多模态作品集「分层存储 + 语义索引」**：面对 PPT、视频、截图、PDF 等异构资料，既不让经历库体积爆炸，又能秒级找回与检索：
  - **Tier 0（在线链接）**：飞书 / Notion / GitHub / Figma 等只存 URL，0 体积；
  - **Tier 1（≤ 5 MB 轻文件内收）**：证件照、证书、核心截图直接 `copy` 进 `assets/`，换设备不丢失；
  - **Tier 2（> 5 MB 重资产外置）**：大视频、大型 PPT 保留在原位置，仅挂软链接 + `sha256` 指纹（原文件挪走可通过 Spotlight 一键 `relink` 找回），并搭配 `serve.py` HTTP Range 流式播放；
  - **Tier 3（轻量语义索引）**：入库时由 AI 提炼 1–3 句 `summary` 纯文本摘要写进卡片 JSON，用几百字节换取全库搜索与 AI 秒级召回。

## 安装与开始使用

环境要求：`Python >= 3.9`（纯标准库，无需安装第三方包）。

### 方式一：一句话让你的 AI 自己安装（推荐）

把本仓库下载到电脑上，直接对你的 AI 工具说：

> 请读一下 `/path/to/Sqs经历库/skill/adapters/README.md`，帮我把经历库 skill 安装到当前工具并启动。

AI 会按你正在用的工具找到对应的安装说明，完成安装、确认数据目录（默认 `~/经历库`），并在右半屏打开经历库页面。

### 方式二：按工具手动安装

各工具的安装位置、右半屏打开方式和避坑说明见 [`skill/adapters/README.md`](skill/adapters/README.md)：

| 工具 | 用户级安装位置 | 安装方式 | 右半屏前端 | 详细说明 |
|---|---|---|---|---|
| Claude Code（桌面版 / CLI） | `~/.claude/skills/jingliku` | 软链接 | 内置浏览器（预览面板） | [`claude-code/README.md`](skill/adapters/claude-code/README.md) |
| Google Antigravity（AGY） | `~/.gemini/config/skills/jingliku` | 软链接 | 内置浏览器（`browser` subagent） | [`antigravity/README.md`](skill/adapters/antigravity/README.md) |
| DeepSeek Harness（DSH） | `~/.agents/skills/jingliku` | 软链接 | 右侧栏 Browser 标签页 | [`dsh/README.md`](skill/adapters/dsh/README.md) |
| Qoder（桌面版 / CLI） | `~/.qoder/skills/jingliku` | `pack.py` 打包成 `.skill` 安装 | 内置浏览器 / `browser-use` | [`qoder/README.md`](skill/adapters/qoder/README.md) |
| WorkBuddy（腾讯） | `~/.workbuddy/skills/jingliku` | 复制 | 内置预览面板 | [`workbuddy/README.md`](skill/adapters/workbuddy/README.md) |
| 豆包（Doubao 桌面版） | `.../workspace/.user_skills/jingliku` | 复制 | 右侧工作区 browser 标签页 | [`doubao/README.md`](skill/adapters/doubao/README.md) |
| Codex | `~/.codex/AGENTS.md` 里加一段引用 | 写指引 | 无内置，给地址 | [`codex/README.md`](skill/adapters/codex/README.md) |

## 仓库结构

```
.
├── README.md                 本文件
├── docs/
│   ├── PRD.md                经历库 PRD v0.1（需求背景、目标、流程、需求 List、待解决问题）
│   ├── architecture.md       Skill 架构：AI 就是后端，代码只有一根细管子
│   └── notes/
│       └── 2026-11-11-思考.md  原始头脑风暴笔记
├── skill/                    经历库 Skill 包（装进 Claude Code / Codex / Qoder / WorkBuddy / DSH 等）
│   ├── SKILL.md              给 AI 的全部 know-how
│   ├── references/data-format.md  数据格式
│   ├── app/index.html        前端（v10）
│   ├── VERSION               版本号（改了 skill 就加一）
│   ├── scripts/serve.py      本地细管子（Python 标准库）
│   ├── scripts/check_update.py  每次会话检查 GitHub 有没有新版本
│   ├── templates/latex/      申请记录、简历 LaTeX 模板
│   ├── examples/sample-vault/ 示例数据
│   └── adapters/             各 harness 的安装与打开方式
├── skill/evals/              skill 的测试用例（skill-creator 格式）
└── demo/
    ├── index.html            前端静态演示（v10 精致 Bento，虚构数据，不保存）
    ├── screenshots/          v10 全屏 / 半屏截图；archive/ 里是其他风格的截图
    └── variants/archive/     已归档的风格：原版 v0、v1–v9、风格比选页
```

## 看 Demo

Demo 是纯静态页面，不需要安装依赖。推荐用本地服务器打开（产品将来也是这样跑在 AI 工具的内置浏览器里）：

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory demo
```

然后访问 <http://127.0.0.1:8765/>（v10 静态演示）。归档的风格在 <http://127.0.0.1:8765/variants/archive/风格比选.html>。在 Claude Code 里也可以直接用 `.claude/launch.json` 里的 `demo` 配置启动预览。

也可以直接双击 `demo/index.html` 用浏览器打开。

静态演示用虚构数据，所有操作都不会真的保存。能读写真实数据的版本是 `skill/app/index.html`，要通过 `skill/scripts/serve.py` 打开（见 `skill/SKILL.md`）。

### 视觉风格：已选定 v10 精致 Bento（2026-11-16）

前端视觉以 v10 为准（静态演示 [`demo/index.html`](demo/index.html)，可编辑版 [`skill/app/index.html`](skill/app/index.html)）：v1 精致产品感的质感和字体，Bento 卡片布局（紧凑的统计条、详情区不等大卡片、「结果」深色卡），配色取自 v8 原版 Bento。截图见 `demo/screenshots/v10-精致Bento.jpg`（全屏）和 `v10-精致Bento-半屏.jpg`（AI 工具右半屏宽度）。其余风格已归档到 `demo/variants/archive/`，以后都在 v10 上改。

## 协作约定

- 分支策略：`main` 用于稳定发布，`dev` 用于日常开发与记录开发日志 / TODO。
- 改了 `skill/` 下的任何东西，提交前把 `skill/VERSION` 的版本号加一（复制安装的用户靠它发现新版本）。
- 原始思考与设计文档见 `docs/PRD.md`、`docs/architecture.md` 和 `docs/notes/`。

## 开源协议

本项目采用 **[GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE)** 开源：个人可自由使用与修改；若对外分发修改版本或架设为网络服务，须以同一协议开源全部修改源码并保留原作者版权声明。

---

## 开发日志（dev）

- **2026-11-18 · v0.3.4**
  - 选择性合入 `skill/ui-fix-and-wordcount`：清理 `.card::before` 遗留阴影 Halo、补充重命名框中文输入法（`keyCode === 229`）防误触、`05-整篇文档.md` 增加硬卡字数（`±5%`）校验指引、`07-导出PDF.md` 补充简历生成前用途确认与纯文本兜底。
- **2026-11-18 · v0.3.3**
  - **多模态作品集分层存储与语义索引**：新增 `skill/scripts/works.py`（`attach` 按 5 MB 阈值自动 `copy` / `link` 并记录 `sha256`、`relink` 基于 Spotlight 找回断链、`audit` 盘点库内体积与摘要覆盖率）。
  - **大视频流式播放与 HTTP Range**：升级 `skill/scripts/serve.py`，支持 `206 Partial Content` 分片流式读取，大视频可顺滑拖拽进度条且不再整文件读入内存。
  - **前端检索与摘要展示**：`skill/app/index.html` 支持在顶部搜索框直接检索 `works[].summary` 与文件名，并在作品卡片下展示轻量摘要。
  - 更新 `skill/references/data-format.md`、`skill/recipes/02-入库.md` 与 `README.md`。
- **2026-11-18 · v0.3.1 – v0.3.2**
  - 新增 `LICENSE`（GNU AGPL-3.0）与 `fill_html.py` + `templates/html/resume.html` 零依赖 HTML A4 打印版简历（前端新增 `/resume-print` 入口与字数统计）。
  - 强化 `check_update.py` 离线/受限网络超时与冷却保护，清理前端「个人概况」卡片与角标视觉细节。
- **2026-11-18 · v0.3.0**
  - 新增 Google Antigravity 专属适配（`skill/adapters/antigravity/README.md`），补充沙箱权限、回环探测授权、`browser` subagent 打开方式与 AI 一句话自安装引导。
  - `serve.py` 自检请求显式绕过系统代理（`ProxyHandler({})`），并新增白名单二进制上传接口 `PUT /vault/assets/portrait.*`。
  - 参照 `sqs-resume` 风格升级 `skill/templates/latex/resume.tex` 与 `fill_tex.py`：支持灰底黑条分节栏、可选右上角证件照、教育背景、`location` 与多版本「技能」卡片。
  - 前端 `skill/app/index.html` 在时间线底部新增置底「个人信息」卡片与右侧 Bento 详情页（支持内联编辑与证件照拖拽/点击上传）。

## TODO

- [x] `serve.py` 支持 HTTP Range 请求，实现右半屏本地视频拖动进度条（PRD 需求 C3）。
- [ ] Codex 适配实测与状态更新（`skill/adapters/codex/README.md`）。
- [ ] 真实素材连续试用一个月（入库 → 申请 → 回存），打磨标签归纳与默认版本召回体验。
- [ ] 探索用户自定义前端视图/小插件的打包与去中心化分享格式（PRD 需求 D5）。
