# reporter.py
import csv
import os
from datetime import timedelta


def _build_period_label(stats: dict) -> str:
    """
    Analyzed Period の表示文字列を生成する。

    後方互換:
      - stats に "period" (=(start_date, end_date)) が無い場合は、
        従来どおり「now_jst - 1日 ~ now_jst」(=日次バッチの直近24h) を表示。
      - "period" がある場合(カスタムレポート)は、指定された期間全体を表示。
    """
    period = stats.get("period")
    if period:
        start, end = period
        return (f"**Analyzed Period:** JST "
                f"`{start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}`")
    # 従来動作 (日次バッチ)
    now_jst = stats["now_jst"]
    return (f"**Analyzed Period:** JST "
            f"`{(now_jst - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')} "
            f"~ {now_jst.strftime('%m-%d %H:%M')}`")


def _build_labels(stats: dict) -> tuple[str, str]:
    """
    見出しと Query Trends ラベルを粒度に応じて返す。

    後方互換:
      - "granularity" が無い/"hourly" の場合は従来の "Daily Insights" /
        "24-Hour Query Trends" を維持。
      - "daily" の場合は "Daily Query Trends" に切り替える。
    """
    gran = stats.get("granularity", "hourly")
    heading = "### 🛡️ Cloudflare Gateway Insights"
    if gran == "daily":
        trends = "#### 📈 Daily Query Trends (JST)"
    else:
        trends = "#### 📈 24-Hour Query Trends (JST)"
    return heading, trends


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
    hours_list           = stats["hours_list"]

    block_rate = (total_blocks / total_queries * 100) if total_queries > 0 else 0

    heading, trends_label = _build_labels(stats)

    report = [
        heading,
        _build_period_label(stats),
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
        trends_label,
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
