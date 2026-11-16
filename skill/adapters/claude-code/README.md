# 适配：Claude Code（桌面版 / CLI）

## 安装

把 skill 目录链接到个人 skills 目录（升级时 `git pull` 即可，不用重装）：

```bash
ln -s "/path/to/Sqs经历库/skill" ~/.claude/skills/jingliku
```

也可以只装到某个项目里：链接到 `<项目>/.claude/skills/jingliku`。

## 在右半屏打开前端

Claude Code 桌面版有内置浏览器，可以打开 `localhost`（已验证）。

- **AI 自己启动：** 按 SKILL.md 在后台运行 `serve.py`，然后用内置浏览器打开它打印的地址。
- **固定配置：** 在当前项目的 `.claude/launch.json` 里加一项，以后用预览面板一键启动：

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "jingliku",
      "runtimeExecutable": "python3",
      "runtimeArgs": ["/Users/<you>/.claude/skills/jingliku/scripts/serve.py", "--port", "8765"],
      "port": 8765
    }
  ]
}
```

注意：

- 内置浏览器直接打开项目文件夹外的 `file://` 页面时，只会显示静态快照，所以要走 `serve.py`。
- CLI 版没有内置浏览器，把地址给用户，让他用自己的浏览器打开即可。
