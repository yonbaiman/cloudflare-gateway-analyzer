import datetime
import random
import os

def generate_sample():
    # 1. 日本時間の現在日付を取得 (JST)
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    date_str = now.strftime("%Y-%m-%d")

    # 2. ダミーデータの生成 (24時間分)
    hours = [f"{h}h" for h in range(24)]
    allow_data = [random.randint(20, 50) if 0 <= i <= 6 else random.randint(100, 300) for i in range(24)]
    block_data = [random.randint(0, 5) if 0 <= i <= 6 else random.randint(5, 20) for i in range(24)]

    # 3. ダミーのドメインとロケーション
    top_blocked = [
        ("ads.example.com", 154),
        ("tracker.generic-analytics.net", 98),
        ("malicious-sample.io", 45),
        ("social-telemetry.co", 32),
        ("api.metrics-dummy.org", 12)
    ]
    
    locations = [
        ("Device A (Tokyo)", 1250, "62.5%"),
        ("Device B (Osaka)", 500, "25.0%"),
        ("Device C (Mobile)", 250, "12.5%")
    ]

    # 4. Markdown の構築
    # f-string の中でのバックティック競合を避けるため、パーツごとに結合します
    header = f"# Cloudflare Gateway Daily Insights 🛡️\n\n"
    header += f"> **Report Date:** {date_str} (JST)  \n"
    header += f"> *This is an automatically generated sample report using anonymized data.*\n\n"

    # Mermaid グラフセクション (バックティックを安全に扱うため f-string を分離)
    mermaid_section = "## 📈 DNS Queries Timeline (UTC)\n"
    mermaid_section += "```mermaid\n"
    mermaid_section += "xychart-beta\n"
    mermaid_section += "    title \"24-Hour Traffic Trend (Allow vs Block)\"\n"
    mermaid_section += f"    x-axis {str(hours).replace(\"'\", '\"')}\n"
    mermaid_section += "    y-axis \"Number of Queries\"\n"
    mermaid_section += f"    bar {allow_data}\n"
    mermaid_section += f"    line {block_data}\n"
    mermaid_section += "```\n"
    mermaid_section += "*Graph: 🟦 Bars = Allowed Queries, 🟥 Line = Blocked Queries*\n\n---\n\n"

    # テーブルセクション
    table_blocked = "## 🚫 Top Blocked Domains (Top 5)\n"
    table_blocked += "| Rank | Domain | Count |\n| :--- | :--- | :--- |\n"
    for i, (domain, count) in enumerate(top_blocked, 1):
        table_blocked += f"| {i} | `{domain}` | {count} |\n"
    table_blocked += "\n---\n\n"

    table_location = "## 📍 Statistics by Location (Source)\n"
    table_location += "| Location / Device | Total Queries | Share (%) |\n| :--- | :--- | :--- |\n"
    for loc, count, share in locations:
        table_location += f"| {loc} | {count} | {share} |\n"

    footer = "\n---\n## 📦 Artifacts\n"
    footer += f"- [ ] `dns-analytics-csv-{date_str}.zip` (Sample data only)\n\n"
    footer += "---\n**Developed by [yonbaiman](https://github.com/yonbaiman) / [yonbaiman.cc](https://yonbaiman.cc)**\n"

    # 全てを結合
    full_markdown = header + mermaid_section + table_blocked + table_location + footer

    # 5. ファイルへの書き出し
    os.makedirs("docs", exist_ok=True)
    with open("docs/sample-report.md", "w", encoding="utf-8") as f:
        f.write(full_markdown)
    
    print(f"✅ Successfully generated: docs/sample-report.md")

if __name__ == "__main__":
    generate_sample()
