# fetcher.py
import json
import urllib.request
from urllib.error import URLError, HTTPError
from datetime import datetime, timedelta, UTC


def fetch_all_logs(api_token: str, account_id: str) -> list:
    """24時間分のログを6時間×4バッチで取得して返す"""
    all_logs = []
    now_utc = datetime.now(UTC)

    for i in range(4):
        s_diff = (i + 1) * 6
        e_diff = i * 6
        start_time = (now_utc - timedelta(hours=s_diff)).strftime('%Y-%m-%dT%H:%M:%SZ')
        end_time   = (now_utc - timedelta(hours=e_diff)).strftime('%Y-%m-%dT%H:%M:%SZ')

        print(f"🔍 Fetching {start_time} to {end_time}...")

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
        req = urllib.request.Request(
            url,
            data=json.dumps(query).encode('utf-8'),
            method='POST'
        )
        req.add_header('Authorization', f'Bearer {api_token}')
        req.add_header('Content-Type', 'application/json')

        try:
            with urllib.request.urlopen(req) as res:
                response_data = json.loads(res.read().decode('utf-8'))
                batch_logs = (
                    response_data['data']['viewer']['accounts'][0]
                    ['gatewayResolverQueriesAdaptiveGroups']
                )
                all_logs.extend(batch_logs)
                print(f"   -> Found {len(batch_logs)} entries")
        except (HTTPError, URLError, KeyError, IndexError) as e:
            print(f"   ⚠️ Warning/Error in this batch: {e}")
            continue

    return all_logs
