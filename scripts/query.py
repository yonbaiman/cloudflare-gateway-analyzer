# scripts/query.py
"""蓄積CSV(全期間)の読み込み・期間/ロケーション絞り込み・粒度判定。

CSV列構成は reporter.write_csv が出力する形式に準拠:
    Datetime(JST), Location, Domain, Count, Decision
"""
import csv
from datetime import datetime, date, timedelta
from typing import Optional


def load_history_csv(path: str = "history/dns_history.csv") -> list[dict]:
    """蓄積CSV(全期間)を読み込み、行リストを返す。

    壊れた行(日時パース不能など)は防御的にスキップする。
    """
    out: list[dict] = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    dt = datetime.strptime(r["Datetime(JST)"], "%Y-%m-%d %H:%M:%S")
                except (ValueError, KeyError):
                    continue
                out.append({
                    "dt": dt,
                    "location": r.get("Location", "Unknown"),
                    "domain": r.get("Domain", ""),
                    "count": int(r.get("Count", 0) or 0),
                    "decision": r.get("Decision", "Unknown"),
                })
    except FileNotFoundError:
        print(f"⚠️ History CSV not found: {path}")
    return out


def filter_rows(rows: list[dict], start: date, end: date,
                location: Optional[str] = None) -> list[dict]:
    """期間[start, end](endは当日を含む)とロケーションで絞り込む。"""
    end_excl = end + timedelta(days=1)  # endの当日を含めるため翌日0時未満で判定
    res: list[dict] = []
    for r in rows:
        d = r["dt"].date()
        if not (start <= d < end_excl):
            continue
        if location and r["location"] != location:
            continue
        res.append(r)
    return res


def pick_granularity(start: date, end: date, mode: str = "auto") -> str:
    """集計粒度を決定する。

    mode='auto' の場合: 期間が2日を超えるなら 'daily'、それ以下は 'hourly'。
    mode='hourly'/'daily' の場合はそのまま返す。
    """
    if mode in ("hourly", "daily"):
        return mode
    span_days = (end - start).days + 1
    return "daily" if span_days > 2 else "hourly"
