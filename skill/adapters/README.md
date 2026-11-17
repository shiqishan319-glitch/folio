# 适配索引：不同 AI 工具怎么装这个 skill

本目录每个子目录对应一个 AI 工具（harness），里面是**那个工具专属**的安装步骤和坑。
装之前先看这张表找到你的工具，再去对应的 README；表里没有就按「通用」那一节装。

| 工具 | 用户级安装位置 | 安装方式 | 右半屏前端 | 详细 |
|---|---|---|---|---|
| Claude Code（桌面版 / CLI） | `~/.claude/skills/jingliku` | 软链接 | 内置浏览器（预览面板） | [`claude-code/README.md`](claude-code/README.md) |
| Codex | `~/.codex/AGENTS.md` 里加一段引用 | 写指引（待验证） | 无内置，给地址 | [`codex/README.md`](codex/README.md) |
| Qoder（桌面版 / CLI） | `~/.qoder/skills/jingliku` | 打包成 `.skill` 再安装 | 内置浏览器 / browser-use | [`qoder/README.md`](qoder/README.md) |
| WorkBuddy（腾讯） | `~/.workbuddy/skills/jingliku` | 复制 | 内置预览面板 | [`workbuddy/README.md`](workbuddy/README.md) |
| DeepSeek Harness（DSH） | `~/.agents/skills/jingliku`（或 `~/.dsh/skills/jingliku`） | 软链接 | 右侧栏 Browser 标签页 | [`dsh/README.md`](dsh/README.md) |

## 通用做法（表里没有你的工具时）

1. 把 `skill/` 目录放到这个工具扫描 skills 的位置，**目录名用 `jingliku`**；
   如果它不扫 skills 目录，就把 `SKILL.md` 的绝对路径写进它的规则文件（`AGENTS.md` / `CLAUDE.md` 之类）。
2. 确认它能读到 `SKILL.md` 开头的 YAML frontmatter（`name` + `description`）。
3. 右半屏：工具有内置浏览器就打开 `serve.py --ensure` 打印的 `http://127.0.0.1:XXXX/`；
   没有就把地址交给用户，让他在自己的浏览器里打开。

## 怎么更新

每次会话开始时，AI 会运行 `scripts/check_update.py`（启动菜谱第 1.5 步）检查 GitHub 上有没有新版本，有就问用户要不要更新。能不能自动更新，取决于安装方式：

| 安装方式 | 工具 | 更新 |
|---|---|---|
| 软链接到 git 仓库 | Claude Code、DSH | 自动：`check_update.py --apply`（等于 `git pull --ff-only`），然后 `serve.py --restart` |
| 复制一份 | WorkBuddy、豆包、Qoder | 只能提示：按对应 README 重新复制 / 打包安装 |

复制安装靠比对 `skill/VERSION` 判断新旧，所以**维护者每次改了 skill，都要把 `VERSION` 的版本号加一**。仓库是私有的时候，复制安装读不到 GitHub 上的版本号，会安静地跳过检查。

## 加一个新工具

复制一个最接近的子目录，改名成工具名，按「安装 / 两个路径 / 在右半屏打开前端 / 和 Claude Code 的差异 /
实测过的行为」写；然后在上表加一行。**没实测过的行为要标「待验证」**，别写成已验证。
