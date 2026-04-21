"""broll-dispatch 主入口。

把选题 JSON 投递到 Windows B-Roll download agent 的 Google Drive inbox。
支持: dispatch test / dispatch broll from scout。
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import normalize_from_scout

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


def cmd_from_scout() -> int:
    if not INBOX.exists():
        print(f"❌ inbox 不存在: {INBOX}")
        return 2
    latest = normalize_from_scout.find_latest_output()
    if latest is None:
        print("❌ Scout 还没产出选题，让 Tony 先跑一次\"今日选题\"")
        return 3
    log(f"📂 读取 Scout 最新输出: {latest.name}")

    kept, total = normalize_from_scout.load_and_normalize(latest)
    log(f"🧮 source={total} 条 / direction 过滤后剩 {len(kept)} 条")

    if not kept:
        print("❌ 这一批 Scout 选题方向全部不在 {AI/美国/世界/中国} 范围，没东西可投")
        print(f"   源文件: {latest}")
        return 4

    to_send = kept[:MAX_PER_DISPATCH]
    written = dispatch_items(to_send)

    print(f"✅ dispatch broll from scout 完成")
    print(f"   源: {latest.name}")
    print(f"   投递数量: {len(written)} (源 {total} 条 → 过滤后 {len(kept)} 条 → 取 rank 最小 {len(to_send)} 条)")
    for p, item in zip(written, to_send):
        print(f"   - rank={item['rank']:>2} [{item['direction']}] {p.name}")

    if len(kept) < MAX_PER_DISPATCH:
        print()
        print(f"⚠️ 只投递了 {len(kept)} 条，其余方向不符被过滤")

    print()
    print("👉 下一步: Google Drive 同步 (~30s) → Windows daemon 接住下载")
    print("👉 回执位置: ~/Library/CloudStorage/.../我的云端硬盘/video-outputs/{slug}_ready.json")
    return 0


def main() -> int:
    msg = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    low = msg.lower()
    log(f"📝 msg={msg!r}")

    if "from scout" in low or "从 scout" in msg or "从scout" in msg or "派发选题" in msg:
        return cmd_from_scout()

    if not msg or "test" in low or "测试" in msg:
        return cmd_test()

    print("❌ 未识别的命令")
    print()
    print("支持的命令:")
    print("  dispatch test                       → 投递 1 个测试 JSON")
    print("  dispatch broll from scout / 派发选题 → 拉 Scout 最新输出投递 Top 5")
    return 1


if __name__ == "__main__":
    sys.exit(main())
