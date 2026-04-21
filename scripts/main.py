"""broll-dispatch 主入口。

把选题 JSON 投递到 Windows B-Roll download agent 的 Google Drive inbox。
MVP: 只实现 "dispatch test" 路径。
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def dispatch_items(items: list[dict]) -> list[Path]:
    if len(items) > MAX_PER_DISPATCH:
        log(f"⚠️ 投递数量 {len(items)} 超过上限 {MAX_PER_DISPATCH}，截断")
        items = items[:MAX_PER_DISPATCH]
    written = []
    for it in items:
        p = write_one(it)
        log(f"✅ wrote {p.name}")
        written.append(p)
    return written


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
        print("   检查 Google Drive 是否已挂载 / 路径是否正确")
        return 2
    item = build_test_item()
    log(f"📦 构造测试选题: rank={item['rank']} slug={item['slug']}")
    written = dispatch_items([item])
    print("✅ dispatch test 完成")
    print(f"   投递数量: {len(written)}")
    for p in written:
        print(f"   - {p}")
    print()
    print("👉 下一步: Google Drive 同步 (~30s) → Windows daemon 自动接住")
    print("👉 回执位置: ~/Library/CloudStorage/.../我的云端硬盘/video-outputs/")
    return 0


def main() -> int:
    msg = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    low = msg.lower()
    log(f"📝 msg={msg!r}")

    if not msg or "test" in low or "测试" in msg:
        return cmd_test()

    print("❌ 未识别的命令")
    print()
    print("MVP 仅支持: dispatch test")
    print("未来支持: dispatch broll <path.json> / dispatch broll from scout")
    return 1


if __name__ == "__main__":
    sys.exit(main())
