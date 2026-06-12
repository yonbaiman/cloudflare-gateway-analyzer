# scripts/analyzer_custom.py
"""粒度可変(hourly/daily)の集計エンジン。

既存 analyzer.analyze_logs は「直近24時間・hourly固定」のため、
期間指定レポート用に粒度可変版を別関数として用意する。
戻り値の dict は既存 reporter.build_markdown_report がそのまま使える構造。
"""
from datetime import datetime, date, timedelta

# ブロック扱いとする Decision ラベル(reporter.write_csv が出力する文字列ベース)。
# 注: 既存 analyzer の RESOLVER_DECISIONS で Block に分類されたものが
#     CSV では "Block" として記録されているため、ここでは文字列で判定する。
BLOCK_LABELS = frozenset({"Block"})


def analyze_rows(rows: list[dict], granularity: str,
                 start: date, end: date) -> dict:
    """フィルタ済み行を粒度可変で集計し、reporter が使う stats dict を返す。

    granularity: 'hourly' (時間軸=HH:00, 単日想定) / 'daily' (時間軸=MM-DD)
    """
    if granularity == "hourly":
        time_axis = [f"{h:02d}:00" for h in range(24)]
        def bucket(dt: datetime) -> str:
            return dt.strftime("%H:00")
    else:  # daily
        days = (end - start).days
        time_axis = [(start + timedelta(days=i)).strftime("%m-%d")
                     for i in range(days + 1)]
        def bucket(dt: datetime) -> str:
            return dt.strftime("%m-%d")

    series = {t: {"allow": 0, "block": 0} for t in time_axis}
    location_stats: dict = {}
    global_domain_blocks: dict = {}
    csv_rows: list = []
    total_queries = 0
    total_blocks = 0

    for r in rows:
        cnt, dom, loc, dec = r["count"], r["domain"], r["location"], r["decision"]
        is_block = dec in BLOCK_LABELS

        total_queries += cnt
        if is_block:
            total_blocks += cnt
            global_domain_blocks[dom] = global_domain_blocks.get(dom, 0) + cnt

        key = bucket(r["dt"])
        if key in series:
            series[key]["block" if is_block else "allow"] += cnt

        if loc not in location_stats:
            location_stats[loc] = {"total": 0, "block": 0, "domains": {}}
        location_stats[loc]["total"] += cnt
        if is_block:
            location_stats[loc]["block"] += cnt
            location_stats[loc]["domains"][dom] = (
                location_stats[loc]["domains"].get(dom, 0) + cnt
            )

        csv_rows.append([
            r["dt"].strftime("%Y-%m-%d %H:%M:%S"), loc, dom, cnt, dec
        ])

    return {
        "total_queries": total_queries,
        "total_blocks": total_blocks,
        "hourly_stats": series,          # 既存 reporter のキー名を流用(中身は粒度可変)
        "location_stats": location_stats,
        "global_domain_blocks": global_domain_blocks,
        "csv_rows": csv_rows,
        "now_jst": datetime(end.year, end.month, end.day, 23, 59),
        "hours_list": time_axis,         # 既存 reporter の x 軸キー名を流用
        "granularity": granularity,
        "period": (start, end),
    }
