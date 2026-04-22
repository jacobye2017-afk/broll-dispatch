"""把用户自然语言标题扩展成 Charles schema JSON。

调 MiniMax(配置从 ~/.openclaw/openclaw.json 读),失败自动 retry 一次。
"""
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MINIMAX_ENDPOINT = "https://api.minimaxi.com/v1/chat/completions"
MODEL_PRIMARY = "MiniMax-M2.7-highspeed"
MODEL_FALLBACK = "MiniMax-M2.7"
OPENCLAW_CFG = Path.home() / ".openclaw" / "openclaw.json"

ALLOWED_DIRECTIONS = {"AI", "美国", "世界", "中国"}
REQUIRED_FIELDS = ("rank", "slug", "title", "keywords", "angles", "direction", "posted_at")

SYSTEM_PROMPT = """You are Charles, a B-roll topic expander for a short-video pipeline. The user gives you a brief topic in Chinese or English. Turn it into a JSON that tells a downstream YouTube downloader what footage to fetch.

OUTPUT FORMAT — return ONLY a JSON object, nothing else. No prose, no markdown, no code fences.

Schema:
{
  "rank": 1,
  "slug": "ascii-kebab-case-max-60-chars",
  "title": "short clean headline, Chinese or English ok",
  "keywords": ["English phrase 1", "English phrase 2", ...],
  "angles": ["中文角度 1", "中文角度 2", "中文角度 3"],
  "direction": "AI" | "美国" | "世界" | "中国",
  "posted_at": "__PLACEHOLDER__"
}

FIELD RULES:

1. slug — ASCII only [a-z0-9-], kebab-case, max 60 chars, derived from the English equivalent. Examples:
     "dario 的故事" → "dario-amodei-anthropic-story"
     "特朗普消失了" → "trump-disappears-3-days"
     "奥特曼辞职" → "sam-altman-resigns"

2. title — one clean headline. Chinese or English both fine. 10-40 chars. For humans to read, NOT for search.

3. keywords — 5 to 8 ENGLISH natural phrases that someone would type into YouTube to find good B-roll. Expand the topic:
   - proper names (Dario Amodei, not "dario")
   - related entities (Anthropic, Claude, AI safety)
   - concrete visual queries ("Dario Amodei interview", "Anthropic office tour")
   AVOID hashtags. AVOID "#". English preferred — YouTube's English corpus is 10x larger.

4. angles — 2 to 3 Chinese 短视频切入角度.

5. direction — pick EXACTLY ONE from {"AI", "美国", "世界", "中国"}.
   - AI: AI companies/models/safety/researchers/tech industry
   - 美国: US politics/society/US-only news
   - 世界: international events, non-US non-China
   - 中国: China-specific
   If ambiguous, default "AI" for tech, "世界" otherwise.

6. rank — always 1.

7. posted_at — exact literal string "__PLACEHOLDER__". The wrapper substitutes it.

EXAMPLE:

Input: "dario 的故事"
Output:
{"rank":1,"slug":"dario-amodei-anthropic-story","title":"Dario Amodei: Anthropic 创始人","keywords":["Dario Amodei","Anthropic CEO interview","Claude AI founder","AI safety Dario","constitutional AI","Anthropic story"],"angles":["Anthropic 成立之路:从 OpenAI 出走到 Claude","Dario 的 AI safety 哲学","兄妹搭档:Dario 与 Daniela"],"direction":"AI","posted_at":"__PLACEHOLDER__"}

Now respond with ONLY the JSON for the user's topic. No preamble. No explanation."""


def get_api_key() -> str:
    key = os.environ.get("MINIMAX_API_KEY")
    if key:
        return key
    cfg = json.loads(OPENCLAW_CFG.read_text())
    key = cfg.get("env", {}).get("MINIMAX_API_KEY")
    if not key:
        raise RuntimeError("MINIMAX_API_KEY not found in env or openclaw.json")
    return key


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def call_minimax(user_msg: str, model: str, temperature: float = 0.3) -> str:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": temperature,
        "max_tokens": 2000,
    }
    req = urllib.request.Request(
        MINIMAX_ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_api_key()}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"]


def extract_json(s: str) -> str:
    """Strip <think>...</think>, code fences, and find the JSON object."""
    s = s.strip()
    if "</think>" in s:
        s = s.rsplit("</think>", 1)[1].strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return s
    return s[start : end + 1]


def parse_and_validate(raw: str) -> dict:
    data = json.loads(extract_json(raw))
    missing = [k for k in REQUIRED_FIELDS if k not in data]
    if missing:
        raise ValueError(f"schema missing fields: {missing}")
    if data["direction"] not in ALLOWED_DIRECTIONS:
        raise ValueError(f"invalid direction: {data['direction']!r}")
    if not isinstance(data["keywords"], list) or not data["keywords"]:
        raise ValueError("keywords must be non-empty list")
    if not isinstance(data["angles"], list):
        raise ValueError("angles must be list")
    data["rank"] = int(data.get("rank", 1))
    data["posted_at"] = iso_now()
    return data


def expand(user_msg: str) -> dict:
    last_err = None
    last_raw = ""
    for attempt, (model, temp) in enumerate([
        (MODEL_PRIMARY, 0.3),
        (MODEL_PRIMARY, 0.0),
        (MODEL_FALLBACK, 0.0),
    ]):
        try:
            raw = call_minimax(user_msg, model, temp)
            last_raw = raw
            return parse_and_validate(raw)
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            last_err = e
            continue
    raise RuntimeError(f"LLM expand failed after retries: {last_err}\nraw: {last_raw[:500]}")
