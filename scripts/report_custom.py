# report_custom.py … workflow_dispatch / CLI 共用の入口
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from datetime import date
from query import load_history_csv, filter_rows, pick_granularity
from analyzer import analyze_rows          # ← 既存analyze_logsをCSV行対応に薄く拡張
from reporter import build_markdown_report, write_summary

def main():
    start = date.fromisoformat(os.environ["INPUT_START"])
    end   = date.fromisoformat(os.environ["INPUT_END"])
    loc   = os.environ.get("INPUT_LOCATION") or None
    gran  = pick_granularity(start, end, os.environ.get("INPUT_GRAN", "auto"))

    rows  = filter_rows(load_history_csv(), start, end, loc)
    if not rows:
        write_summary(f"### 🔎 No data for {start}〜{end}"
                      + (f" / location={loc}" if loc else ""))
        return

    stats = analyze_rows(rows, granularity=gran, start=start, end=end)
    markdown, _ = build_markdown_report(stats)
    write_summary(f"### 🔎 Custom Report `{start} 〜 {end}`"
                  + (f" / 📍`{loc}`" if loc else " / 📍All") + "<br><br>" + markdown)

if __name__ == "__main__":
    main()
