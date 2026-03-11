# Cloudflare Gateway Log Insights 🛡️

A lightweight, automated analytics tool for Cloudflare Zero Trust (Free Tier) users. 
Get professional-grade security reports delivered to your GitHub Actions summary every day.

## 🚀 Why this?
Cloudflare's Free Tier limits detailed log access. This tool hacks the GraphQL API to provide:
- **Daily Traffic Overview**: Total vs. Blocked queries.
- **Top Blocked Domains**: Instantly identify aggressive trackers (like those in certain smartphones).
- **100% Free & Private**: Runs on GitHub Actions. No external servers, no data leaks.

## 🤝 Perfect Companion
Designed to be used alongside [mrrfv/cloudflare-gateway-pihole-scripts](https://github.com/mrrfv/cloudflare-gateway-pihole-scripts). Use his scripts to **block**, and use this tool to **see** what you blocked.

## 🛠️ Setup (3 Minutes)
1. **Use this template**: Click the green "Use this template" button to create your private/public copy.
2. **Set Secrets**: Go to `Settings > Secrets and variables > Actions` and add:
   - `CLOUDFLARE_API_TOKEN`: Your API Token (requires Gateway read permission).
   - `CLOUDFLARE_ACCOUNT_ID`: Your Cloudflare Account ID.
3. **Enjoy**: The script runs automatically every day at 08:00 JST. You can also trigger it manually from the `Actions` tab.

## 🔒 Privacy
This tool does **not** store your logs in the repository. It processes data in memory and outputs a summary to the GitHub Actions Step Summary only.
