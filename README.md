# 经历库

一个住在本地、由 AI 维护的个人经历数据库。每段经历只存一份；申请时按场景检索，生成对应的写法；生成结果存回库里，下次直接复用。

> 状态：**产品梳理阶段**（PRD v0.1 + 前端交互 Demo）。执行方案未定。

## 为什么做

申请很频繁（志愿者、评奖评优、网申、面试），每次都要把经历重新归纳一遍。卡住的不是「想不起有哪些经历」，而是三件事：

1. 素材散在备忘录、Word、相册、网盘、聊天记录里；
2. 录入时没人追问，事后补不回数字、难点和思考；
3. 同一段经历有很多种写法，版本散落在各个面试文件里。

经历库把组织单位从「一次申请」换成「一段经历」：一段经历一张卡片，各种写法挂在卡片下。

## 产品形态（当前设想）

```
  左半屏：AI 对话（Claude Code / Codex …）     右半屏：经历库前端
  ┌──────────────────────────────┐   ┌──────────────────────────────┐
  │ Skill：入库、追问、检索、生成、回存 │   │ 浏览、筛选、取用、轻量编辑       │
  └──────────────┬───────────────┘   └──────────────┬───────────────┘
                 └──────────── 同一份本地数据 ────────────┘
```

- **AI 做重活，前端做轻活**：批量入库、追问、检索、生成由 Skill 完成；前端负责浏览和取用。
- **数据和产品都在本地**：不收集用户数据。换 AI 工具只需适配 Skill。
- **只在电脑上维护**：不做手机端。

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

## 接下来

PRD 里列了 10 个待解决问题，前 3 个决定产品形态，要先定：

1. 前端交互方式怎么呈现？
2. 产品住在哪里：AI 工具的右半屏，还是远程网页 + 本地数据？
3. 结构化信息到底分哪几类？（暂定：事实、结果、思考、作品）

详见 [docs/PRD.md](docs/PRD.md#五待解决的问题)。

## 协作约定

- PRD 以本仓库的 `docs/PRD.md` 为准。原稿在飞书（「个人素材库-产品思路」），迁入后改动都在这里做，靠 git 记录历史。
- 讨论用 Issue：一个待解决问题、一条需求或一个 bug 开一个 Issue，标题带编号（如 `[问题2] 产品住在哪里`、`[C1] Demo 接入真实数据`）。
- 改动走分支 + Pull Request，不直接推 `main`。
- 改了 `skill/` 下的任何东西，提交前把 `skill/VERSION` 的版本号加一（复制安装的用户靠它发现新版本）。
- 新的原始想法放 `docs/notes/YYYY-MM-DD-主题.md`，整理成结论后再合进 PRD。
