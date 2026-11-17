# 适配：WorkBuddy（腾讯）

WorkBuddy 原生支持 SKILL.md 格式（带 YAML frontmatter 的 `name` / `description`），
所以本 skill 不用改一个字就能用。按下面做即可。

## 安装

WorkBuddy 的用户级 skills 目录是 `~/.workbuddy/skills/`，把本 skill 目录放进去、目录名用 `jingliku`：

```bash
cp -R "/path/to/Sqs经历库/skill" "$HOME/.workbuddy/skills/jingliku"
```

- 只装到某个项目：放到 `<项目>/.workbuddy/skills/jingliku`（项目级）。
- **推荐用复制，不要用软链（`ln -s`）。** WorkBuddy 的 skill 发现机制对软链目录的支持未经确认；
  复制最稳。代价是源目录更新后要重新复制一次；如果确实想用软链随改随生效，自己验证一次能否被识别即可。
- 装好后**新开一个会话**，WorkBuddy 会在可用技能里列出 `jingliku`，之后用自然语言提到「记经历 / 写简历 /
  自荐信 / 导出 PDF」就会自动触发。想当场用又不想重开会话，就把本文件所在目录的 `SKILL.md` 路径发给它，
  让它先读一遍。

> 环境要求：`python3` ≥ 3.9 即可，脚本全部只用标准库，无需 pip 安装。

## 两个路径（先弄清楚）

- **`<SKILL>`** = 安装后的绝对路径，用户级就是 `<HOME>/.workbuddy/skills/jingliku`（`<HOME>` 如 `/Users/你的用户名`）。
- **`<VAULT>`** = 数据目录，默认 `~/经历库`。

⚠️ **WorkBuddy 最容易踩的坑：路径里的 `~`。**
SKILL.md 里所有命令都用英文双引号包路径，而 `~` 在双引号里**不会展开**。
写 `"~/.workbuddy/skills/jingliku/scripts/serve.py"` 会报 `No such file or directory`。
二选一，别用第一种：

```bash
# ✗ 错：双引号里的 ~ 不展开
python3 "~/.workbuddy/skills/jingliku/scripts/serve.py" --vault "~/经历库" --ensure

# ✓ 对：用 $HOME（在双引号里会展开）
python3 "$HOME/.workbuddy/skills/jingliku/scripts/serve.py" --vault "$HOME/经历库" --ensure

# ✓ 对：直接写完整绝对路径，最省事、最不容易错
python3 "/Users/你的用户名/.workbuddy/skills/jingliku/scripts/serve.py" --vault "/Users/你的用户名/经历库" --ensure
```

同理，`<VAULT>` 也别写 `"~/经历库"`，用 `"$HOME/经历库"` 或完整路径。
这不是 WorkBuddy 独有的坑，但因为它把 skill 装在 `~` 底下，命中率特别高。

## 在右半屏（结果区）打开网页

WorkBuddy 有内置浏览器预览面板，能打开 `localhost`，体验跟 Claude Code 桌面版一样：

- **AI 自己启动：** 按 SKILL.md 铁律第 1 条运行
  `python3 "$HOME/.workbuddy/skills/jingliku/scripts/serve.py" --vault "$HOME/经历库" --ensure`，
  拿到 `RUNNING` / `STARTED http://127.0.0.1:XXXX/` 后，用预览/打开网页的能力打开这个地址，
  就会显示在右半屏的结果区。
- **固定配置：** 不想每次都启动，可以让 AI 记住上面这条命令，每次会话开头先跑一遍（它很快，已在运行时什么都不改）。
- 地址端口可能不是 8765（被占用时自动顺延），以 `--ensure` 打印的为准，或 `cat "$HOME/经历库/.runtime.json"` 看 `url`。

**别用 `file://` 直接打开 `app/index.html`**：那样只会看到「演示数据 · 不会保存」的静态版，改动存不下来。
一律走 `serve.py` 的 `http://127.0.0.1:XXXX/` 地址。

## WorkBuddy 上验证过的行为

- 复制到 `~/.workbuddy/skills/jingliku` 后，新会话的可用技能列表里能看到 `jingliku`，frontmatter 的
  `description` 会被用来判断是否触发。
- `--ensure` 启动的后台服务能跨命令存活（用 `lsof -ti:<端口>` 可查到进程），不会随某条命令结束而被关掉。
  万一被关了，按铁律第 1 条再跑一次 `--ensure`，网页几秒内自动重连。
- 右半屏能实时读写数据目录里的 JSON；AI 改文件前**一定要重新读一遍**（铁律第 3 条），
  否则会覆盖用户刚在网页上改的内容。

## 实测：在 WorkBuddy 里启动并在内置浏览器打开（2026-11-17）

按 SKILL.md 跑 `serve.py --ensure`，再用 WorkBuddy 的预览面板打开它打印的地址。实测结果：

- 数据目录已存在时，`--ensure` 可能直接返回 `RUNNING http://127.0.0.1:8765/`（复用已在跑的服务，不重启）。
- 页面 HTTP 200，标题「经历库」，`<meta name="jingliku-token">` 已注入 → 页面能读写。
- 预览面板能打开 `localhost` 地址，这和 Claude Code 桌面版一致。

过程中踩到 / 排查过的坑：

**坑 1：Host 头必须带端口，否则 403 白屏（最容易踩）。**
`serve.py` 只接受 `Host: 127.0.0.1:PORT` 或 `localhost:PORT`。实测：

| Host 头 | 结果 |
|---|---|
| `127.0.0.1:8765` / `localhost:8765` | 200 |
| `127.0.0.1` / `localhost`（不带端口）、其它域名 | 403 `{"error":"bad host"}` |

所以一定用 `--ensure` 打印的**完整**地址 `http://127.0.0.1:XXXX/` 打开。
如果预览面板里出现 `{"error":"bad host"}` 或空白，八成是地址被改写/丢了端口，用完整地址重开即可。
端口也可能不是 8765（被占会顺延），以打印值为准或看 `<VAULT>/.runtime.json` 的 `url`。

**坑 2：能看 ≠ 能存。**
写入（PUT/DELETE）除 token 外还校验 `Origin` 必须是 `http://127.0.0.1:PORT` / `http://localhost:PORT` 或缺失。
页面打得开但保存报 `{"error":"bad token"}`，就看浏览器控制台里 PUT 的 `Origin` 和 `X-Token`。

**坑 3：日志里的 `BrokenPipeError` 可忽略（源版已修）。**
预览面板或探测请求提前断开连接时，旧版 `serve.py` 会刷一段 traceback，但不影响服务。
源目录的 `serve.py` 已在 `send()` 里捕获 `BrokenPipeError` / `ConnectionResetError`；如果你装到的是修复前的版本，
日志里看到这段 traceback 不必紧张。日志在 `<VAULT>/.serve.log`，排查用 `tail -30`。

**坑 4：`--ensure` 复用的是"当前已在跑的那个服务"。**
它按 `<VAULT>/.runtime.json` 里的地址判断；若之前从别的位置（比如源目录）启动过，跑的就是那份代码。
改了安装副本想让新代码生效，先停掉旧进程（`lsof -ti:8765` 拿 PID 再 `kill`），再跑一次 `--ensure`。

## 装完自检（可选）

```bash
python3 --version   # 需要 3.9+
ls "$HOME/.workbuddy/skills/jingliku/SKILL.md" && echo INSTALLED
python3 -m json.tool "$HOME/经历库/config.json" > /dev/null && echo VAULT_OK
```

数据目录还不存在时，按 `<SKILL>/recipes/01-启动.md` 第 2 步初始化（空库或带示例数据）。
其余功能（入库、挂作品、申请写作、改删、导出 PDF）完全按 SKILL.md 的任务表走，无需 WorkBuddy 专属适配。
