# scripts/harvester.py
import os
import sys

# scripts/ ディレクトリをパスに追加（同階層モジュールを確実に読み込む）
sys.path.insert(0, os.path.dirname(__file__))

from fetcher  import fetch_all_logs
from analyzer import analyze_logs
from reporter import build_markdown_report, write_summary, write_csv
from notifier import send_discord_alert


def main():
    api_token  = os.environ.get('CF_API_TOKEN')
    account_id = os.environ.get('CF_ACCOUNT_ID')

    if not api_token or not account_id:
        print("❌ Error: CF_API_TOKEN or CF_ACCOUNT_ID is not set.")
        exit(1)

    # 1. データ取得
    logs = fetch_all_logs(api_token, account_id)

    if not logs:
        write_summary("### 🛡️ Cloudflare Gateway Daily Insights\n\nNo queries found in the last 24 hours.")
        print("✅ No data found.")
        return

    # 2. 集計
    stats = analyze_logs(logs)

    # 3. レポート生成・出力
    markdown, top_domains = build_markdown_report(stats)
    write_summary(markdown)
    write_csv(stats["csv_rows"])

    print("✅ Report generated successfully!")

    # 4. Discord通知
    send_discord_alert(stats["total_queries"], stats["total_blocks"], top_domains)


if __name__ == "__main__":
    main()
