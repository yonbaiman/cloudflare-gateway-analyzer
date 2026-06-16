# scripts/report_custom.py
"""workflow_dispatch / CLI 共用の「期間・ロケーション指定」レポート入口。

データソースは蓄積CSV(history/dns_history.csv)。
無料枠APIは直近24hしか返さないため、過去の期間指定には蓄積CSVが前提。

環境変数(workflow_dispatch経由):
    INPUT_START    開始日 YYYY-MM-DD (JST)
    INPUT_END      終了日 YYYY-MM-DD (JST, 当日を含む)
    INPUT_LOCATION ロケーション名(空欄=全て)
    INPUT_GRAN     'auto' | 'hourly' | 'daily'
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

from query import load_history_csv, filter_rows, pick_granularity
from analyzer_custom import analyze_rows
from reporter import build_markdown_report, write_summary, write_csv


def _get_params():
    """環境変数 or CLI引数から (start, end, location, gran) を取得。"""
    # CLI: report_custom.py 2026-06-01 2026-06-07 [location] [gran]
    if len(sys.argv) >= 3:
        start = date.fromisoformat(sys.argv[1])
        end = date.fromisoformat(sys.argv[2])
        loc = sys.argv[3] if len(sys.argv) >= 4 and sys.argv[3] else None
        gran = sys.argv[4] if len(sys.argv) >= 5 else "auto"
    else:
        start = date.fromisoformat(os.environ["INPUT_START"])
        end = date.fromisoformat(os.environ["INPUT_END"])
        loc = os.environ.get("INPUT_LOCATION") or None
        gran = os.environ.get("INPUT_GRAN", "auto")
    return start, end, loc, gran


def main():
    start, end, loc, gran_mode = _get_params()

    if end < start:
        print("❌ Error: end_date is before start_date.")
        sys.exit(1)

    gran = pick_granularity(start, end, gran_mode)
    rows = filter_rows(load_history_csv(), start, end, loc)

    loc_label = f" / 📍`{loc}`" if loc else " / 📍All"
    header = f"### 🔎 Custom Report `{start} 〜 {end}`{loc_label} (granularity: {gran})"

    if not rows:
        write_summary(f"{header}\n\nNo data found for the specified conditions.")
        print("✅ No data found for the specified conditions.")
        return

    stats = analyze_rows(rows, gran, start, end)
    markdown, _top_domains = build_markdown_report(stats)
    write_summary(f"{header}\n\n{markdown}")
    write_csv(stats["csv_rows"], filename="custom_report.csv")
    print("✅ Custom report generated successfully!")


if __name__ == "__main__":
    main()
