# analyzer.py
from datetime import datetime, timedelta, UTC

# resolverDecision の数値定数
# 出典: Cloudflare GraphQL API スキーマ イントロスペクション (2026-04-27 確認)
# AccountGatewayResolverQueriesAdaptiveGroupsDimensions.resolverDecision description より
RESOLVER_DECISIONS = {
    0:  "Unknown",   # unknown
    1:  "Allow",     # allowedByQueryName
    2:  "Block",     # blockedByQueryName
    3:  "Block",     # blockedByCategory
    4:  "Allow",     # allowedOnNoLocation
    5:  "Allow",     # allowedOnNoPolicyMatch
    6:  "Block",     # blockedAlwaysCategory
    7:  "Override",  # overrideForSafeSearch
    8:  "Override",  # overrideApplied
    9:  "Block",     # blockedRule
    10: "Allow",     # allowedRule
}

BLOCK_DECISIONS = frozenset({2, 3, 6, 9})


def analyze_logs(logs: list) -> dict:
    """
    ログリストを受け取り、集計結果をまとめた辞書を返す。

    Returns:
        {
            "total_queries": int,
            "total_blocks": int,
            "hourly_stats": dict,          # {"09:00": {"allow": N, "block": N}, ...}
            "location_stats": dict,        # ロケーション別統計
            "global_domain_blocks": dict,  # ドメイン別ブロック数
            "csv_rows": list,              # CSV出力用の行リスト
            "now_jst": datetime,
            "hours_list": list,
        }
    """
    now_utc  = datetime.now(UTC)
    now_jst  = now_utc + timedelta(hours=9)

    hours_list = [
        (now_jst - timedelta(hours=i)).strftime('%H:00')
        for i in range(23, -1, -1)
    ]
    hourly_stats = {h: {'allow': 0, 'block': 0} for h in hours_list}

    location_stats       = {}
    total_queries        = 0
    total_blocks         = 0
    global_domain_blocks = {}
    csv_rows             = []

    for item in logs:
        utc_dt_str = item['dimensions'].get('datetime', '')
        count      = item['count']
        domain     = item['dimensions']['queryName']
        loc        = item['dimensions'].get('locationName', 'Unknown')
        decision   = item['dimensions']['resolverDecision']

        is_block     = decision in BLOCK_DECISIONS
        decision_str = RESOLVER_DECISIONS.get(decision, f"Unknown({decision})")

        total_queries += count
        if is_block:
            total_blocks += count
            global_domain_blocks[domain] = global_domain_blocks.get(domain, 0) + count

        jst_dt_display = "Unknown"
        if utc_dt_str:
            try:
                utc_dt = datetime.strptime(utc_dt_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=UTC)
                jst_dt = utc_dt + timedelta(hours=9)
                jst_dt_display = jst_dt.strftime('%Y-%m-%d %H:%M:%S')

                hour_key = jst_dt.strftime('%H:00')
                if hour_key in hourly_stats:
                    if is_block:
                        hourly_stats[hour_key]['block'] += count
                    else:
                        hourly_stats[hour_key]['allow'] += count
            except ValueError:
                pass

        if loc not in location_stats:
            location_stats[loc] = {'total': 0, 'block': 0, 'domains': {}}

        location_stats[loc]['total'] += count
        if is_block:
            location_stats[loc]['block'] += count
            location_stats[loc]['domains'][domain] = (
                location_stats[loc]['domains'].get(domain, 0) + count
            )

        csv_rows.append([jst_dt_display, loc, domain, count, decision_str])

    return {
        "total_queries":        total_queries,
        "total_blocks":         total_blocks,
        "hourly_stats":         hourly_stats,
        "location_stats":       location_stats,
        "global_domain_blocks": global_domain_blocks,
        "csv_rows":             csv_rows,
        "now_jst":              now_jst,
        "hours_list":           hours_list,
    }
