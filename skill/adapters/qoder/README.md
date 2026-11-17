# 适配：Qoder（桌面版 / CLI）

## 安装

Qoder 的本地 Skill 安装入口只接受压缩包（`.zip` / `.skill`），不能直接选文件夹。所以先打包，再安装。

### 第 1 步：打包

```bash
python3 "/path/to/Sqs经历库/skill/adapters/qoder/pack.py"
```

它会生成 `jingliku.skill` 并打印绝对路径（默认在系统临时目录）。这个脚本顺手处理了三个坑：

| 坑 | 现象 | 脚本怎么处理 |
|---|---|---|
| frontmatter 不是合法 YAML | 安装报 `EXTENSION_SKILL_FRONTMATTER_INVALID` | 打包前先校验；`description` 含 `: ` 却没加引号时直接报错并提示改法 |
| 中文文件名编码 | 用 macOS 自带 `zip` 打包，中文名变成 `????` | 用 Python `zipfile`，文件名按 UTF-8 写入 |
| `._` 资源分叉文件 | 用 `ditto` 打包会多出一堆 `._*` | 跳过 `.DS_Store`、`._*`、`__MACOSX` |

> 为什么踩坑：Qoder 安装器会严格解析 `SKILL.md` 的 frontmatter。`description` 里只要出现英文冒号加空格（例如 `vault: logging`），YAML 就非法了。**最省事的规则：description 整段用双引号包起来。**

### 第 2 步：安装

二选一：

- **在 Qoder 里装：** 打开 Skill 安装入口（上传本地 Skill），选第 1 步生成的 `.skill` 文件。
- **让 Agent 装：** 直接说「安装这个本地 skill：<脚本打印的完整路径>」。

安装位置是用户级的 `~/.qoder/skills/jingliku`，不写进项目。装完通常立刻出现在技能列表；没看到就新开一个会话。

**同名冲突：** 安装器默认拒绝覆盖。更新时在安装界面明确选择覆盖/更新；如果同名 Skill 来自市场或链接目录，先处理原来源再装，不要靠删目录绕过。

**更新：** 安装是复制一份快照到 `~/.qoder/skills/jingliku`，不是链接源目录。之后在源目录改的东西（包括这份文档）不会自动同步，要重新跑 `pack.py` 再覆盖安装。安装前先用第 3 步确认旧版在不在。

### 第 3 步：验证

```bash
test -f ~/.qoder/skills/jingliku/SKILL.md && echo INSTALLED
```

## 两个路径（先弄清楚）

- **`<SKILL>`** = 安装后的绝对路径，用户级是 `$HOME/.qoder/skills/jingliku`。
- **`<VAULT>`** = 数据目录，默认 `$HOME/经历库`。

SKILL.md 里的命令都用英文双引号包路径，但双引号里的 `~` 不会展开。写 `"~/.qoder/..."` 会报 `No such file or directory`，改用 `"$HOME/..."` 或完整绝对路径：

```bash
# ✗ 双引号里的 ~ 不展开
python3 "~/.qoder/skills/jingliku/scripts/serve.py" --vault "~/经历库" --ensure

# ✓ 用 $HOME（在双引号里会展开）
python3 "$HOME/.qoder/skills/jingliku/scripts/serve.py" --vault "$HOME/经历库" --ensure
```

## 在右半屏打开前端

Qoder 桌面版自带浏览器能力（Agent 侧是 browser-use 工具），可以让它打开 `localhost`：

- **AI 自己启动：** 按 SKILL.md 在后台运行 `serve.py --ensure`，然后打开它打印的地址。
- **打开方式：** 用 Qoder 内置浏览器（Agent 侧是 browser-use 工具）打开，实测不会拉起外部浏览器。
- **Agent 的具体做法（已验证）：** `list_pages` 为空时，直接 `navigate_page` 到 `http://127.0.0.1:XXXX/` 就会新开内置浏览器预览页；再用 `take_screenshot` 确认渲染结果。不需要在 Qoder 里提前建预览配置。

Qoder 没有 `.claude/launch.json` 那种固定预览配置，不需要额外配置：每次会话让 Agent 跑一遍 `serve.py --ensure` 就够，它已经在运行时不会重启。

CLI 版一般没有内置浏览器，把地址交给用户，让他在自己的浏览器里打开。

## Qoder 上实测过的行为（2026-11-17）

- **安装：** `.skill` 安装后立即出现在技能列表，当前会话即可用；位置是 `~/.qoder/skills/jingliku`。
- **启动：** `serve.py --ensure` 在服务已运行时输出 `RUNNING http://127.0.0.1:8765/`，复用原服务，不会重启；端口以 `.runtime.json` 为准。
- **打开：** 用 browser-use 的 `navigate_page` 打开后，页面直接出现在 Qoder 内置浏览器里，未拉起外部浏览器。
- **渲染：** 无 console 报错；前端每几秒轮询 `/vault/experiences/` 和 `/vault/applications/`，均返回 200，属正常。
- **半屏：** 内置浏览器按面板宽度自适应；想要半屏效果把预览面板拖窄即可（页面本身支持两栏→单栏）。
- **快照：** 安装的是副本；源目录后续改动（包括新增 adapters）不会同步到 `~/.qoder/skills`。

## 和 Claude Code 的差异

| | Claude Code | Qoder |
|---|---|---|
| 安装单位 | 目录（可软链） | 压缩包（`.skill` / `.zip`） |
| 安装位置 | `~/.claude/skills/jingliku` | `~/.qoder/skills/jingliku` |
| 更新方式 | 改源目录即生效（软链） | 重新打包 + 覆盖安装 |
| 固定预览配置 | `.claude/launch.json` | 无，靠 `serve.py --ensure` |

## 打包脚本维护提示

`pack.py` 只依赖 Python 标准库，默认把顶层目录命名为 frontmatter 里的 `name`（当前是 `jingliku`）。改 `SKILL.md` 的 `name` 后不用改脚本；但名字要符合小写字母/数字/连字符的规则，否则脚本会报错。
