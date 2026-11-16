# 经历库数据格式（schema 1）

数据目录 `$VAULT`（默认 `~/经历库`）：

```
config.json                 配置：经历类型、个人信息
experiences/<id>.json       一段经历一个文件
applications/<id>.json      一份申请记录（整篇文档）一个文件
assets/<卡片id>/<文件名>     作品的快捷方式（软链接），指向原文件
.trash/                     删除的文件移到这里
.runtime.json               serve.py 写的运行信息（地址），不要手动改
.token                      serve.py 的写入口令（重启后沿用，已打开的页面才能继续保存），不要改、不要外传
```

`id` 只用字母、数字、`-`、`_`，最长 64 个字符，同时是文件名。

## config.json

```json
{
  "schema": 1,
  "types": ["实习", "项目", "志愿者", "获奖", "思考"],
  "resume_types": ["实习", "项目", "志愿者", "获奖"],
  "profile": {
    "name": "姓名",
    "headline": "专业 · 年级",
    "email": "",
    "phone": "",
    "links": []
  }
}
```

- `types`：经历类型，前端左栏按这个顺序显示。用户可以增删。
- `resume_types`：导出简历时包含哪些类型，可省略（默认除「思考」外全部）。
- `profile`：只用于导出简历和落款，可省略。

## experiences/<id>.json：一段经历

```json
{
  "schema": 1,
  "id": "xhs",
  "type": "实习",
  "org": "小红书",
  "title": "小红书 · 内容运营实习",
  "time": "2025.06 – 2025.09",
  "year": 2025,
  "role": "运营实习生",
  "tags": ["实习相关", "内容"],
  "fact": "负责一个垂类话题的选题与数据复盘，每周输出选题建议。",
  "result": "负责话题的周均互动量提升约 30%。",
  "thought": "真正有用的选题来自创作者自己的历史数据，而不是模仿别人的爆款。",
  "works": [
    "周报截图 ×3",
    {"label": "选题复盘文档", "kind": "link", "url": "https://example.com/doc"},
    {"label": "复盘汇报.pptx", "kind": "slides", "asset": "xhs/复盘汇报.pptx",
     "mode": "link", "original": "/Users/me/Documents/复盘汇报.pptx",
     "size": 2483912, "mtime": 1757212800}
  ],
  "writings": [
    {"type": "简历条目", "versions": [
      {"name": "v1 通用", "text": "负责垂类话题选题与数据复盘……"},
      {"name": "v2 偏数据", "text": "搭建话题数据复盘表……"}
    ]},
    {"type": "网申短描述", "versions": [
      {"name": "v1 100 字", "text": "在小红书做内容运营实习时……"}
    ]}
  ],
  "created": "2026-11-16T10:00:00+08:00",
  "updated": "2026-11-16T10:00:00+08:00"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 是 | 和文件名一致 |
| `type` | 是 | 必须是 `config.json` 里 `types` 之一 |
| `title` | 是 | 卡片标题，常用「机构 · 角色/事情」 |
| `org`, `role`, `time` | 否 | `time` 用 `YYYY.MM – YYYY.MM` 或 `YYYY.MM` |
| `year` | 否 | 数字，时间线按它分组（取开始年份） |
| `tags` | 否 | 字符串数组，用于筛选 |
| `fact` / `result` / `thought` | 否 | 四类信息中的三类，空着就写 `""` |
| `works` | 否 | 作品，见下 |
| `writings` | 否 | 写法，按类型分组，每类可以有多个带名字的版本 |
| `created` / `updated` | 否 | ISO 时间；改动后更新 `updated` |

### works 里的一项

可以是一个字符串（只有名字），也可以是对象：

| 字段 | 说明 |
|---|---|
| `label` | 显示名（必填） |
| `kind` | `image` / `video` / `pdf` / `slides` / `document` / `archive` / `folder` / `link` / `file` |
| `url` | 网页链接（`kind: link` 时） |
| `asset` | 快捷方式在 `assets/` 下的相对路径，即 `<卡片id>/<文件名>`；前端通过 `/vault/assets/<asset>` 打开 |
| `mode` | `link`（软链接，默认）或 `copy`（复制进来） |
| `original` | 原文件绝对路径 |
| `size`, `mtime` | 挂载时原文件的大小（字节）和修改时间（秒），用来发现文件被移动或改动 |

## applications/<id>.json：申请记录

```json
{
  "schema": 1,
  "id": "d1",
  "title": "某乡村支教志愿项目 · 自荐信",
  "kind": "自荐信",
  "target": "某乡村支教志愿项目",
  "scene": "志愿项目",
  "date": "2026.11",
  "lang": "中文",
  "paras": [
    {"text": "尊敬的项目负责人：……", "card": null},
    {"text": "我有面向儿童讲解的经验……", "card": "museum"}
  ],
  "created": "2026-11-16T10:00:00+08:00",
  "updated": "2026-11-16T10:00:00+08:00"
}
```

- 整篇存，不拆。`paras` 按顺序排列，每段的 `card` 是它用到的经历 `id`，没有就填 `null`。
- `kind`、`target`、`scene`、`date`、`lang` 是打标维度，用来检索和复用。

## 前端怎么读写

前端通过 `serve.py` 访问数据目录：

- `GET /vault/experiences/`：列出文件（含 `mtime`），前端靠轮询它发现变化并自动刷新。
- `GET /vault/experiences/<id>.json`：读一张卡片。
- `PUT /vault/experiences/<id>.json`：写入（需要页面里的口令）。
- `DELETE /vault/experiences/<id>.json`：移到 `.trash/`。

所以 AI 直接改文件、前端通过管子改文件，两边看到的是同一份数据。
