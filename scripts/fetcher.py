# fetcher.py
import json
import math
import urllib.request
from urllib.error import URLError, HTTPError
from datetime import datetime, timedelta, UTC

# === 取得窓の設定 ===
# LOOKBACK_HOURS: さかのぼる時間。24h固定だと GitHub Actions の cron 実行時刻の
#   ブレ(毎日数分〜数十分ズレる)により、日跨ぎ境界でギャップ(欠損)/オーバーラップ
#   (重複)が発生する。前日と 2h オーバーラップさせることで、persist_history 側の
#   「完全バケットのみ採用」と組み合わせ、履歴を過不足なく連続させる。
#   余剰なオーバーラップ分は履歴側の重複排除で吸収される。
LOOKBACK_HOURS = 26
# BATCH_HOURS: 1バッチあたりの取得時間幅。limit:10000 を 6h 単位で維持する。
BATCH_HOURS = 6

# Cloudflare GraphQL エンドポイント
CF_GRAPHQL_URL = "https://api.cloudflare.com/client/v4/graphql"
# urlopen のタイムアウト(秒)。未設定だと API 無応答時にハングするため明示する。
REQUEST_TIMEOUT = 30

GRAPHQL_QUERY = """
query($accountTag: String!, $start: Time!, $end: Time!) {
  viewer {
    accounts(filter: {accountTag: $accountTag}) {
      gatewayResolverQueriesAdaptiveGroups(
        limit: 10000,
        filter: {FILTER_PLACEHOLDER},
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
"""


def _build_batches(now_utc):
    """[now-LOOKBACK_HOURS, now] を BATCH_HOURS 刻みで分割する。

    各バッチの上端は、最新バッチ(i=0)のみ datetime_leq(now を含む)、
    それ以外は datetime_lt とする。これにより隣接バッチの境界バケットが
    両方に含まれる二重カウントを防ぐ(下側 geq 包含・上側 lt 排他)。

    Returns: [(start_iso, end_iso, end_op), ...]  end_op は "leq" か "lt"。
    """
    n = math.ceil(LOOKBACK_HOURS / BATCH_HOURS)
    batches = []
    for i in range(n):
        e_diff = i * BATCH_HOURS
        # 最古バッチは LOOKBACK_HOURS ちょうどで切る(端数調整)
        s_diff = min((i + 1) * BATCH_HOURS, LOOKBACK_HOURS)
        start = now_utc - timedelta(hours=s_diff)
        end = now_utc - timedelta(hours=e_diff)
        end_op = "leq" if i == 0 else "lt"
        batches.append((
            start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            end.strftime('%Y-%m-%dT%H:%M:%SZ'),
            end_op,
        ))
    return batches


def fetch_all_logs(api_token: str, account_id: str) -> list:
    """直近 LOOKBACK_HOURS のログを BATCH_HOURS 刻みのバッチで取得して返す。"""
    all_logs = []
    now_utc = datetime.now(UTC)

    for start_time, end_time, end_op in _build_batches(now_utc):
        print(f"\U0001f50d Fetching {start_time} to {end_time} (datetime_{end_op})...")

        # バッチ境界の二重カウントを避けるため、上端の演算子(leq/lt)を切り替える
        filter_expr = f"datetime_geq: $start, datetime_{end_op}: $end"
        query = {
            "query": GRAPHQL_QUERY.replace("FILTER_PLACEHOLDER", filter_expr),
            "variables": {
                "accountTag": account_id,
                "start": start_time,
                "end": end_time,
            }
        }

        req = urllib.request.Request(
            CF_GRAPHQL_URL,
            data=json.dumps(query).encode('utf-8'),
            method='POST'
        )
        req.add_header('Authorization', f'Bearer {api_token}')
        req.add_header('Content-Type', 'application/json')

        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as res:
                response_data = json.loads(res.read().decode('utf-8'))
                batch_logs = (
                    response_data['data']['viewer']['accounts'][0]
                    ['gatewayResolverQueriesAdaptiveGroups']
                )
                all_logs.extend(batch_logs)
                print(f"   -> Found {len(batch_logs)} entries")
        except (HTTPError, URLError, KeyError, IndexError, TimeoutError) as e:
            print(f"   \u26a0\ufe0f Warning/Error in this batch: {e}")
            continue

    return all_logs
