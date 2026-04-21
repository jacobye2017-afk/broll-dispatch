---
name: broll-dispatch
description: >
  把选题 JSON 投递到 Windows B-Roll download agent 的 inbox
  （Google Drive 同步）。Windows 端 daemon 会自动接住并下载素材。
  Triggers on: "dispatch broll", "dispatch test", "投递 broll",
  "派发选题", "发 broll", "broll dispatch", "派发素材".
---

## ⚠️ EXECUTION RULE

```
exec: bash /Users/ye/.openclaw/workspace-scout/skills/broll-dispatch/scripts/run.sh "{用户原始消息}"
```

把脚本 stdout 原样返回给用户，不要解释、不要道歉。

## 参数说明

- `dispatch test` → 写 1 个测试 JSON 到 inbox（MVP 路径）
- `dispatch broll <path.json>` → 读取本地 JSON 文件并投递（未来扩展）
- `dispatch broll from scout` → 读取 Scout 最新 output 并投递（未来扩展）

## Schema (Windows agent 已按此实现)

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

## 约束

- 单次最多 5 个 JSON（Windows 端 10GB/day 上限保护）
- 输出路径: `~/Library/CloudStorage/GoogleDrive-jacobye2017@gmail.com/我的云端硬盘/video-inbox/{rank:02d}_{slug}.json`
