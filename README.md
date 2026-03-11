# Cloudflare Gateway Log Analyzer 🛡️

[![GitHub License](https://img.shields.io/github/license/yonbaiman/cloudflare-gateway-analyzer)](https://github.com/yonbaiman/cloudflare-gateway-analyzer/blob/main/LICENSE)
[![Node.js Version](https://img.shields.io/badge/Node.js-24-blue?logo=node.js)](https://github.com/yonbaiman/private-dns-monitor)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://github.com/yonbaiman/cloudflare-gateway-analyzer)

A lightweight, automated analytics tool for Cloudflare Zero Trust (Free Tier) users. Generates professional-grade security reports with interactive charts and device-level insights.
Cloudflare Zero Trust (無料プラン) ユーザー向けの、軽量で自動化された解析ツールです。プロフェッショナルなセキュリティレポート、推移グラフ、デバイス別の詳細分析を自動生成します。

---

## 🌟 Key Features / 主な機能

- **📊 24-Hour Query Trends (JST)**: Visualizes allowed vs. blocked queries over 24 hours using Mermaid.js. 
  (24時間の許可/ブロック推移をMermaid.jsで視覚化)
- **📍 Location (Device) Insights**: Identifies which devices are triggering blocks and tracks their top blocked domains.
  (どのデバイスがブロックされているか、その主な原因ドメインを特定)
- **🚀 Zero Dependencies**: Pure Python script. No `pandas`, no `requests`. Extremely fast and secure.
  (標準ライブラリのみで動作。非常に高速でセキュアな設計)
- **🧹 Auto-Cleanup**: Detailed logs (CSV) are stored as artifacts and automatically deleted after 7 days.
  (詳細ログはCSVとして保存され、7日後に自動消去)

---

## 🔒 Security First: Two-Repo Architecture / セキュリティ設計

DNS logs contain sensitive browsing history. To protect your privacy, this tool uses a **separated execution model**.
DNSログには機微な情報が含まれるため、本ツールは「公開」と「実行」を分けた分離アーキテクチャを採用しています。

1.  **Public Repo (This one)**: Manages the core analysis logic. No personal data.
    (このリポジトリ。解析ロジックのみを管理し、個人データは含みません。)
2.  **Private Repo (Yours)**: A private repository for execution. Stores your Secrets and generates reports.
    (あなたが作成する非公開リポジトリ。設定を保存し、解析結果を自分だけに表示します。)

---

## 🚀 Getting Started / セットアップ手順

### 1. Prepare Cloudflare / Cloudflareでの準備
Get these values from your Cloudflare dashboard: / ダッシュボードから以下の値を取得します。

- **`CLOUDFLARE_API_TOKEN`**: Create a token with `Account > Cloudflare Zero Trust > Read` permissions.
  ([APIトークン画面](https://dash.cloudflare.com/profile/api-tokens)で、Zero Trustの読取り権限を持つトークンを作成)
- **`CLOUDFLARE_ACCOUNT_ID`**: Found in your dashboard sidebar.
  (ダッシュボードのサイドバーにある「アカウント ID」をコピー)

### 2. Setup Private Repo / 実行用リポジトリの作成
1. Create a new **Private** GitHub repository. (新しい **非公開** リポジトリを作成)
2. Go to `Settings > Secrets and variables > Actions` and register the secrets above.
   (リポジトリのSecretsに、上記2つの値を登録)

### 3. Create Workflow / ワークフローの作成
Add `.github/workflows/monitor.yml` to your private repo:
(非公開リポジトリに以下のファイルを作成して貼り付けます)

```yaml
name: Private DNS Monitor
on:
  schedule:
    - cron: '0 23 * * *' # 08:00 JST
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Core Logic
        uses: actions/checkout@v6
        with:
          repository: 'yonbaiman/cloudflare-gateway-analyzer' # 👈 Calls this repo
          
      - name: Setup Python
        uses: actions/setup-python@v6
        with:
          python-version: '3.12'

      - name: Run Harvester
        env:
          CF_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CF_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
        run: python scripts/harvester.py

      - name: Save Secure Logs
        uses: actions/upload-artifact@v7
        with:
          name: dns-analytics-csv
          path: dns_logs_summary.csv
          retention-days: 7
