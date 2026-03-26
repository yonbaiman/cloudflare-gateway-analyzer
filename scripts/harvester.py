import os
import json
import urllib.request
from urllib.error import URLError, HTTPError
from datetime import datetime, timedelta
import csv

def main():
    api_token = os.environ.get('CF_API_TOKEN')
    account_id = os.environ.get('CF_ACCOUNT_ID')

    if not api_token or not account_id:
        print("❌ Error: CF_API_TOKEN or CF_ACCOUNT_ID is not set.")
        exit(1)

    # 取得期間の計算 (UTC基準)
    now_utc = datetime.utcnow()
    start_time = (now_utc - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    end_time = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    print(f"🔍 Fetching data from {start_time} to {end_time}...")

    query = {
        "query": """
        query {
          viewer {
            accounts(filter: {accountTag: "%s"}) {
              gatewayResolverQueriesAdaptiveGroups(
                limit: 10000, 
                filter: {datetime_geq: "%s", datetime_leq: "%s"},
                orderBy: [datetime_DESC]
              ) {
                dimensions {
                  datetime
                  locationName
                  queryName
                  resolverDecision
                }
                count
              }
            }
          }
        }
        """ % (account_id, start_time, end_time)
    }

    url = "https://api.cloudflare.com/client/v4/graphql"
    req = urllib.request.Request(url, data=json.dumps(query).encode('utf-8'), method='POST')
    req.add_header('Authorization', f'Bearer {api_token}')
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req) as res:
            response_data = json.loads(res.read().decode('utf-8'))
    except HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        exit(1)
    except URLError as e:
        print(f"❌ URL Error: {e.reason}")
        exit(1)

    try:
        logs = response_data['data']['viewer']['accounts'][0]['gatewayResolverQueriesAdaptiveGroups']
    except (KeyError, IndexError):
        logs = []

    if not logs:
        write_summary("### 🛡️ Cloudflare Gateway Daily Insights\n\nNo queries found in the last 24 hours.")
        print("✅ No data found.")
        return

    # === 集計用の初期化 ===
    now_jst = now_utc + timedelta(hours=9)
    
    # グラフ用: 直近24時間の「時間(HH:00)」リストを作成 (JST)
    hours_list = [(now_jst - timedelta(hours=i)).strftime('%H:00') for i in range(23, -1, -1)]
    hourly_stats = {h: {'allow': 0, 'block': 0} for h in hours_list}
    
    location_stats = {}
    total_queries = 0
    total_blocks = 0
    global_domain_blocks = {}
    csv_rows = []

    # === データのパースと集計 ===
    for item in logs:
        utc_dt_str = item['dimensions'].get('datetime', '')
        count = item['count']
        domain = item['dimensions']['queryName']
        loc = item['dimensions'].get('locationName', 'Unknown')
        decision = item['dimensions']['resolverDecision']
        
        # 判定 (2, 3, 6, 9 がブロックポリシー・セーフサーチ等による遮断)
        is_block = decision in [2, 3, 6, 9]
        decision_str = "Block" if is_block else "Allow"

        total_queries += count
        if is_block:
            total_blocks += count
            global_domain_blocks[domain] = global_domain_blocks.get(domain, 0) + count

        # JST時間の計算と、グラフ用の時間別集計
        jst_dt_display = "Unknown"
        if utc_dt_str:
            try:
                utc_dt = datetime.strptime(utc_dt_str, '%Y-%m-%dT%H:%M:%SZ')
                jst_dt = utc_dt + timedelta(hours=9)
                jst_dt_display = jst_dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # グラフバケット用の丸め処理
                hour_key = jst_dt.strftime('%H:00')
                if hour_key in hourly_stats:
                    if is_block:
                        hourly_stats[hour_key]['block'] += count
                    else:
                        hourly_stats[hour_key]['allow'] += count
            except ValueError:
                pass

        # ロケーション別集計
        if loc not in location_stats:
            location_stats[loc] = {'total': 0, 'block': 0, 'domains': {}}
        
        location_stats[loc]['total'] += count
        if is_block:
            location_stats[loc]['block'] += count
            location_stats[loc]['domains'][domain] = location_stats[loc]['domains'].get(domain, 0) + count

        # CSV出力用データ
        csv_rows.append([jst_dt_display, loc, domain, count, decision_str])

    # === Markdownレポートの作成 ===
    block_rate = (total_blocks / total_queries * 100) if total_queries > 0 else 0

    report = [
        "### 🛡️ Cloudflare Gateway Daily Insights",
        f"**Analyzed Period:** JST `{(now_jst - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')} ~ {now_jst.strftime('%m-%d %H:%M')}`",
        "",
        "#### 📊 Traffic Overview",
        f"- **Total Queries**: {total_queries:,}",
        f"- **Blocked**: {total_blocks:,} ({block_rate:.1f}%)",
        ""
    ]

    # 1. グラフセクション (Mermaid.js xychart-beta)
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

    # 2. ロケーション別分析セクション
    report.append("#### 📍 Location Insights")
    report.append("| Location | Total Queries | Blocked | Block Rate | Top Blocked Domain |")
    report.append("| :--- | :---: | :---: | :---: | :--- |")
    
    # 総クエリ数が多い順にソートしてテーブル化
    sorted_locs = sorted(location_stats.items(), key=lambda x: x[1]['total'], reverse=True)
    for loc, stats in sorted_locs:
        l_total = stats['total']
        l_block = stats['block']
        l_rate = (l_block / l_total * 100) if l_total > 0 else 0
        
        top_domain = "None"
        if stats['domains']:
            top_domain = sorted(stats['domains'].items(), key=lambda x: x[1], reverse=True)[0][0]
            top_domain = f"`{top_domain}`"
            
        report.append(f"| **{loc}** | {l_total:,} | {l_block:,} | {l_rate:.1f}% | {top_domain} |")
    report.append("\n")

    # 3. 全体の上位ブロックドメイン
    report.append("#### 🚫 Top 10 Blocked Domains (Global)")
    report.append("| Count | Domain |")
    report.append("| :--- | :--- |")
    
    top_global_blocked = sorted(global_domain_blocks.items(), key=lambda x: x[1], reverse=True)[:10]
    if top_global_blocked:
        for domain, count in top_global_blocked:
            report.append(f"| {count:,} | `{domain}` |")
    else:
        report.append("| 0 | No blocked domains |")

    write_summary("\n".join(report))
    
    # === CSVの出力 (変更なし) ===
    csv_filename = "dns_logs_summary.csv"
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Datetime(JST)', 'Location', 'Domain', 'Count', 'Decision'])
            writer.writerows(csv_rows)
        print(f"✅ CSV saved as {csv_filename}")
    except Exception as e:
        print(f"❌ Failed to write CSV: {e}")

    print("✅ Report generated successfully!")

def write_summary(markdown_content):
    summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(markdown_content + "\n")
    else:
        # ローカル実行時のデバッグ用
        print(markdown_content)

if __name__ == "__main__":
    main()
