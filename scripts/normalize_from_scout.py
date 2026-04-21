"""把 Scout output JSON 规整成 Charles schema。

Scout 输出: ~/.openclaw/workspace-scout/output/topics_YYYYMMDD_HHMMSS.json
"""
import glob
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

SCOUT_OUTPUT_DIR = Path.home() / ".openclaw" / "workspace-scout" / "output"
ALLOWED_DIRECTIONS = {"AI", "美国", "世界", "中国"}
MAX_SLUG_LEN = 60
SCHEMA_FIELDS = ("rank", "slug", "title", "keywords", "angles", "direction", "posted_at")


def find_latest_output() -> Path | None:
    paths = sorted(SCOUT_OUTPUT_DIR.glob("topics_*.json"))
    return paths[-1] if paths else None


def slugify(text: str, rank: int) -> str:
    if not text:
        return f"topic-{rank:02d}"
    norm = unicodedata.normalize("NFKD", text)
    ascii_only = norm.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^A-Za-z0-9]+", "-", ascii_only).strip("-").lower()
    if not s:
        return f"topic-{rank:02d}"
    if len(s) > MAX_SLUG_LEN:
        cut = s[:MAX_SLUG_LEN].rsplit("-", 1)[0]
        s = cut if cut else s[:MAX_SLUG_LEN]
    return s


def to_utc_z(local_iso: str) -> str:
    dt = datetime.fromisoformat(local_iso)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_one(item: dict) -> dict | None:
    direction = item.get("direction")
    if direction not in ALLOWED_DIRECTIONS:
        return None
    rank = int(item["rank"])
    return {
        "rank": rank,
        "slug": slugify(item.get("title", ""), rank),
        "title": item["title"],
        "keywords": item.get("keywords", []),
        "angles": item.get("angles", []),
        "direction": direction,
        "posted_at": to_utc_z(item["posted_at"]),
    }


def load_and_normalize(path: Path) -> tuple[list[dict], int]:
    """returns (kept_items_sorted_by_rank, total_in_source)"""
    raw = json.loads(path.read_text(encoding="utf-8"))
    kept = [n for it in raw if (n := normalize_one(it)) is not None]
    kept.sort(key=lambda x: x["rank"])
    return kept, len(raw)
