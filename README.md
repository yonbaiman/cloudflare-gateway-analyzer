# Cloudflare Gateway Log Analyzer 🛡️

A lightweight, automated analytics script for Cloudflare Zero Trust (Free Tier) users. 
Generates professional-grade security reports with interactive charts and device-level insights.

## 🌟 Features
- **Daily Traffic Trends**: Visualizes allowed vs. blocked queries over 24 hours using Mermaid.js.
- **Location (Device) Insights**: Identifies which devices are triggering blocks and tracks their top blocked domains.
- **Zero Dependencies**: Pure Python script. No `pandas`, no `requests`. Extremely fast and eco-friendly.

## 🔒 Security First: The "Two-Repo" Architecture
To protect your privacy (DNS logs reveal your browsing habits), this tool is designed to be run in a **completely separated private environment**. 

**DO NOT** run this script directly in a public repository. 

### Recommended Setup
1. **Create a Private Repository** (e.g., `private-dns-monitor`).
2. Add your Cloudflare API credentials as Secrets in that private repo:
   - `CLOUDFLARE_API_TOKEN`
   - `CLOUDFLARE_ACCOUNT_ID`
3. Create a workflow file (`.github/workflows/monitor.yml`) in your private repo that calls this public script:

```yaml
# Example Workflow for your Private Repo
name: Private DNS Monitor
on:
  schedule:
    - cron: '0 23 * * *'
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
