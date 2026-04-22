# broll-dispatch

OpenClaw skill — 用户发一句自然语言标题 → LLM 扩展成合规 JSON → 投递到 Windows B-Roll download agent 的 inbox(Google Drive 同步)。

## 配对

- **Mac 端(本仓库)**:接自然语言 → MiniMax 扩展 → 写 `video-inbox/{rank:02d}_{slug}.json`
- **Windows 端**:B-Roll download agent(`--once` / `--daemon`)读 inbox → yt-dlp 搜索 + 下载 → 写回执到 `video-outputs/{slug}_ready.json`

## 安装

```
git clone https://github.com/jacobye2017-afk/broll-dispatch.git \
  ~/.openclaw/workspace-charles/skills/broll-dispatch
chmod +x ~/.openclaw/workspace-charles/skills/broll-dispatch/scripts/run.sh
```

`SKILL.md` 里的 exec 路径默认是 `workspace-charles`,若装到其他 workspace 需自行修改。

## 触发

在 Charles 对话里说:

- `dario 的故事` — LLM 扩展 + 投递
- `特朗普消失了 3 天` — 同上
- `苹果裁员` — 同上
- `dispatch test` — 写 1 个硬编码测试 JSON

## Schema (Windows agent 固化)

```json
{
  "rank": 1,
  "slug": "dario-amodei-anthropic-story",
  "title": "Dario Amodei: Anthropic 创始人",
  "keywords": ["Dario Amodei", "Anthropic CEO interview", "Claude AI founder"],
  "angles": ["Anthropic 成立之路", "Dario 的 AI safety 哲学"],
  "direction": "AI|美国|世界|中国",
  "posted_at": "2026-04-22T00:52:01Z"
}
```

## LLM 扩展

- API key: 读 `~/.openclaw/openclaw.json` 的 `env.MINIMAX_API_KEY`(或 shell 环境变量)
- Model: `MiniMax-M2.7-highspeed`(失败 retry 用 `MiniMax-M2.7`)
- Prompt 定义在 `scripts/llm_expand.py::SYSTEM_PROMPT`,要改行为改那里

## 配置

Google Drive 挂载路径写死在 `scripts/main.py:13-16`,如需换账号自行修改:

```python
INBOX = Path(
    "/Users/ye/Library/CloudStorage/GoogleDrive-<email>"
    "/我的云端硬盘/video-inbox"
)
```

## 约束

- 原子写(`.tmp` → rename),避免 Drive 同步读到半文件
- Windows 端 10GB/day 上限,每天别连续派超过 ~7 条
