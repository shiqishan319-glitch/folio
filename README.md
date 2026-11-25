# 经历库

一个住在本地、由 AI 维护的个人经历数据库。每段经历只存一份；申请时按场景检索，生成对应的写法；生成结果存回库里，下次直接复用。

> 当前版本：**`v0.3.12`**（v10 精致 Bento 前端 + **简历**：按岗位做简历、右半屏直接改的简历编辑器、导入旧简历 + 申请信与简历的 LaTeX / 网页打印版 PDF + 多模态作品集分层存储（视频可让 AI 看懂写摘要）+ 个人主页一键生成 + 用户自定义前端（`custom.css` / `custom.js`）+ 首次打开分区引导 + 已适配 7 款主流 AI 工具）。

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
- **数据和产品都在本地**：所有数据存在 `~/folio/`，不收集用户数据。换 AI 工具只需挂载 Skill，数据不用搬家。
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

AI 会按你正在用的工具找到对应的安装说明，完成安装、确认数据目录（默认 `~/folio`），并在右半屏打开经历库页面。

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
│   ├── resume-design.md      简历功能设计（分工、数据格式、前端交互；第九节问题已定）
│   └── notes/
│       └── 2026-11-11-思考.md  原始头脑风暴笔记
├── skill/                    经历库 Skill 包（装进 Claude Code / Codex / Qoder / WorkBuddy / DSH 等）
│   ├── SKILL.md              给 AI 的全部 know-how
│   ├── references/data-format.md  数据格式
│   ├── app/index.html        前端（v10）
│   ├── VERSION               版本号（改了 skill 就加一）
│   ├── scripts/serve.py      本地细管子（Python 标准库）
│   ├── scripts/check_update.py  每次会话检查 GitHub 有没有新版本
│   ├── scripts/resume_model.py  简历：LaTeX / 网页打印版共用的排版模型 + 引用检查与快照同步
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
- 改了前端或示例数据后运行 `python3 tools/sync_demo.py`（演示数据和 `demo/index.html` 都由它生成）；改了简历渲染规则后运行 `python3 tools/test_render_parity.py`。
- 原始思考与设计文档见 `docs/PRD.md`、`docs/architecture.md` 和 `docs/notes/`。

## 开源协议

本项目采用 **[GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE)** 开源：个人可自由使用与修改；若对外分发修改版本或架设为网络服务，须以同一协议开源全部修改源码并保留原作者版权声明。

---

## 开发日志（dev）

- **2026-11-25 · v0.3.12**（PRD 远期需求的轻量版）
  - **C4 用户改造前端**：用户的定制放在数据目录的 `custom.css` / `custom.js`，前端启动时自动加载，skill 更新不会覆盖，删掉就复原；`custom.js` 通过很小的 `window.JL`（只读数据 + `afterRender` 钩子 + `toast`）往页面加东西，出错只弹一次提示、页面照常。菜谱 `recipes/12-改造前端.md`。
  - 安全：`serve.py` 给页面加了 CSP，页面只能和本机的 `serve.py` 通信——别人分享来的 `custom.js` 也没法把数据发到外网（实测 `fetch` 和图片请求都被拦截，字体、视频、打印等原有功能不受影响）。
  - **D4 个人主页**：`fill_html.py site` 用和简历同一套数据生成一个单文件 HTML（`templates/html/site.html`，深浅色、手机适配，默认不放电话）；菜谱 `recipes/13-个人主页.md`，提一句可放到 GitHub Pages。
  - **D3 视频**：新菜谱 `recipes/14-理解视频.md`，写成建议性的：好摘要写什么、按工具能力怎么看（能直接看视频就直接看 / 看截图 / 字幕 / 转文字），拿不准再走兜底（`ffmpeg` 9 宫格缩略图 + 取字幕 + 请用户描述）。
  - **菜谱写法：规则必须守，方法可以换。** SKILL.md 把「照着做，不要自由发挥」改成：铁律、数据格式、文件位置、「做完是什么样」必须守；读文件、看图看视频、打开网页这类方法可以用工具的原生能力；拿不准就照菜谱的兜底步骤。入库（02）、导入旧简历（11）按这个思路补了说明；导出 PDF（07）反过来明确「排版方式必须照用」，保证版式一致。
- **2026-11-24 · v0.3.11**
  - **首次打开的分区引导**（参照 SqsAgent 的 GuidedTour）：模态聚光灯 + 说明卡片，逐个介绍左栏类型 / 简历 / 申请信、统计条、经历卡片、个人概况、事实结果思考作品、写法版本、同步状态；简历页另有一套。第一次打开自动走一遍，之后从左栏或时间线标题的「?」再看（「这一页怎么用」/「完整流程」）。看不到的区域自动跳过，`?notour` 跳过自动引导。
  - 简历编辑器：**分节拖拽**（分节标题上的 ⋮⋮）、**刷新后保留撤销历史**（存在本标签页，文件被 AI 改过就自动丢弃）、**对照另一份简历**（如中文版 / 英文版并排，按卡片对齐，只在一边出现的条目标出来，可让 AI 做英文版）。
  - **导入旧简历**：新菜谱 `recipes/11-导入旧简历.md`（读 PDF / Word → 个人信息 → 每段经历一张卡片，原文存为「v1 原简历」→ 一份原样的简历记录）与测试 `skill/evals/import-old-resume`（虚构简历；Haiku 8/8，入库回归 9/9）。
  - `promo/`（本地，不进仓库）：路径改成 `~/folio`，产品截图换成当前界面，过时的行数 / 菜谱数改正，文案补了简历功能，一页 Slide / PPTX / 概念动画重新生成。
- **2026-11-22 · v0.3.10**
  - 简历编辑器：**专注模式**（收起时间线和左栏，半屏时自动进入，纸从约 50% 放大到约 84%）和**缩放切换**（适应宽度 / 100%）；顶栏在窄宽度下固定排成两行。
  - **全局撤销 / 重做**（⌘Z / ⇧⌘Z、顶栏 ↶ ↷），覆盖换版本、覆盖或另存卡片版本、排序、增删、改名等全部简历改动；AI 从外部改了文件时清空历史，避免撤销冲掉 AI 的修改。
  - 「已投递」改回草稿前先确认（推荐改用「复制为新草稿」）；经历详情显示「简历引用 N」并列出用到它的简历，可直接跳转；`#res=<id>` 直接打开某份简历（刷新后保持，改地址栏也会切换）。
  - 新增开发工具 `tools/`：`sync_demo.py` 从 `sample-vault` 生成前端演示数据并同步 demo（`--check` 检查是否过期）；`test_render_parity.py` 对比前端与 `resume_model.py` 的拆行结果。它当场抓到英文小标题「Skills:」在预览里变成全角冒号等几处不一致，已修正，42/42 一致。
  - `demo/screenshots/简历编辑器-*.jpg` 换成真实前端截图。
- **2026-11-22 · v0.3.9**
  - **默认数据目录改成英文路径 `~/folio`**（原来是 `~/经历库`），各工具的命令和沙箱处理英文路径更稳。启动菜谱 `01-启动.md` 会发现旧的 `~/经历库`，问用户后用 `serve.py --stop` + `mv` 搬过去（`~/folio` 已存在时不覆盖）；不想搬的继续用旧路径。
  - `serve.py` 新增 `--stop`（输出 `STOPPED` / `NOT_RUNNING`）；还没建出来的数据文件夹（如旧库里的 `resumes/`）列目录时返回空列表，不再让前端每两秒报一次 404。
  - 所有适配说明、数据格式文档、前端提示里的路径同步改成 `~/folio`。
- **2026-11-22 · v0.3.8**
  - **简历编辑器进了前端**（`skill/app/index.html`）：左栏分成「简历」（`resumes/`）和「申请信」（`applications/`）两组；选中简历时详情区是一张可以直接编辑的 A4 纸：拖时间线卡片进来、拖动或 ⌥↑↓ 排序、换版本（显示字数和「也用在哪份简历」）、双击改字后选择覆盖或另存为卡片新版本、就地改标题 / 求职意向 / 分节名、照片开关、岗位关键词增删与覆盖率、实时「还剩 N 行」与压回一页的建议、草稿 / 已投递切换、复制改投、删除（进 .trash）。
  - 和 AI 协作：AI 在磁盘上改了卡片，草稿简历自动跟着变并刷新快照；AI 改了简历文件，右半屏两秒内更新；在卡片里给版本改名，所有简历的引用自动跟着改。需要判断或改写的事（按 JD 生成、改写一条、压到一页、LaTeX 精排）只放「问 AI」按钮，复制指令给左边对话。
  - 修复：动效引擎的页面标识没有考虑简历，导致简历视图每次渲染都走异步过渡、就地编辑拿不到焦点；`serve.py` 允许删除 `resumes/` 下的文件。
  - 分工写进 `docs/resume-design.md`「分工」一节；`demo/index.html` 同步。
- **2026-11-22 · v0.3.7**
  - **简历功能第 1 步（数据 + AI 流程）**：新增 `resumes/<id>.json`（引用卡片写法版本 + 文字快照；草稿跟随卡片，已投递冻结）与菜谱 `recipes/10-按岗位做简历.md`（选经历 → 选/改写版本 → 存简历 → 导出并检查一页 → 标记已投递）。
  - 新增 `scripts/resume_model.py`：`fill_tex.py` / `fill_html.py` 共用的排版模型；`check` 查断掉的版本引用，`sync [--sent]` 同步快照、标记已投递。两个导出脚本都支持 `--from <简历id>`，`serve.py` 的 `/resume-print?resume=<id>` 同理，`resumes/` 加入可写目录。
  - 网页打印版模板改成和 LaTeX 版同一版式；示例数据加了两份简历（草稿、已投递）；新增测试用例 `skill/evals/resume-for-jd`。
- **2026-11-22 · v0.3.6**
  - 简历功能设计草案 `docs/resume-design.md`（简历存为「引用清单」、草稿跟随卡片 / 已投递冻结、AI 菜谱、前端交互、分三步做），附可点击原型 `demo/resume-editor.html` 与截图。
  - LaTeX 简历模板按 sqs 的简历改版：无衬线、分节标题加粗 + 通栏细线、条目「机构 - 角色」、首行概述不带圆点、教育背景改为不带圆点的标签行；按系统挑有真粗体的黑体（Mac 冬青黑体 → Windows 微软雅黑 → Linux Noto 黑体 → 伪粗体兜底）。
- **2026-11-19 · v0.3.5**
  - `serve.py`：格式不对的 `Range` 头（如 `bytes=abc-`）不再让连接断开、日志刷报错，而是按 HTTP 规范忽略分段、返回整个文件（200）；正常分段仍是 206，越界是 416。
  - `works.py relink`：原文件「改名 + 挪位置」也能找回。按文件名找不到时，再按文件大小找（先 Spotlight，再扫桌面 / 下载 / 文稿 / 影片 / 图片），用 `sha256` 指纹确认，没有指纹时要求修改时间也一致，同样大小的其他文件不会被误认。
  - 前端：半屏下统计条显示完整的「简历」（以前被缩成「简」），三个两位数统计也放得下。
  - 用 Haiku 重跑了 3 个 skill 测试：带 skill 24/24 全过。测试里的海报改为按分层规则判定（≤ 5 MB 复制进库）。
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
- [x] 简历：存成引用清单（`resumes/`）、按岗位做简历（菜谱 10）、右半屏简历编辑器、导入旧简历（菜谱 11）。
- [ ] 发布：把 `dev` 合进 `main`（已安装用户按 `main` 检查更新）。
- [ ] `promo/` 的 84 秒交互演示视频还是旧界面（没有简历），需要按新界面重新录制。
- [x] PRD 远期（轻量版）：C4 改造前端（`custom.css` / `custom.js`）、D3 视频缩略图 + 字幕、D4 个人主页模板。
- [ ] D5 插件分享：目前是「把 `custom.*` 两个文件发给朋友」，还没有打包格式。
- [ ] 探索用户自定义前端视图/小插件的打包与去中心化分享格式（PRD 需求 D5）。
