#!/usr/bin/env python3
"""
DS New Customers daily snapshot capture.

Runs each morning against the Tableau view:
  https://inhouse-analytics.hktv.com.hk/#/views/DailyNewCustPerformanceReport/DailyNewCustPerformance

The published extract ("ds t-1") holds ONLY yesterday's row. This script captures
that row daily and appends it to ds_new_cust_daily.jsonl, building full history
from the capture start date forward.

History before capture start is NOT recoverable from this workbook (verified
2026-08-31: extract contains a single date; T-1 parameter not exposed to viewers;
URL param override breaks all sheets).

This script is invoked by the browser-console capture flow — it post-processes
the JSON the browser captured (via Hermes browser tools) and can also be run
standalone with --check to report DB health.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "ds_new_cust_daily.jsonl"


def load_all():
    if not DB.exists():
        return []
    rows = []
    for line in DB.read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def upsert(row: dict):
    """Insert or replace by date key. Keeps one row per date (latest wins)."""
    rows = [r for r in load_all() if r.get("date") != row["date"]]
    row["captured_at"] = datetime.now(timezone.utc).isoformat()
    rows.append(row)
    rows.sort(key=lambda r: r["date"])
    DB.parent.mkdir(parents=True, exist_ok=True)
    DB.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    return rows


def check():
    rows = load_all()
    dates = [r["date"] for r in rows]
    gaps = []
    if len(dates) > 1:
        from datetime import date as d, timedelta
        have = set(dates)
        cur, d1 = d.fromisoformat(dates[0]), d.fromisoformat(dates[-1])
        while cur <= d1:
            if cur.isoformat() not in have:
                gaps.append(cur.isoformat())
            cur += timedelta(days=1)
    print(f"rows={len(rows)} first={dates[0] if dates else '-'} last={dates[-1] if dates else '-'} gaps={gaps}")
    return rows


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    elif "--upsert" in sys.argv:
        payload = json.loads(sys.argv[sys.argv.index("--upsert") + 1])
        rows = upsert(payload)
        print(f"upserted; total={len(rows)}")
    else:
        print(__doc__)
