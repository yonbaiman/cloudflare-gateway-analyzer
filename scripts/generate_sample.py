import datetime
import random
import os

def generate_sample():
    # 1. 元のコードと同じ時間計算ロジック (JST)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_jst = now_utc + datetime.timedelta(hours=9)
    
    # 24時間の時間軸リストを生成 (HH:00 形式)
    hours_list = [(now_jst - datetime.timedelta(hours=i)).strftime('%H:00') for i in range(23, -1, -1)]
    
    # 2. ダミー統計データの生成
    total_queries = 0
    total_blocks = 0
    hourly_stats = {h: {'allow': 0, 'block': 0} for h in hours_list}
    
    # ダミーロケーションデータ (元のコードのテーブル構造に対応)
    location_data = {
        "Home-Network": {"total": 1240, "block": 45, "top_domain": "doubleclick.net"},
        "Mobile-VPN": {"total": 580, "block": 12, "top_domain": "analytics.google.com"},
        "Office-PC": {"total": 890, "block": 154, "top_domain": "malware-sample.io"}
    }

    # グラフ用データの積み上げ
    for h in hours_list:
        allow = random.randint(50, 200)
        block = random.randint(5, 30)
        hourly_stats[h]['allow'] = allow
        hourly_stats[h]['block'] = block
        total_queries += (allow + block)
        total_blocks += block

    # 3. レポート作成 (元のコードの Markdown 構造を完全再現)
    block_rate = (total_blocks / total_queries * 100) if total_queries > 0 else 0
    
    report = [
        "### 🛡️ Cloudflare Gateway Daily Insights",
        f"**Analyzed Period:** JST `{(now_jst - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M')} ~ {now_jst.strftime('%m-%d %H:%M')}`",
        "",
        "#### 📊 Traffic Overview",
        f"- **Total Queries**: {total_queries:,}",
        f"- **Blocked**: {total_blocks:,} ({block_rate:.1f}%)",
        ""
    ]

    # グラフセクション (xychart-beta)
    x_axis_str = "[" + ", ".join(f'"{h}"' for h in hours_list) + "]"
    allow_data_str = "[" + ", ".join(str(hourly_stats[h]['allow']) for h in hours_list) + "]"
    block_data_str = "[" + ", ".join(str(hourly_stats[h]['block']) for h in hours_list) + "]"

    report.append("#### 📈 24-Hour Query Trends (JST)")
    report.append("```mermaid")
    report.append("xychart-beta")
    report.append('    title "DNS Queries (Allow vs Block)"')
    report.append(f'    x-axis {x_axis_str}')
    report.append('    y-axis "Queries"')
    report.append(f'    bar {allow_data_str}')
    report.append(f'    line {block_data_str}')
    report.append("```")
    report.append("> ※ Bar = Allow, Line = Block  \n")

    # ロケーションInsightsセクション (元のコードのテーブル列を再現)
    report.append("#### 📍 Location Insights")
    report.append("| Location | Total Queries | Blocked | Block Rate | Top Blocked Domain |")
    report.append("| :--- | :---: | :---: | :---: | :--- |")
    
    for loc, stats in location_data.items():
        l_rate = (stats['block'] / stats['total'] * 100)
        report.append(f"| **{loc}** | {stats['total']:,} | {stats['block']:,} | {l_rate:.1f}% | `{stats['top_domain']}` |")
    report.append("\n")

    # 全体の上位ブロックドメイン
    report.append("#### 🚫 Top 10 Blocked Domains (Global)")
    report.append("| Count | Domain |")
    report.append("| :--- | :--- |")
    dummy_domains = [("doubleclick.net", 42), ("adservice.google.com", 38), ("track.evil-analytics.io", 25)]
    for domain, count in dummy_domains:
        report.append(f"| {count:,} | `{domain}` |")

    # 4. 書き出し
    os.makedirs("docs", exist_ok=True)
    with open("docs/sample-report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    print("✅ Verified Sample generated at docs/sample-report.md")

if __name__ == "__main__":
    generate_sample()
