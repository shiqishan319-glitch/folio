# 适配：DeepSeek Harness（DSH，桌面版 / CLI）

DSH 原生认 SKILL.md 格式（YAML frontmatter 里的 `name` / `description`），**本 skill 一个字都不用改**。
DSH 只要求 skill 是「根目录下一层的目录 + `SKILL.md`」，`recipes/`、`app/`、`templates/`、`examples/`
这些子目录原样跟着走；`evals/`、`adapters/` 会被忽略，不影响加载。

## 安装

DSH 会按下面的优先级扫描 skill 根（前面的先命中，同名会被高优先级遮住）：

| 优先级 | 来源 | 位置 |
|---|---|---|
| 100 | 项目级（DSH） | `<项目根>/.dsh/skills` |
| 200 | 项目级（通用） | `<项目根>/.agents/skills` |
| 300 | 自定义 | 配置项 `customSkillDirs` |
| 400 | 用户级（DSH） | `$DSH_HOME/skills`，默认 `~/.dsh/skills` |
| 500 | 用户级（通用） | `~/.agents/skills` |

项目根 = 最近的含 `.git` 的祖先目录。几条硬规则，照着做就不会白装：

- **只认根目录下一层**：`~/.agents/skills/jingliku/SKILL.md` 能被发现；
  `~/.agents/skills/x/jingliku/SKILL.md`（多套了一层）**不会**被发现。
- 也支持平铺的 `<name>.md`，但本 skill 带 `scripts/`、`app/` 等子目录，**必须用目录形态**。
- `~/.agents/skills` 通常已经在用（别的工具也读它，比如 WorkBuddy 之外的一堆 CLI）；
  `~/.dsh/skills` 可能还不存在，不存在就先 `mkdir -p`。

推荐装用户级，并**用软链接**——`git pull` 之后自动生效，不用重装：

```bash
# 0. 先看目标是否已被占用。输出 CANT_INSTALL 就先处理掉旧的，别直接覆盖
test -e "$HOME/.agents/skills/jingliku" -a ! -L "$HOME/.agents/skills/jingliku" && echo CANT_INSTALL || echo OK

# 1. 建根目录（已存在就跳过）
mkdir -p "$HOME/.agents/skills"

# 2. 软链接（-n 保证重复执行不会套娃）
ln -sfn "/path/to/Sqs经历库/skill" "$HOME/.agents/skills/jingliku"
```

- 只给某个项目用：把第 2 步的目标换成 `<项目根>/.dsh/skills/jingliku`。
- 想装 DSH 专属的用户级目录：换成 `$HOME/.dsh/skills/jingliku`，发现效果一样。
- **更新 skill**：`cd /path/to/Sqs经历库 && git pull`，软链接自动指向新内容，不用重装。

### ⚠️ 头号坑：DSH 的文件沙箱

DSH 的文件策略默认是 `workspace-write`：**只允许写当前会话的工作区**。
`~/.agents/skills`、`~/经历库` 都在工作区外，所以 `ln -s`、改 JSON、往 `.trash/` 移文件会被**直接拒绝**：

```
ln: /Users/you/.agents/skills/jingliku: Operation not permitted
[sandbox: file access denied under workspace-write mode]
```

这不是文件权限问题（`chmod`、`sudo` 都没用），是策略问题。三条出路，任选一条：

1. **让 Agent 申请一次授权。** DSH 会弹审批，选允许即可；授权只对那一条命令生效，下一次还要再点。
   无人值守的场景会 fail closed（直接失败），所以得有人在电脑前。
2. **自己开终端装。** 上面那两条 `ln` 命令在系统终端里跑，没有沙箱，一步到位。
3. **把数据目录放进工作区。** 安装用上面第 2 条，运行期把 `--vault` 指到工作区里的路径
   （例如 `<工作区>/经历库`），之后读写经历、挂作品都不再需要授权。

> 怎么选：**日常写经历、改卡片、挂作品全是写 `<VAULT>` 的操作**，vault 在 `~/经历库` 的话，
> DSH 每次都要审批一次，很烦。已有历史数据在 `~/经历库` 的，用第 1 或第 2 条并接受审批；
> 新用户直接按第 3 条把 vault 建在工作区里最省心。**不要替用户改 DSH 的安全策略**，要改让他自己改。

### 安装后验证

```bash
# 软链接指向对不对
ls -l "$HOME/.agents/skills/jingliku/SKILL.md"

# frontmatter 能读到（DSH 只强制要求 name + description 两行）
head -3 "$HOME/.agents/skills/jingliku/SKILL.md"
```

DSH 会**热加载** skill 目录：装完不用重启，**当前会话**的下一条消息里 `jingliku` 就出现在可用技能列表里
（已实测）。万一没看到，新开一个会话。

## 两个路径（先弄清楚）

- **`<SKILL>`** = 安装后的绝对路径，用户级就是 `$HOME/.agents/skills/jingliku`。
- **`<VAULT>`** = 数据目录，默认 `$HOME/经历库`（用户指定了就用用户的）。

`~` 在英文双引号里不展开——这个坑 DSH 上命中率特别高，因为 skill 本身就装在 `~` 底下：

```bash
# ✗ 错：双引号里的 ~ 不展开，报 No such file or directory
python3 "~/.agents/skills/jingliku/scripts/serve.py" --vault "~/经历库" --ensure

# ✓ 对：用 $HOME（双引号里会展开）
python3 "$HOME/.agents/skills/jingliku/scripts/serve.py" --vault "$HOME/经历库" --ensure

# ✓ 更稳：直接写完整绝对路径
python3 "/Users/你的用户名/.agents/skills/jingliku/scripts/serve.py" --vault "/Users/你的用户名/经历库" --ensure
```

## 在右半屏打开前端

DSH 桌面版的右侧栏有一个 **Browser 标签页**（非桌面端默认关闭），能打开 `http(s)` 和 `localhost`：

- **AI 自己启动：** 按 SKILL.md 铁律第 1 条运行 `serve.py --ensure`，拿到 `STARTED http://127.0.0.1:XXXX/`。
- **打开方式：** 在右侧栏开一个 Browser 标签页，把地址粘进去；栏宽拖到约半屏，就是「右半屏」。
- **没有 Browser 标签页 / CLI 版：** 把地址交给用户，让他在系统浏览器里打开，窗口放屏幕右边。
- **侧边栏的文件预览（Document）标签页不行**：它只渲染静态文件，`localhost` 的页面要走 Browser 标签页。

**别用 `file://` 打开 `app/index.html`**：那样只会显示「演示数据 · 不会保存」的静态版，改动存不下来。
一律走 `serve.py` 打印的 `http://127.0.0.1:XXXX/` 地址（端口被占时会顺延，以打印的为准，
也可以 `cat "$HOME/经历库/.runtime.json"` 看 `url`）。

DSH 没有 `.claude/launch.json` 那种固定预览配置，也不需要：每次会话开头跑一遍 `serve.py --ensure` 就够，
已经在运行时它什么都不改。

## 和 Claude Code 的差异

| | Claude Code | DSH |
|---|---|---|
| 安装单位 | 目录（可软链） | 目录（可软链） |
| 用户级位置 | `~/.claude/skills/jingliku` | `~/.agents/skills/jingliku`（或 `~/.dsh/skills/jingliku`） |
| 生效方式 | 新会话 / 重启 | 热加载，装完当场生效 |
| 固定预览配置 | `.claude/launch.json` | 无，靠 `serve.py --ensure` |
| 右半屏 | 内置浏览器（预览面板） | 右侧栏 Browser 标签页 |
| 写工作区外文件 | 直接可写 | `workspace-write` 沙箱，要审批或自己开终端 |

## 在 DSH 上实测过的行为

- 软链接装到 `~/.agents/skills/jingliku` 后，**当前会话当场**就出现了 `jingliku`（无需重启）。
- 沙箱确实拦：`ln -s` 到 `~` 下报 `Operation not permitted` + `[sandbox: file access denied under workspace-write mode]`。
- `--vault` 指向**工作区内**的临时目录时全链路通、**不需要任何审批**：
  `--ensure` 输出 `STARTED`；`GET /` 200（写入口令已注入页面）；`GET /vault/experiences/` 200；
  带 `X-Token` 的 `PUT /vault/experiences/x.json` 200，且 `python3 -m json.tool` 校验通过。
- `--ensure` 起的后台服务能跨命令存活；被关掉时再跑一次 `--ensure`，网页几秒内自动重连。
- `python3` 3.13.5、`xelatex` / `latexmk` 都在时，导出 PDF 的链路可用（TeX 需用户自备）。

## 装完自检

```bash
python3 --version                                   # 需要 3.9+
test -f "$HOME/.agents/skills/jingliku/SKILL.md" && echo INSTALLED
python3 -m json.tool "$HOME/经历库/config.json" > /dev/null && echo VAULT_OK
```

`VAULT_OK` 没出来就按 `<SKILL>/recipes/01-启动.md` 第 2 步初始化数据目录（空库或带示例数据）。
其余功能（入库、挂作品、申请写作、改删、导出 PDF）完全按 SKILL.md 的任务表走，无需 DSH 专属适配。
