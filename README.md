# Cloudflare Gateway Log Analyzer 🛡️

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://www.python.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Two--Repo-green?logo=githubactions)](#🔒-security-first-two-repo-architecture--セキュリティ設計)

**Break the "Free Tier" limit. Export detailed DNS logs and visualize your network security.**
**無料プランの壁を越える。詳細なDNSログを抽出し、ネットワークセキュリティを可視化します。**

---

## ✨ Why this is Special? / このツールの特別な点

Cloudflare Zero Trust's free tier has a significant limitation: you cannot export logs to external tools (Logpush). This project overcomes this by using the GraphQL API to extract **Structured Query Logs**—a feature normally reserved for paid plans.

- **📊 Visualized Insights**: Daily trends via Mermaid.js charts. (24時間の推移をグラフ化)
- **📥 Structured CSV Export**: Access granular data (Domain, Location, Decision) with query counts. (ドメイン、デバイス、判定結果を含む詳細な構造化ログを抽出)
- **📍 Device Tracking**: Monitor DNS traffic patterns by Location. (デバイス別の通信パターンを分析)

---

## 🔒 Security First: Two-Repo Architecture / セキュリティ設計

DNS logs contain your private browsing history. To ensure your privacy, we recommend a **separated execution model**:
DNSログには個人の閲覧履歴が含まれます。プライバシーを守るため、以下の分離アーキテクチャを採用しています。

1. **Public Repo (This one)**: Manages core analysis logic. Contains no personal data.
   (このリポジトリ。解析ロジックのみを管理し、個人データは含みません。)
2. **Private Repo (Yours)**: For execution and private log storage.
   (あなたが作成する非公開リポジトリ。設定を保存し、解析結果を自分だけに保持します。)

---

## 🚀 Quick Start / セットアップ手順

### 1. Prepare Cloudflare / Cloudflareでの準備
Get these values from your Cloudflare dashboard: / ダッシュボードから以下の値を取得します。
- **`CLOUDFLARE_API_TOKEN`**: Create a token with `Account > Cloudflare Zero Trust > Read` permissions.
- **`CLOUDFLARE_ACCOUNT_ID`**: Found in your dashboard sidebar.

### 2. Setup Private Repo / 実行用リポジトリの作成
1. Create a new **Private** GitHub repository. (新しく「非公開」リポジトリを作成)
2. Add the secrets above to `Settings > Secrets and variables > Actions`. (上記2つをSecretsに登録)

### 3. Create Workflow / ワークフローの作成
Create `.github/workflows/monitor.yml` in your **private** repo and paste the code below:
(非公開リポジトリに `.github/workflows/monitor.yml` を作成し、以下のコードを貼り付けます)

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
          repository: 'yonbaiman/cloudflare-gateway-analyzer'
          
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
