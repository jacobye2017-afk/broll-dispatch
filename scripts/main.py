"""broll-dispatch 主入口。

把用户自然语言标题投递到 Windows B-Roll download agent 的 Google Drive inbox。
支持: <任何自然语言标题> / dispatch test
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import llm_expand

INBOX = Path(
    "/Users/ye/Library/CloudStorage/GoogleDrive-jacobye2017@gmail.com"
    "/我的云端硬盘/video-inbox"
)
MAX_PER_DISPATCH = 5


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sanitize_slug(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_\-]+", "_", s).strip("_")
    return s or "untitled"


def validate(item: dict) -> list[str]:
    required = ["rank", "slug", "title", "keywords", "angles", "direction", "posted_at"]
    errs = [f"missing field: {k}" for k in required if k not in item]
    if "direction" in item and item["direction"] not in ("AI", "美国", "世界", "中国"):
        errs.append(f"invalid direction: {item['direction']!r}")
    if "rank" in item and not isinstance(item["rank"], int):
        errs.append(f"rank must be int, got {type(item['rank']).__name__}")
    return errs


def write_one(item: dict) -> Path:
    errs = validate(item)
    if errs:
        raise ValueError(f"schema validation failed: {errs}")
    rank = int(item["rank"])
    slug = sanitize_slug(item["slug"])
    path = INBOX / f"{rank:02d}_{slug}.json"
    INBOX.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def build_test_item() -> dict:
    return {
        "rank": 1,
        "slug": f"openclaw_dispatch_test_{datetime.now().strftime('%H%M%S')}",
        "title": "OpenClaw dispatcher MVP 测试投递",
        "keywords": [
            "Claude Code",
            "OpenClaw",
            "Google Drive sync",
            "Windows agent",
        ],
        "angles": [
            "Mac→Windows 跨机投递链路打通",
            "broll-dispatch skill MVP 上线",
        ],
        "direction": "AI",
        "posted_at": iso_now(),
    }


def cmd_test() -> int:
    if not INBOX.exists():
        print(f"❌ inbox 不存在: {INBOX}")
        return 2
    item = build_test_item()
    log(f"📦 构造测试选题: rank={item['rank']} slug={item['slug']}")
    p = write_one(item)
    print("✅ dispatch test 完成")
    print(f"   → {p.name}")
    return 0


def cmd_expand(msg: str) -> int:
    if not INBOX.exists():
        print(f"❌ inbox 不存在: {INBOX}")
        return 2
    log(f"🧠 LLM 扩展中: {msg!r}")
    try:
        item = llm_expand.expand(msg)
    except Exception as e:
        print(f"❌ LLM 扩展失败: {e}")
        return 3
    log(f"📦 slug={item['slug']} direction={item['direction']}")
    p = write_one(item)
    print(f"✅ 已投递: {msg}")
    print()
    print(f"   标题: {item['title']}")
    print(f"   方向: {item['direction']}")
    print(f"   关键词: {', '.join(item['keywords'])}")
    print(f"   角度:")
    for a in item["angles"]:
        print(f"     - {a}")
    print(f"   文件: {p.name}")
    print()
    print("👉 下一步: 去 Windows 群说\"处理\",或等 daemon 自动接 (~60s)")
    return 0


def main() -> int:
    msg = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    low = msg.lower()
    log(f"📝 msg={msg!r}")

    if not msg:
        print("❌ 请告诉我你要投什么选题,例如:")
        print("   - dario 的故事")
        print("   - 特朗普消失了 3 天")
        print("   - 安克雷奇峰会")
        print("或用 'dispatch test' 跑一次测试投递。")
        return 1

    if low in ("dispatch test", "测试") or low.startswith("dispatch test"):
        return cmd_test()

    return cmd_expand(msg)


if __name__ == "__main__":
    sys.exit(main())
