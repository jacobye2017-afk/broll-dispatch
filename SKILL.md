---
name: broll-dispatch
description: >
  用户发自然语言标题 → LLM 扩展成合规 JSON → 投递到 Windows B-Roll
  download agent 的 inbox（Google Drive 同步）。例如用户说
  "dario 的故事" / "特朗普消失了" / "苹果裁员" / "奥特曼" 等,都直接 exec。
  Triggers on: 任何非空消息(除 "dispatch test" 走测试分支)。
---

## ⚠️ EXECUTION RULE

```
exec: bash /Users/ye/.openclaw/workspace-charles/skills/broll-dispatch/scripts/run.sh "{用户原始消息}"
```

把脚本 stdout 原样返回给用户，不要解释、不要道歉、不要改格式、不要脑补菜单。

## 参数说明

- `<任何自然语言标题>` → 调 MiniMax 扩展成 7 字段 JSON 并投递
- `dispatch test` → 写 1 个硬编码测试 JSON(调试用)

## Schema (Windows agent 已按此实现,不可改)

```json
{
  "rank": 1,
  "slug": "ascii-kebab-case",
  "title": "标题(中英文均可,仅展示用)",
  "keywords": ["英文自然搜索短语", "..."],
  "angles": ["中文角度", "..."],
  "direction": "AI|美国|世界|中国",
  "posted_at": "2026-04-21T10:00:00Z"
}
```

## LLM 扩展依赖

- API key: 读 `~/.openclaw/openclaw.json` 里的 `env.MINIMAX_API_KEY`
- Primary model: `MiniMax-M2.7-highspeed`(失败自动 retry 用 `MiniMax-M2.7`)
- Prompt 在 `scripts/llm_expand.py` 的 `SYSTEM_PROMPT`

## 输出路径

`~/Library/CloudStorage/GoogleDrive-jacobye2017@gmail.com/我的云端硬盘/video-inbox/{rank:02d}_{slug}.json`

原子写(`.tmp` → rename),Windows 端 daemon 不会读到半文件。
