# Cloudflare Gateway Log Analyzer 🛡️

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)](https://www.python.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Two--Repo-green?logo=githubactions)](#🔒-security-first-two-repo-architecture--セキュリティ設計)

**Break the "Free Tier" limit. Extract raw DNS logs and visualize your network security.**
**無料プランの壁を越える。生のDNSログを抽出し、ネットワークセキュリティを可視化します。**

---

## ✨ Why this is Special? / このツールの特別な点

Historically, raw log export (Logpush) was a **Paid-only** feature in Cloudflare Zero Trust. This tool bypasses that limitation using the GraphQL API to empower Free Tier users with raw CSV data.
従来、生のログエクスポート（Logpush）は有料プラン限定の機能でした。本ツールは GraphQL API を活用することで、**無料プランでも生のCSVデータを取得可能**にする「ハック」を実現しています。

- **📊 Visualized Insights**: Daily trends via Mermaid.js. (24時間の推移をグラフ化)
- **📥 Raw CSV Export**: Access data previously restricted to paid tiers. (有料級の生ログCSV抽出)
- **📍 Device Tracking**: Monitor blocks by Location (iPhone, PC, etc.). (デバイス別の詳細分析)

---

## 🔒 Security First: Two-Repo Architecture / セキュリティ設計

DNS logs contain sensitive browsing history. To protect your privacy, this tool uses a **separated execution model**.
DNSログには機微な情報が含まれるため、本ツールは以下の分離アーキテクチャを採用しています。

1. **Public Repo (This one)**: Core logic only. No personal data.
   (このリポジトリ。解析ロジックのみを管理し、個人データは含みません。)
2. **Private Repo (Yours)**: A private repository for execution. Stores your Secrets and generates reports.
   (あなたが作成する非公開リポジトリ。設定を保存し、解析結果を自分だけに表示します。)

---

## 🚀 Quick Start / セットアップ手順

### 1. Prepare Cloudflare / Cloudflareでの準備
Get these values from your dashboard: / ダッシュボードから以下の値を取得します。
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
    - cron: '0 23 * * *' # Runs daily at 08:00 JST (23:00 UTC)
  workflow_dispatch:    # Allows manual execution from the Actions tab

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      # 1. Checkout this public repository to get the script
      # (この公開リポジトリから解析スクリプトを取得)
      - name: Checkout Core Logic
        uses: actions/checkout@v6
        with:
          repository: 'yonbaiman/cloudflare-gateway-analyzer'
          
      # 2. Setup Python environment (Node.js 24 ready)
      # (Python環境のセットアップ - Node.js 24対応済み)
      - name: Setup Python
        uses: actions/setup-python@v6
        with:
          python-version: '3.12'

      # 3. Execute the analysis script using your secrets
      # (登録したSecretsを使用して解析を実行)
      - name: Run Harvester
        env:
          CF_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CF_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
        run: python scripts/harvester.py

      # 4. Upload raw CSV as a private artifact (stored for 7 days)
      # (生ログCSVを非公開アーティファクトとして保存 - 7日間保持)
      - name: Upload CSV Artifact
        uses: actions/upload-artifact@v7
        with:
          name: dns-analytics-csv
          path: dns_logs_summary.csv
          retention-days: 7
