# scripts/persist_history.py
"""日次バッチの出力(直近24h)を履歴CSV(全期間)へ追記・永続化する。

設計:
  - 入力: --source (日次の dns_logs_summary.csv) / --history (累積 dns_history.csv)
  - 重複排除: (Datetime(JST), Location, Domain, Decision) の完全一致キー。
              同一キーが既存にあれば追加しない(Count は既存を優先=後勝ちさせない)。
  - 保持期間: --retention-days (デフォルト365)。履歴内の最新日付を基準に、
              それより古い行を削除する。0以下なら無制限。
  - 依存: 標準ライブラリのみ(csv/argparse/datetime)。

CSV列構成(reporter.write_csv 準拠):
  Datetime(JST), Location, Domain, Count, Decision
"""
import argparse
import csv
import os
from datetime import datetime, timedelta

HEADER = ["Datetime(JST)", "Location", "Domain", "Count", "Decision"]
DT_FMT = "%Y-%m-%d %H:%M:%S"


def _read_csv(path: str) -> list[dict]:
    """CSVを読み込み行リストを返す。存在しなければ空リスト。"""
    if not os.path.exists(path):
        return []
    rows: list[dict] = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def _key(r: dict) -> tuple:
    """重複排除キー: (Datetime, Location, Domain, Decision)。"""
    return (r.get("Datetime(JST)", ""), r.get("Location", ""),
            r.get("Domain", ""), r.get("Decision", ""))


def _parse_dt(r: dict):
    """日時をdatetimeで返す。パース不能なら None(防御的)。"""
    try:
        return datetime.strptime(r["Datetime(JST)"], DT_FMT)
    except (ValueError, KeyError):
        return None


def merge_history(history_rows: list[dict], source_rows: list[dict],
                  retention_days: int = 365) -> tuple[list[dict], dict]:
    """履歴に新規分をマージし、重複排除・保持期間トリムした行リストを返す。

    Returns: (merged_rows, stats)
    """
    # 1. 既存キー集合を作りつつ、有効な履歴行を保持
    merged: list[dict] = []
    seen: set = set()
    for r in history_rows:
        if _parse_dt(r) is None:      # 破損行はスキップ
            continue
        k = _key(r)
        if k in seen:                 # 履歴内の既存重複も排除
            continue
        seen.add(k)
        merged.append(r)

    # 2. 新規分を重複排除しながら追加
    added = 0
    for r in source_rows:
        if _parse_dt(r) is None:
            continue
        k = _key(r)
        if k in seen:                 # 既存と完全一致 → スキップ(後勝ちさせない)
            continue
        seen.add(k)
        merged.append(r)
        added += 1

    before_trim = len(merged)

    # 3. 保持期間トリム(履歴内の最新日付を基準にする)
    removed_old = 0
    if retention_days and retention_days > 0 and merged:
        latest = max(_parse_dt(r) for r in merged)
        cutoff = latest - timedelta(days=retention_days)
        kept = [r for r in merged if _parse_dt(r) >= cutoff]
        removed_old = before_trim - len(kept)
        merged = kept

    # 4. 日時昇順でソート(可読性・差分の安定化)
    merged.sort(key=lambda r: (_parse_dt(r), r.get("Location", ""), r.get("Domain", "")))

    stats = {
        "history_in": len(history_rows),
        "source_in": len(source_rows),
        "added": added,
        "removed_old": removed_old,
        "total_out": len(merged),
    }
    return merged, stats


def write_history(path: str, rows: list[dict]) -> None:
    """履歴CSVを書き出す(ヘッダ付き)。"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in HEADER})


def main():
    ap = argparse.ArgumentParser(description="Persist daily DNS summary into history CSV.")
    ap.add_argument("--source", default="dns_logs_summary.csv",
                    help="日次バッチが出力した直近24h CSV")
    ap.add_argument("--history", default="history/dns_history.csv",
                    help="累積する履歴CSV")
    ap.add_argument("--retention-days", type=int, default=365,
                    help="保持日数(0以下で無制限)")
    args = ap.parse_args()

    source_rows = _read_csv(args.source)
    if not source_rows:
        print(f"⚠️ No source rows in {args.source}. Nothing to persist.")
        # 履歴が既存なら触らず終了。無ければ空ヘッダだけ作る。
        if not os.path.exists(args.history):
            write_history(args.history, [])
        return

    history_rows = _read_csv(args.history)
    merged, stats = merge_history(history_rows, source_rows, args.retention_days)
    write_history(args.history, merged)

    print("✅ History persisted:")
    print(f"   history(before) : {stats['history_in']:,} rows")
    print(f"   source(new 24h) : {stats['source_in']:,} rows")
    print(f"   added           : {stats['added']:,} rows")
    print(f"   removed(>{args.retention_days}d): {stats['removed_old']:,} rows")
    print(f"   history(after)  : {stats['total_out']:,} rows")


if __name__ == "__main__":
    main()
