import datetime
import random
import os

def generate_sample():
    # 1. 日本時間の現在日付を取得 (JST)
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    date_str = now.strftime("%Y-%m-%d")

    # 2. ダミーデータの生成 (24時間分)
    hours = [f"{h}h" for h in range(24)]
    # 本物に近い挙動: 日中はクエリが多く、夜間は少ない
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

    # 4. Markdown の構築 (analyze summary.pdf のレイアウトを再現)
    md = f"""# Cloudflare Gateway Daily Insights 🛡️

> **Report Date:** {date_str} (JST)  
> *This is an automatically generated sample report using anonymized data.*

## 📈 DNS Queries Timeline (UTC)
```mermaid
xychart-beta
    title "24-Hour Traffic Trend (Allow vs Block)"
    x-axis {str(hours).replace("'", '"')}
    y-axis "Number of Queries"
    bar {allow_data}
    line {block_data}
