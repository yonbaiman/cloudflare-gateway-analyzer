# notifier.py
import json
import os
import urllib.request
from datetime import datetime, timedelta, UTC


def send_discord_alert(total_queries: int, blocked_count: int, top_domains: list) -> None:
    """Discordへ解析結果のサマリーを送信する"""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ DISCORD_WEBHOOK_URL が設定されていません。通知をスキップします。")
        return

    block_rate = (blocked_count / total_queries * 100) if total_queries > 0 else 0
    now_jst    = datetime.now(UTC) + timedelta(hours=9)
    date_str   = now_jst.strftime("%Y-%m-%d")

    domain_list_str = "\n".join(top_domains) if top_domains else "None"
    domains_value   = f"```text\n{domain_list_str}\n```"

    footer_text = (
        "Secured by 1Password Secrets Automation"
        if os.environ.get("OP_SERVICE_ACCOUNT_TOKEN")
        else "Cloudflare Gateway Analyzer"
    )

    payload = {
        "username": "Cloudflare Gateway Analyzer",
        "embeds": [{
            "title": "🛡️ Daily Security Insights",
            "description": f"**Date:** {date_str}\nCloudflare Gateway のログ解析が完了しました。",
            "color": 3447003,
            "fields": [
                {"name": "📊 Total Queries", "value": f"`{total_queries:,}`",                         "inline": True},
                {"name": "🚫 Blocked",        "value": f"`{blocked_count:,}` ({block_rate:.1f}%)",    "inline": True},
                {"name": "🔝 Top Blocked Domains", "value": domains_value,                            "inline": False},
            ],
            "footer": {"text": footer_text},
        }]
    }

    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode('utf-8'),
        method='POST'
    )
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'Cloudflare-Gateway-Analyzer')

    try:
        with urllib.request.urlopen(req) as _:
            print("✅ Discord通知の送信に成功しました！")
    except Exception as e:
        print(f"❌ Discord通知の送信に失敗しました: {e}")
