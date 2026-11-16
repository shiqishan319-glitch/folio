# 适配：Codex（待验证）

> 以下是初步方案，还没有在 Codex 里实测。

## 安装

在用户的 `AGENTS.md`（全局 `~/.codex/AGENTS.md` 或项目根目录）里加一段，让 Codex 知道去读 SKILL.md：

```markdown
## 经历库
当用户要记录经历、准备网申/简历/自荐信/动机信，或导出相关 PDF 时，
先读 /path/to/Sqs经历库/skill/SKILL.md 并按其中的流程操作。
```

如果 Codex 支持 skills 目录，改成把 `skill/` 链接进去即可（待确认）。

## 在右半屏打开前端

- 按 SKILL.md 在后台运行 `python3 /path/to/skill/scripts/serve.py`。
- Codex 是否有能打开 `localhost` 的内置浏览器或 canvas，**待验证**（PRD 待解决问题 2）。没有就把地址给用户，在系统浏览器里打开。

## 待验证清单

- [ ] Codex 读取 AGENTS.md 后能否稳定按 SKILL.md 操作
- [ ] 后台进程（serve.py）能否在 Codex 会话里保持运行
- [ ] 有没有内置浏览器 / 右半屏可以显示 localhost 页面
