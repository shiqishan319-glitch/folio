# 适配：豆包（Doubao 桌面版 · Agent 模式）

> 已在 macOS 桌面客户端实测：安装、技能自动生效、serve.py 后台进程存活、API 读写。未实测项见文末「待验证清单」。

## 安装

### 1. 找到安装目录（不要照抄任何示例路径）

豆包的用户技能目录没有固定路径：规范位置是「以 `workspace/.user_skills` 结尾」的那个目录，前缀因系统与安装方式而异。macOS 桌面客户端默认形如：

```
/Users/<用户名>/Library/Application Support/Doubao/Default/.doubao/agent_mode/workspace/.user_skills
```

不确定就搜（注意 `Application Support` 里的空格）：

```bash
find ~/Library/Application\ Support/Doubao -type d -name .user_skills 2>/dev/null
```

- 要装的是复数的 `.user_skills`；旁边的 `.skills` 是系统内置技能目录，不要动。
- 最省事的做法：把本 README 交给豆包，让它自己解析位置并执行安装——它知道自己默认装在哪。

### 2. 复制（安装目录必须叫 `jingliku`）

源码文件夹叫 `skill`，**安装目录必须与 SKILL.md 的 `name` 一致，即 `jingliku`**。原目录保留（复制，不要移动），并排除 macOS 的 .DS_Store：

```bash
rsync -a --exclude ".DS_Store" "/path/to/Sqs经历库/skill/" "<第 1 步的目录>/jingliku/"
```

装完立即 diff 校验——源目录可能正在被编辑（实测发生过：安装途中 SKILL.md 被改，第一份拷贝就旧了）：

```bash
diff -rq --exclude=.DS_Store "/path/to/Sqs经历库/skill" "<目录>/jingliku" && echo IDENTICAL
```

### 3. 检查 frontmatter（无需安装任何依赖）

- 开头 YAML 必须有 `name:` 和 `description:`。
- **这个 description 的值必须用双引号包起来**：内容含半角「冒号+空格」（…experience vault: logging…），不加引号会被部分 YAML 解析器截断或报错（实测踩过）。
- 如果让豆包用官方校验脚本检查 frontmatter：脚本依赖 PyYAML，豆包环境的系统 python3 没装，会报 `ModuleNotFoundError: No module named 'yaml'`——那是校验工具缺依赖，不是 skill 坏了；手工核对上面两条即可。

### 4. 生效时机

装完即用，无需重启会话（实测当轮就进入技能列表）。触发靠 description：用户说「帮我记一段经历 / 写网申 / 导出简历 PDF」即可命中；也可以直接点名「用经历库 / jingliku」。

## 在右半屏打开前端

第 1–3 步照 `recipes/01-启动.md` 不变。豆包的差异与实测结论：

- 豆包的命令直接跑在用户真实系统上（无沙箱容器），vault 就是真实文件夹；`--ensure` 拉起的 detached 进程**跨命令调用存活**（实测：隔一条命令再 `--ensure` 返回 `RUNNING`，curl 能取到数据）。
- 第 4 步（已实测）：豆包桌面版右侧工作区新建 browser 标签页，打开 serve.py 打印的地址即可——localhost 页面正常加载，标签标题正确显示「经历库」；没有该能力（网页版等）就退化为把地址告诉用户，用系统浏览器打开。

## 升级与运维坑（实测）

- **升级后页面可能还是旧版**：存活的 serve.py 进程把 `--app` 目录固定在启动那一刻。升级安装目录后，杀掉旧进程再 `--ensure`（同一 vault 的地址与写 token 会沿用，已打开的页面自动重连，见 recipes/01 第 3 步）。
- **杀进程要验尸**：实测普通 `kill` 后 1 秒进程可能仍在监听，用 `lsof -nP -iTCP:8765 -sTCP:LISTEN` 确认端口已释放再重启，必要时 `kill -9`。
- **8765 可能被别的 vault 的旧服务占着**：serve.py 会自动换端口（如 8766），先用 lsof 确认那是谁，别杀错；多服务并存时每个 vault 靠自己的 `.runtime.json` 记住自己的地址。
- 路径含中文与空格（技能根目录本身就带 `Application Support`）：命令里的路径一律用双引号包好（SKILL.md 铁律 2）。
- macOS 是 BSD 工具链；serve.py 纯标准库，系统 python3（≥3.9）即可，无需额外环境。

## 待验证清单

- [x] 右侧工作区 browser 标签页打开 localhost 页面（实测正常加载，标题正确）
- [ ] 标签页内编辑 → 写回 vault 的闭环
- [ ] `~/Doubao/skills`、`~/.agents/skills` 安装是否同样生效
- [ ] 符号链接安装（git pull 即升级）是否被豆包扫描支持
