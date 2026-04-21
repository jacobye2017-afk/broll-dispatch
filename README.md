# broll-dispatch

OpenClaw skill — 把选题 JSON 从 Mac 投递到 Windows B-Roll download agent 的 inbox（经 Google Drive 同步）。

## 配对

- **Mac 端（本仓库）**：写 topic JSON → `video-inbox/{rank:02d}_{slug}.json`
- **Windows 端**：B-Roll download agent（`--once` / `--daemon`）读 inbox → 下载素材 → 写回执到 `video-outputs/{slug}_ready.json`

## 安装

```
# 作为 OpenClaw skill 使用
git clone https://github.com/jacobye2017-afk/broll-dispatch.git \
  ~/.openclaw/workspace-scout/skills/broll-dispatch
chmod +x ~/.openclaw/workspace-scout/skills/broll-dispatch/scripts/run.sh
```

## 触发

在 Scout 对话里说：

- `dispatch test` — 写 1 个测试 JSON 到 inbox（MVP）
- `dispatch broll <path.json>` — 未实现
- `dispatch broll from scout` — 未实现

## Schema

Windows agent 期望的字段：

```json
{
  "rank": 1,
  "slug": "trump_budget_1_5T",
  "title": "...",
  "keywords": ["..."],
  "angles": ["..."],
  "direction": "AI|美国|世界|中国",
  "posted_at": "2026-04-21T10:00:00Z"
}
```

## 配置

Google Drive 挂载路径写死在 `scripts/main.py:11-14`，如需换账号自行修改：

```python
INBOX = Path(
    "/Users/ye/Library/CloudStorage/GoogleDrive-<email>"
    "/我的云端硬盘/video-inbox"
)
```

## 约束

- 单次最多 5 个 JSON（Windows 端 10GB/day 上限保护）
- 原子写（`.tmp` → rename），避免 Drive 同步读到半文件
