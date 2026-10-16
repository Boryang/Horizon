"""Build the retail-sentiment section for Bor's daily email from ApeWisdom.

Numbers come straight from ApeWisdom (Reddit ticker-mention counts); no AI
rewriting, so every figure is the source's own. Writes data/extra_sections.md.
"""

from __future__ import annotations

import html
import json
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

API = "https://apewisdom.io/api/v1.0/filter/{filter}/page/{page}"
OUT = Path("data/extra_sections.md")
TPE = timezone(timedelta(hours=8))

# A ticker counts as a sudden spike when it has real volume and either
# doubled its mentions or jumped far up the ranking within 24h.
SPIKE_MIN_MENTIONS = 30
SPIKE_RATIO = 2.0
SPIKE_RANK_JUMP = 20


def fetch(filter_name: str, pages: int = 2) -> list[dict]:
    rows: list[dict] = []
    for page in range(1, pages + 1):
        req = urllib.request.Request(
            API.format(filter=filter_name, page=page),
            headers={"User-Agent": "Mozilla/5.0 (Horizon daily radar)"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            rows.extend(json.load(resp).get("results", []))
    return rows


def _int(v) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def change(now: int, before: int) -> str:
    if before <= 0:
        return "新進榜"
    pct = (now - before) / before * 100
    return f"{pct:+.0f}%"


def rank_move(rank: int, before) -> str:
    b = _int(before)
    if b <= 0:
        return "新進榜"
    d = b - rank
    return f"↑{d}" if d > 0 else (f"↓{-d}" if d < 0 else "持平")


def build(rows: list[dict], fetched_at: datetime) -> str:
    for r in rows:
        r["name"] = html.unescape(r.get("name") or "")
        r["mentions"] = _int(r.get("mentions"))
        r["mentions_24h_ago"] = _int(r.get("mentions_24h_ago"))
        r["rank"] = _int(r.get("rank"))

    top = rows[:10]
    spikes = []
    for r in rows:
        m, b = r["mentions"], r["mentions_24h_ago"]
        jump = _int(r.get("rank_24h_ago")) - r["rank"] if _int(r.get("rank_24h_ago")) else 0
        if m >= SPIKE_MIN_MENTIONS and ((b > 0 and m / b >= SPIKE_RATIO) or b == 0 or jump >= SPIKE_RANK_JUMP):
            spikes.append(r)
    spikes.sort(key=lambda r: (r["mentions"] / max(r["mentions_24h_ago"], 1)), reverse=True)
    spikes = spikes[:8]

    ts = fetched_at.astimezone(TPE).strftime("%Y-%m-%d %H:%M")
    lines = [
        "## 散戶熱度雷達（Reddit 提及次數）",
        "",
        f"> 來源：[ApeWisdom](https://apewisdom.io/)，統計 Reddit 各投資版過去 24 小時的個股提及次數；"
        f"抓取時間 {ts}（台灣時間）。數字為來源原始統計，未經 AI 改寫。",
        "",
        "### 異常竄升",
        "",
        f"條件：24 小時提及 ≥ {SPIKE_MIN_MENTIONS} 次，且提及量較前一個 24 小時至少翻倍、新進榜，或排名上升 ≥ {SPIKE_RANK_JUMP} 名。",
        "",
    ]
    if spikes:
        lines += ["| 代號 | 名稱 | 24h 提及 | 前 24h | 變化 | 排名 | 讚數 |", "|---|---|---|---|---|---|---|"]
        for r in spikes:
            lines.append(
                f"| {r['ticker']} | {r['name']} | {r['mentions']} | {r['mentions_24h_ago']} | "
                f"{change(r['mentions'], r['mentions_24h_ago'])} | {r['rank']}（{rank_move(r['rank'], r.get('rank_24h_ago'))}） | {r.get('upvotes', '')} |"
            )
    else:
        lines.append("今天沒有符合條件的個股。")
    lines += [
        "",
        "### 討論度前 10",
        "",
        "| 排名 | 代號 | 名稱 | 24h 提及 | 變化 | 讚數 |",
        "|---|---|---|---|---|---|",
    ]
    for r in top:
        lines.append(
            f"| {r['rank']}（{rank_move(r['rank'], r.get('rank_24h_ago'))}） | {r['ticker']} | {r['name']} | "
            f"{r['mentions']} | {change(r['mentions'], r['mentions_24h_ago'])} | {r.get('upvotes', '')} |"
        )
    lines += ["", "*熱度是落後指標，只適合當觀察名單入口，不是進場理由。*", ""]
    return "\n".join(lines)


def main() -> int:
    try:
        rows = fetch("all-stocks")
    except Exception as exc:  # keep the daily run going without this section
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(f"## 散戶熱度雷達\n\n> 今天無法取得 ApeWisdom 資料（{type(exc).__name__}）。\n\n---\n\n", encoding="utf-8")
        print(f"ApeWisdom fetch failed: {exc}", file=sys.stderr)
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(rows, datetime.now(timezone.utc)), encoding="utf-8")
    print(f"Wrote {OUT} from {len(rows)} ApeWisdom rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
