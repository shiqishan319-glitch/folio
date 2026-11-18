# 适配：Google Antigravity（AGY，桌面版 / IDE / CLI）

Antigravity 原生支持 `SKILL.md` 格式（YAML frontmatter 里的 `name` / `description`），**本 skill 一个字都不用改**。
支持通过软链接（`ln -s`）或 `skills.json` 注册，装好后既能按语义自动触发，也能在输入框里用 `/jingliku` 斜杠命令直接调用。

## 安装

Antigravity 按下面的优先级发现 skills（前面的优先级更高，同名会覆盖后面的）：

| 优先级 | 来源 | 位置 |
|---|---|---|
| 1 | 项目级目录 | `<项目根>/.agents/skills/jingliku`（也认 `.agent/`、`_agents/`、`_agent/`） |
| 2 | 项目级清单 | `<项目根>/.agents/skills.json` |
| 3 | 用户级目录（全局） | `~/.gemini/config/skills/jingliku` |
| 4 | 内置技能 | Antigravity 自带内置 skills |
| 5 | 用户级清单（全局） | `~/.gemini/config/skills.json` |

推荐装到**用户级目录**并**用软链接**——升级时 `git pull` 或自动更新即可生效，不用重装：

```bash
# 0. 先看目标是否已被非软链目录占用。输出 CANT_INSTALL 就先处理旧目录，别直接覆盖
test -e "$HOME/.gemini/config/skills/jingliku" -a ! -L "$HOME/.gemini/config/skills/jingliku" && echo CANT_INSTALL || echo OK

# 1. 建全局 skills 目录（已存在会直接跳过）
mkdir -p "$HOME/.gemini/config/skills"

# 2. 建软链接（-n 保证重复执行不会在目录里套娃）
ln -sfn "/path/to/Sqs经历库/skill" "$HOME/.gemini/config/skills/jingliku"
```

- 只给某个项目用：把目标换成 `<项目根>/.agents/skills/jingliku`。
- 不想建软链、想保留原路径：在 `~/.gemini/config/skills.json` 里注册它的父目录（注意 `entries.path` 是按**下一层子目录**扫描的，所以如果源目录名叫 `skill` 而不是 `jingliku`，仍建议用上面的软链接方式把目录名映射成 `jingliku`）。

### 安装后验证

```bash
ls -l "$HOME/.gemini/config/skills/jingliku/SKILL.md"
head -4 "$HOME/.gemini/config/skills/jingliku/SKILL.md"
```

---

## ⚠️ 实测踩坑与解决（Antigravity 专属）

### 坑 1：直接 `ls ~/.gemini/config/` 会报 `Operation not permitted`

Antigravity 的终端工具（`run_command`）默认跑在 macOS Seatbelt 沙箱里。为了保护 `~/.gemini/config/` 下的其它认证配置，沙箱禁止直接列举 `~/.gemini/config/` 根目录：

```text
ls: /Users/you/.gemini/config/: Operation not permitted
```

**不要误以为 `~/.gemini/config/skills` 不能写。** 实测在沙箱内直接执行：
- `mkdir -p "$HOME/.gemini/config/skills"`
- `ln -sfn "/path/to/Sqs经历库/skill" "$HOME/.gemini/config/skills/jingliku"`
- `ls -la "$HOME/.gemini/config/skills"`

全部**可以直接成功（exit 0）**，不需要绕过沙箱。

### 坑 2：沙箱内运行 `serve.py --ensure` 报 `FAILED to start`

这是启动时最容易踩的坑。在默认沙箱（`BypassSandbox: false`）里运行：

```bash
python3 "$HOME/.gemini/config/skills/jingliku/scripts/serve.py" --vault "$HOME/经历库" --ensure
```

会等待约 10 秒后退出（exit 1），输出：

```text
There were sandbox errors that may or may not be related to the failure...
FAILED to start; read /Users/you/经历库/.serve.log
```

- **原因：** `serve.py --ensure` 需要通过 `urllib.request.urlopen("http://127.0.0.1:PORT/vault/config.json")` 探测本地端口并拉起后台常驻 HTTP 服务，而默认沙箱限制了本地回环 HTTP 探测/系统代理读取。
- **解决（给 Agent）：** 看到上述沙箱报错时，直接用 `BypassSandbox: true` 重新运行同一条 `serve.py --ensure`（或 `--restart`）命令，向用户申请一次执行授权即可。获批后 `serve.py` 会在后台常驻，跨轮次、跨会话存活，后续只读/写 JSON 文件在沙箱内即可正常完成。
- **解决（给用户）：** 批准 Agent 的这一次命令运行请求，或者自己在终端里跑一次 `serve.py --ensure`。

### 坑 3：`check_update.py` 在沙箱里输出 `SKIPPED`

沙箱内无法读取 `~/.ssh/` 下的私钥或访问外网，`check_update.py` 会输出：

```text
SKIPPED cannot reach GitHub: Warning: Identity file /Users/you/.ssh/... not accessible: Operation not permitted.
```

并且返回码为 `0`。这完全符合 `recipes/01-启动.md` 的预期——**不是错误**，不用拿 `BypassSandbox: true` 重试，也不用打扰用户，直接进入第 2 步即可。

### 坑 4：双引号里的 `~` 不会展开

和其它把 skill 装在 `~` 下的工具一样，命令里路径加英文双引号时，不要写 `"~/.gemini/..."` 或 `"~/经历库"`：

```bash
# ✗ 错：双引号里的 ~ 不展开
python3 "~/.gemini/config/skills/jingliku/scripts/serve.py" --vault "~/经历库" --ensure

# ✓ 对：用 $HOME 或完整绝对路径
python3 "$HOME/.gemini/config/skills/jingliku/scripts/serve.py" --vault "$HOME/经历库" --ensure
```

---

## 两个路径（先弄清楚）

- **`<SKILL>`** = 安装后的绝对路径，用户级是 `$HOME/.gemini/config/skills/jingliku`（如 `/Users/你的用户名/.gemini/config/skills/jingliku`）。
- **`<VAULT>`** = 数据目录，默认 `$HOME/经历库`（如 `/Users/你的用户名/经历库`）。

---

## 在右半屏打开前端

Antigravity 桌面版 / IDE 右侧辅助面板（HTML Auxiliary Pane）内置了 Webview 浏览器，由 **`browser` 子 Agent（subagent）** 驱动：

1. **先由主 Agent 启动服务：** 按 `recipes/01-启动.md` 第 3 步运行 `serve.py --ensure`（遇到沙箱拦截时设 `BypassSandbox: true`），拿到 `RUNNING http://127.0.0.1:XXXX/` 或 `STARTED http://127.0.0.1:XXXX/`。
2. **调用 `browser` subagent 打开页面：**
   - 使用 `invoke_subagent` 工具，`TypeName` 传 `"browser"`，`Model` 传 `"flash"`。
   - Prompt 示例：让它打开第 3 步输出的 `http://127.0.0.1:XXXX/`，确认「经历库」页面加载正常（无「连接中断」），并保持页面打开。
3. **不要做的事：**
   - **不要**在 `run_command` 里跑 `open http://127.0.0.1:XXXX/`——那会拉起 macOS 系统外部浏览器，而不是 Antigravity 右侧内置浏览器。
   - **不要**用 `file://` 打开 `app/index.html`——那样只会看到静态演示数据，无法保存修改。
   - 启动服务拿到地址后，直接交给 `browser` subagent，**不要**再用 `curl`、`lsof`、`ps` 去探测本地端口。

如果是纯 CLI 环境（无内置浏览器面板），则把 `http://127.0.0.1:XXXX/` 地址告诉用户，让用户在自己的浏览器里打开。

---

## 和 Claude Code 的差异

| | Claude Code | Antigravity |
|---|---|---|
| 安装单位 | 目录（可软链） | 目录（可软链）或 `skills.json` |
| 用户级位置 | `~/.claude/skills/jingliku` | `~/.gemini/config/skills/jingliku` |
| 项目级位置 | `<项目>/.claude/skills/jingliku` | `<项目>/.agents/skills/jingliku` |
| 斜杠命令 | `/jingliku` | `/jingliku` |
| 右半屏打开方式 | 内置预览面板 / `.claude/launch.json` | 调用内置 `browser` subagent 打开 `http://127.0.0.1:XXXX/` |
| 终端沙箱影响 | 视权限模式而定 | `serve.py --ensure` 需 `BypassSandbox: true` 授权一次；读写 `~/经历库` JSON 与创建 `~/.gemini/config/skills` 软链在沙箱内直接可用 |

---

## 在 Antigravity 上实测过的行为（2026-11-18）

- **安装软链：** 在默认沙箱内执行 `mkdir -p "$HOME/.gemini/config/skills" && ln -sfn ... "$HOME/.gemini/config/skills/jingliku"` 直接成功（尽管 `ls ~/.gemini/config/` 会被沙箱拒绝）。
- **检查更新：** 沙箱内 `check_update.py` 因无法访问 `~/.ssh` 输出 `SKIPPED ...` 并正常退出（exit 0），不阻塞后续启动。
- **数据目录读写：** 即使当前会话没有打开任何工作区（no active workspace），沙箱内对 `/Users/<you>/经历库` 的存在性检查（`test -f`）和写入测试（`touch` / `rm`）均直接通过。
- **启动本地服务：** 默认沙箱内 `serve.py --ensure` 会因本地网络探测限制报 `FAILED to start`；改为 `BypassSandbox: true` 后立即成功返回 `RUNNING http://127.0.0.1:8766/`（8765 被占用时自动顺延到 8766）。
- **内置浏览器渲染：** 通过 `invoke_subagent(TypeName="browser", Model="flash")` 打开 `http://127.0.0.1:8766/`，右侧内置浏览器正常渲染三栏界面（左侧类型筛选与「已同步」状态、中间时间线、右侧经历详情与写法），HTTP 200 无连接报错。

---

## 装完自检

```bash
python3 --version                                                    # 需要 3.9+
test -f "$HOME/.gemini/config/skills/jingliku/SKILL.md" && echo INSTALLED
python3 -m json.tool "$HOME/经历库/config.json" > /dev/null && echo VAULT_OK
```

`VAULT_OK` 没出来就按 `<SKILL>/recipes/01-启动.md` 第 2 步初始化数据目录（空库或带示例数据）。
其余功能（入库、挂作品、申请写作、改删、导出 PDF）完全按 `SKILL.md` 的任务表走，无需额外适配。
