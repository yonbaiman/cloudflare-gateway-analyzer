# reporter.py
import csv
import os
from datetime import timedelta


def build_markdown_report(stats: dict) -> tuple[str, list]:
    """
    集計結果からMarkdownレポートを生成する。

    Returns:
        (markdown_text, top_domains_for_discord)
    """
    total_queries        = stats["total_queries"]
    total_blocks         = stats["total_blocks"]
    hourly_stats         = stats["hourly_stats"]
    location_stats       = stats["location_stats"]
    global_domain_blocks = stats["global_domain_blocks"]
    now_jst              = stats["now_jst"]
    hours_list           = stats["hours_list"]

    block_rate = (total_blocks / total_queries * 100) if total_queries > 0 else 0

    report = [
        "### 🛡️ Cloudflare Gateway Daily Insights",
        f"**Analyzed Period:** JST `{(now_jst - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')} ~ {now_jst.strftime('%m-%d %H:%M')}`",
        "",
        "#### 📊 Traffic Overview",
        f"- **Total Queries**: {total_queries:,}",
        f"- **Blocked**: {total_blocks:,} ({block_rate:.1f}%)",
        "",
    ]

    # Mermaid チャート
    x_axis_str    = "[" + ", ".join(f'"{h}"' for h in hours_list) + "]"
    allow_data_str = "[" + ", ".join(str(hourly_stats[h]['allow']) for h in hours_list) + "]"
    block_data_str = "[" + ", ".join(str(hourly_stats[h]['block']) for h in hours_list) + "]"

    report += [
        "#### 📈 24-Hour Query Trends (JST)",
        "```mermaid",
        "xychart-beta",
        '    title "DNS Queries (Allow vs Block)"',
        f'    x-axis {x_axis_str}',
        '    y-axis "Queries"',
        f'    bar {allow_data_str}',
        f'    line {block_data_str}',
        "```",
        "> ※ Bar = Allow, Line = Block  \n",
    ]

    # ロケーション別テーブル
    report += [
        "#### 📍 Location Insights",
        "| Location | Total Queries | Blocked | Block Rate | Top Blocked Domain |",
        "| :--- | :---: | :---: | :---: | :--- |",
    ]
    for loc, s in sorted(location_stats.items(), key=lambda x: x[1]['total'], reverse=True):
        l_total = s['total']
        l_block = s['block']
        l_rate  = (l_block / l_total * 100) if l_total > 0 else 0
        top_domain = "None"
        if s['domains']:
            top_domain = f"`{sorted(s['domains'].items(), key=lambda x: x[1], reverse=True)[0][0]}`"
        report.append(f"| **{loc}** | {l_total:,} | {l_block:,} | {l_rate:.1f}% | {top_domain} |")
    report.append("\n")

    # グローバルトップブロックドメイン
    report += [
        "#### 🚫 Top 10 Blocked Domains (Global)",
        "| Count | Domain |",
        "| :--- | :--- |",
    ]
    top_global_blocked     = sorted(global_domain_blocks.items(), key=lambda x: x[1], reverse=True)[:10]
    top_domains_for_discord = []

    if top_global_blocked:
        for domain, count in top_global_blocked:
            report.append(f"| {count:,} | `{domain}` |")
            top_domains_for_discord.append(f"{domain} ({count:,})")
    else:
        report.append("| 0 | No blocked domains |")

    return "\n".join(report), top_domains_for_discord


def write_summary(markdown_content: str) -> None:
    """GitHub Step Summary またはコンソールへ出力する"""
    summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(markdown_content + "\n")
    else:
        print(markdown_content)


def write_csv(csv_rows: list, filename: str = "dns_logs_summary.csv") -> None:
    """CSVファイルに集計データを書き出す"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Datetime(JST)', 'Location', 'Domain', 'Count', 'Decision'])
            writer.writerows(csv_rows)
        print(f"✅ CSV saved as {filename}")
    except Exception as e:
        print(f"❌ Failed to write CSV: {e}")
