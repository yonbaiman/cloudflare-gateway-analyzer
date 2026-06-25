# scripts/persist_history.py
"""日次バッチの出力(直近 LOOKBACK_HOURS)を履歴CSV(全期間)へ追記・永続化する。

設計:
  - 入力: --source (日次の dns_logs_summary.csv) / --history (累積 dns_history.csv)
  - 重複排除キー: (Datetime(JST), Location, Domain, Decision) の完全一致。
  - 完全バケットのみ採用 [A]:
      日次CSVは取得窓の両端の時間バケットが「部分集計」になる(その窓に入った
      ぶんだけ Count される)。これを履歴に入れると、cron 実行時刻のブレと相まって
      Count が過少なまま固定される。そこで source の最古・最新バケットを除外し、
      丸ごと1時間ぶん揃った完全バケットだけを履歴へ取り込む。
      (fetcher の 26h オーバーラップ取得により、捨てた両端は前日/翌日の中央
       バケットとして必ず補完され、履歴は連続する)
  - Count最大優先マージ [B]:
      同一キーが衝突した場合、Count が大きい方を採用する。万一過去に部分集計が
      混入していても、後日の完全集計(Count大)で自己修復される。
  - 保持期間: --retention-days (デフォルト365)。履歴内の最新日付を基準に、
      それより古い行を削除する。0以下なら無制限。
  - 依存: 標準ライブラリのみ(csv/argparse/datetime/os)。

CSV列構成(reporter.write_csv 準拠):
  Datetime(JST), Location, Domain, Count, Decision
"""
import argparse
import csv
import os
from datetime import datetime, timedelta

HEADER = ["Datetime(JST)", "Location", "Domain", "Count", "Decision"]
DT_FMT = "%Y-%m-%d %H:%M:%S"

# 両端バケット除外を行う最小バケット数。これ未満(低トラフィックで時間帯が
# 1〜2個しかない日)は除外すると履歴に何も残らなくなるため、除外しない。
MIN_BUCKETS_FOR_BOUNDARY_DROP = 3


def _read_csv(path: str) -> "list[dict]":
    """CSVを読み込み行リストを返す。存在しなければ空リスト。"""
    if not os.path.exists(path):
        return []
    rows = []
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
    except (ValueError, KeyError, TypeError):
        return None


def _count(r: dict) -> int:
    """Count を int で返す。空/非数は 0(防御的)。"""
    try:
        return int(str(r.get("Count", "0")).strip() or "0")
    except (ValueError, TypeError):
        return 0


def drop_boundary_buckets(rows: "list[dict]") -> "list[dict]":
    """[A] 取得窓の両端(最古・最新)の時間バケットを除外し、完全集計のみ残す。

    バケット種類数が MIN_BUCKETS_FOR_BOUNDARY_DROP 未満の場合は、除外すると
    履歴に何も残らなくなるため、そのまま返す(低トラフィック保護)。
    """
    valid = [r for r in rows if _parse_dt(r) is not None]
    if not valid:
        return rows
    buckets = sorted({_parse_dt(r) for r in valid})
    if len(buckets) < MIN_BUCKETS_FOR_BOUNDARY_DROP:
        return rows
    lo, hi = buckets[0], buckets[-1]
    return [r for r in rows if _parse_dt(r) not in (lo, hi)]


def merge_history(history_rows: "list[dict]", source_rows: "list[dict]",
                  retention_days: int = 365,
                  drop_boundary: bool = True) -> "tuple[list[dict], dict]":
    """履歴に新規分をマージし、重複排除[B]・保持期間トリムした行リストを返す。

    [A] source は両端バケットを除外してから取り込む(drop_boundary=True 時)。
    [B] 同一キーは Count 最大を採用する(部分集計の自己修復)。

    Returns: (merged_rows, stats)
    """
    dropped_boundary = 0
    if drop_boundary:
        before = len(source_rows)
        source_rows = drop_boundary_buckets(source_rows)
        dropped_boundary = before - len(source_rows)

    # key -> row を保持。衝突時は Count 最大を採用。
    best: "dict[tuple, dict]" = {}

    def _consider(r: dict) -> str:
        """row を取り込み判定。戻り値: "new" / "updated" / "skip"。"""
        if _parse_dt(r) is None:        # 破損行はスキップ
            return "skip"
        k = _key(r)
        if k not in best:
            best[k] = r
            return "new"
        if _count(r) > _count(best[k]):  # より大きい Count(=より完全)で上書き
            best[k] = r
            return "updated"
        return "skip"

    # 1. 既存履歴を取り込む
    for r in history_rows:
        _consider(r)

    # 2. 新規分(source)を取り込む
    added = 0
    updated = 0
    for r in source_rows:
        result = _consider(r)
        if result == "new":
            added += 1
        elif result == "updated":
            updated += 1

    merged = list(best.values())
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
        "dropped_boundary": dropped_boundary,
        "added": added,
        "updated": updated,
        "removed_old": removed_old,
        "total_out": len(merged),
    }
    return merged, stats


def write_history(path: str, rows: "list[dict]") -> None:
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
                    help="日次バッチが出力した直近Nh CSV")
    ap.add_argument("--history", default="history/dns_history.csv",
                    help="累積する履歴CSV")
    ap.add_argument("--retention-days", type=int, default=365,
                    help="保持日数(0以下で無制限)")
    ap.add_argument("--no-drop-boundary", action="store_true",
                    help="両端バケット除外を無効化する(デバッグ/特殊用途)")
    args = ap.parse_args()

    source_rows = _read_csv(args.source)
    if not source_rows:
        print(f"\u26a0\ufe0f No source rows in {args.source}. Nothing to persist.")
        # 履歴が既存なら触らず終了。無ければ空ヘッダだけ作る。
        if not os.path.exists(args.history):
            write_history(args.history, [])
        return

    history_rows = _read_csv(args.history)
    merged, stats = merge_history(
        history_rows, source_rows,
        retention_days=args.retention_days,
        drop_boundary=not args.no_drop_boundary,
    )
    write_history(args.history, merged)

    print("\u2705 History persisted:")
    print(f"   history(before)   : {stats['history_in']:,} rows")
    print(f"   source(new)       : {stats['source_in']:,} rows")
    print(f"   dropped boundary  : {stats['dropped_boundary']:,} rows")
    print(f"   added             : {stats['added']:,} rows")
    print(f"   updated(maxCount) : {stats['updated']:,} rows")
    print(f"   removed(>{args.retention_days}d): {stats['removed_old']:,} rows")
    print(f"   history(after)    : {stats['total_out']:,} rows")


if __name__ == "__main__":
    main()
